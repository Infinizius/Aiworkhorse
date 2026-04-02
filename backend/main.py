import asyncio
import concurrent.futures
import hashlib
import json
import logging
import logging.handlers
import os
import re
import time
import unicodedata
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from google import genai
import httpx
import pdfplumber
import redis.asyncio as redis
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, Security, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models import Base, FileEmbedding, UserConfig, UploadedFile as UploadedFileModel
from security_utils import decrypt_key, encrypt_key

# ─── Configuration ────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
REACTIVE_MAX_ITERATIONS = int(os.getenv("REACTIVE_MAX_ITERATIONS", "3"))
GOAL_MAX_ITERATIONS = int(os.getenv("GOAL_MAX_ITERATIONS", "10"))
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
# API Key for Bearer-Token authentication (empty = auth disabled for local dev)
API_KEY = os.getenv("API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
WEBUI_API_KEY = os.getenv("WEBUI_API_KEY", "")
WEBUI_INTERNAL_URL = os.getenv("WEBUI_INTERNAL_URL", "http://ai-workhorse-webui:8080")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
# Dedicated encryption key for user-specific API keys (Phase 2).
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

POSTGRES_USER = os.getenv("POSTGRES_USER", "workhorse")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "workhorse_secure_pw")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "workhorse_db")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}",
)

# ─── Logging ──────────────────────────────────────────────────────────────────

LOG_DIR = os.path.abspath("logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "workhorse.jsonl")


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "req_info"):
            log_obj.update(record.req_info)
        return json.dumps(log_obj)


logger = logging.getLogger("ai_workhorse")
logger.setLevel(logging.INFO)

# TimedRotatingFileHandler: Rotation daily, keep 7 days
fh = logging.handlers.TimedRotatingFileHandler(
    LOG_FILE, when="D", interval=1, backupCount=7, encoding="utf-8"
)
fh.setFormatter(JSONFormatter())
logger.addHandler(fh)

# StreamHandler für Docker-Logs ("docker logs ai-workhorse-api")
sh = logging.StreamHandler()
sh.setFormatter(JSONFormatter())
logger.addHandler(sh)

# Thread pool for synchronous Gemini SDK calls
_thread_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup-Validation: Fail-Fast if critical settings are missing
    if not GEMINI_API_KEY:
        error_msg = "Critical environment variable missing: GEMINI_API_KEY"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    if not API_KEY:
        logger.warning(
            "API_KEY is not set – authentication is DISABLED. Set API_KEY in .env for production.",
            extra={"req_info": {"event": "startup_warning", "missing": "API_KEY"}},
        )

    # Initialize Gemini (google-genai Phase 2)
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    app_instance.state.gemini_client = gemini_client
    logger.info(
        "Gemini client initialized (google-genai)",
        extra={"req_info": {"event": "startup", "client": "google-genai"}},
    )

    # Database + pgvector setup
    try:
        engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
        import subprocess
        # Fail-Fast Migration
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Alembic migrations applied successfully")

        app_instance.state.db_engine = engine
        app_instance.state.db_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info(
            "Database initialized",
            extra={"req_info": {"event": "startup", "db": "connected"}},
        )
    except Exception as exc:
        logger.critical(f"Initialization failed: {exc}")
        raise

    from arq import create_pool
    from arq.connections import RedisSettings
    app_instance.state.arq_pool = await create_pool(RedisSettings(host="redis", port=6379))
    logger.info("Arq worker pool initialized.")
    
    yield

    # Shutdown
    _thread_executor.shutdown(wait=True)
    if getattr(app_instance.state, "db_engine", None):
        await app_instance.state.db_engine.dispose()


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="AI-Workhorse v8.1 API", lifespan=lifespan)

# Request-ID Middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# RFC 7807 Error Handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content={
            "type": "https://ai-workhorse.de/errors/http-error",
            "title": exc.detail if isinstance(exc.detail, str) else "An error occurred",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
            "request_id": getattr(request.state, "request_id", "unknown")
        },
        status_code=exc.status_code,
        media_type="application/problem+json"
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        content={
            "type": "https://ai-workhorse.de/errors/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc) if os.getenv("DEBUG") else "An unexpected error occurred.",
            "instance": request.url.path,
            "request_id": getattr(request.state, "request_id", "unknown")
        },
        status_code=500,
        media_type="application/problem+json"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = os.path.abspath("uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
# Redis Connection
redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    file_ids: Optional[List[str]] = []

class ToolApprovalRequest(BaseModel):
    approved: bool

class UserConfigRequest(BaseModel):
    provider: str
    api_key: str

# ─── Constants ────────────────────────────────────────────────────────────────

_MSG_MISSING_API_KEY = "GEMINI_API_KEY is not configured."
_MSG_API_ERROR = "An error occurred while processing your request."
_LOG_CONTENT_MAX_LEN = 200

# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_user_api_key(user_id: str, provider: str, app_instance: FastAPI) -> Optional[str]:
    db_session_factory = getattr(app_instance.state, "db_session_factory", None)
    if not db_session_factory or not user_id:
        return None
    try:
        async with db_session_factory() as session:
            res = await session.execute(
                select(UserConfig).where(UserConfig.user_id == user_id, UserConfig.provider == provider)
            )
            config = res.scalar_one_or_none()
            if config and config.encrypted_key:
                return decrypt_key(config.encrypted_key)
    except Exception as exc:
        logger.error(f"Failed to lookup user API key: {exc}")
    return None

def _convert_messages_for_gemini(messages: List[dict]):
    system_instruction: Optional[str] = None
    contents: List[dict] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
    return system_instruction, contents

def _split_into_chunks(text_content: str, chunk_size: int = 500, overlap: int = 50):
    words = text_content.split()
    chunks: List[str] = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

async def _get_rag_context(file_ids: List[str], query: str, app_instance: FastAPI, top_k: int = 5):
    if not getattr(app_instance.state, "db_session_factory", None): return ""
    try:
        client: genai.Client = app_instance.state.gemini_client
        response = await asyncio.to_thread(
            client.models.embed_content,
            model="text-embedding-004",
            contents=query,
            config={"task_type": "RETRIEVAL_QUERY"},
        )
        query_vec = response.embeddings[0].values
        async with app_instance.state.db_session_factory() as session:
            rows = await session.execute(
                select(FileEmbedding)
                .where(FileEmbedding.file_id.in_(file_ids))
                .order_by(FileEmbedding.embedding.cosine_distance(query_vec))
                .limit(top_k)
            )
            chunks = rows.scalars().all()
        if not chunks: return ""
        return "\n\n".join([f"[Quelle: Datei {c.file_id}]\n{c.chunk_text}" for c in chunks])
    except Exception as exc:
        logger.error(f"RAG failed: {exc}")
        return ""

async def tool_web_search(query: str):
    if SERPER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                    json={"q": query, "num": 5},
                )
                data = resp.json()
                results = [f"{item.get('title')}: {item.get('snippet')}" for item in data.get("organic", [])[:3]]
                if results: return "\n".join(results)
        except Exception: pass
    return f"Search results for '{query}' could not be retrieved."

# ─── Auth & Rate Limiting ─────────────────────────────────────────────────────

def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for: return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _get_user_id(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if API_KEY and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        return "key:" + hashlib.sha256(token.encode()).hexdigest()[:16]
    return _get_client_ip(request)

_bearer_scheme = HTTPBearer(auto_error=False)

async def verify_api_key(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme)):
    if not API_KEY: return
    if credentials is None or credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

async def get_current_user(request: Request) -> str:
    user_email = request.headers.get("X-User-Email")
    return user_email if user_email else "system_default"

async def check_rate_limit(request: Request):
    user_id = _get_user_id(request)
    key = f"bucket:{user_id}"
    try:
        now = time.time()
        res = await redis_client.hgetall(key)
        if not res:
            await redis_client.hset(key, mapping={"tokens": 9, "last_update": now})
            await redis_client.expire(key, 60)
            return
        tokens = float(res.get("tokens", 10))
        last_update = float(res.get("last_update", now))
        tokens = min(10, tokens + (now - last_update) * (10 / 60.0))
        if tokens >= 1:
            await redis_client.hset(key, mapping={"tokens": tokens - 1, "last_update": now})
        else:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except HTTPException: raise
    except Exception: pass

# ─── Prompt Injection Defense ─────────────────────────────────────────────────

_INJECTION_PATTERNS = [
    r"(?i)ignore\s+instructions", r"(?i)system\s*prompt", r"(?i)jailbreak", r"(?i)pretend\s+you\s+are"
]

def apply_prompt_injection_defense(messages: List[Message]) -> List[dict]:
    secure_messages = [{"role": "system", "content": "Du bist AI-Workhorse, ein sicherer KI-Assistent."}]
    for msg in messages:
        sanitized = unicodedata.normalize("NFKC", msg.content)
        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, sanitized):
                raise HTTPException(status_code=400, detail="Security Violation")
        secure_messages.append({"role": msg.role, "content": sanitized})
    return secure_messages

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/readyz", include_in_schema=False)
async def readiness_probe(): return {"status": "ok"}

@app.get("/health", dependencies=[Depends(verify_api_key)])
async def health_check(request: Request):
    try:
        async with request.app.state.db_session_factory() as session: await session.execute(text("SELECT 1"))
        await redis_client.ping()
        return {"status": "ok"}
    except Exception: raise HTTPException(status_code=503, detail="Unhealthy")

@app.post("/v1/user/config", dependencies=[Depends(verify_api_key)])
async def update_user_config(config: UserConfigRequest, user_id: str = Depends(get_current_user), req: Request = None):
    if config.provider not in ["gemini", "mistral", "deepseek"]: raise HTTPException(status_code=400)
    encrypted = encrypt_key(config.api_key)
    async with req.app.state.db_session_factory() as session:
        res = await session.execute(select(UserConfig).where(UserConfig.user_id == user_id, UserConfig.provider == config.provider))
        existing = res.scalar_one_or_none()
        if existing: existing.encrypted_key = encrypted
        else: session.add(UserConfig(user_id=user_id, provider=config.provider, encrypted_key=encrypted))
        await session.commit()
    return {"status": "success"}

@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": "gemini-2.0-flash", "owned_by": "google"}, {"id": "mistral-large-latest", "owned_by": "mistral"}]}

@app.post("/v1/tools/approve/{execution_id}", dependencies=[Depends(verify_api_key)])
async def approve_tool(execution_id: str, req: ToolApprovalRequest):
    """
    HITL Endpoint: Frontend bestätigt oder lehnt eine Tool-Ausfuhrung ab.
    Speichert das Resultat in Redis mit 5 Minuten TTL.
    """
    redis_key = f"approval:{execution_id}"
    await redis_client.set(redis_key, "approved" if req.approved else "denied", ex=300)
    return {"status": "success", "execution_id": execution_id, "approved": req.approved}

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def chat_completions_proxy(request: ChatCompletionRequest, req: Request, user_id: str = Depends(get_current_user)):
    secure_messages = apply_prompt_injection_defense(request.messages)
    model_name = request.model or "gemini-2.0-flash"
    
    # Provider routing
    provider = "gemini"
    default_key = GEMINI_API_KEY
    if "mistral" in model_name: provider, default_key = "mistral", MISTRAL_API_KEY
    elif "deepseek" in model_name: provider, default_key = "deepseek", DEEPSEEK_API_KEY
    
    api_key = await _get_user_api_key(user_id, provider, req.app) or default_key
    if not api_key: raise HTTPException(status_code=503, detail=f"{provider} key missing")

    if provider in ["mistral", "deepseek"]:
        base_url = "https://api.mistral.ai/v1" if provider == "mistral" else "https://api.deepseek.com/v1"
        async def _proxy():
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json={"model": model_name, "messages": secure_messages, "stream": request.stream}) as resp:
                    async for chunk in resp.aiter_bytes(): yield chunk
        if request.stream: return StreamingResponse(_proxy(), media_type="text/event-stream")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json={"model": model_name, "messages": secure_messages})
            return resp.json()

    # Gemini
    rag_context = ""
    if request.file_ids:
        last_msg = next((m["content"] for m in reversed(secure_messages) if m["role"] == "user"), "")
        rag_context = await _get_rag_context(request.file_ids, last_msg, req.app)

    client = genai.Client(api_key=api_key) if api_key != GEMINI_API_KEY else req.app.state.gemini_client
    chat_id, created_ts = f"chatcmpl-{uuid.uuid4().hex}", int(time.time())

    async def sse_gen():
        msgs = list(secure_messages)
        if rag_context: msgs[0]["content"] += f"\n\nContext:\n{rag_context}"
        
        def _chunk(c): 
            return f'data: {json.dumps({"id": chat_id, "object": "chat.completion.chunk", "created": created_ts, "model": model_name, "choices": [{"index": 0, "delta": {"content": c}}]})}\n\n'

        # Week 11: Persistent HITL Logic via Redis
        needs_tool = any("search" in msg["content"].lower() for msg in msgs if msg["role"] == "user")
        if needs_tool:
            execution_id = str(uuid.uuid4())
            redis_key = f"approval:{execution_id}"
            yield _chunk(f"\n[SYSTEM] Tool-Freigabe erforderlich (Web-Search). execution_id: {execution_id}\n")
            try:
                deadline = time.time() + 60
                approved = False
                while time.time() < deadline:
                    status = await redis_client.get(redis_key)
                    if status == "approved":
                        approved = True
                        break
                    elif status == "denied":
                        break
                    await asyncio.sleep(1)
                    yield ": keep-alive\n\n"
                
                if approved:
                    search_query = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "AI Workhorse")
                    tool_result = await tool_web_search(search_query)
                    yield _chunk(f"\n[TOOL] {tool_result}\n")
                    msgs.append({"role": "user", "content": f"[Web-Search Ergebnis]\n{tool_result}\n\nBitte fortfahren."})
                else:
                    yield _chunk("\n[SYSTEM] Tool-Ausfuhrung abgelehnt oder Timeout.\n")
            finally:
                await redis_client.delete(redis_key)

        def _convert_and_stream():
            try:
                sys_instr, contents = _convert_messages_for_gemini(msgs)
                stream = client.models.generate_content_stream(model="gemini-2.0-flash", contents=contents, config={"system_instruction": sys_instr})
                for chunk in stream:
                    if chunk.text: yield _chunk(chunk.text)
            except Exception as e: yield _chunk(f"Error: {e}")
            yield "data: [DONE]\n\n"

        for c in _convert_and_stream(): yield c

    if request.stream: return StreamingResponse(sse_gen(), media_type="text/event-stream")
    sys_instr, contents = _convert_messages_for_gemini(secure_messages)
    if rag_context: sys_instr = (sys_instr or "") + f"\n\nContext:\n{rag_context}"
    resp = await asyncio.to_thread(client.models.generate_content, model="gemini-2.0-flash", contents=contents, config={"system_instruction": sys_instr})
    return {"id": chat_id, "object": "chat.completion", "created": created_ts, "model": model_name, "choices": [{"index": 0, "message": {"role": "assistant", "content": resp.text}}]}

async def sync_file_to_webui(file_path: str, filename: str):
    if not WEBUI_API_KEY: return
    headers = {"Authorization": f"Bearer {WEBUI_API_KEY}"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            with open(file_path, "rb") as f:
                up_resp = await client.post(f"{WEBUI_INTERNAL_URL}/api/v1/files/", headers=headers, files={"file": (filename, f, "application/pdf")})
            if up_resp.status_code == 200:
                file_id = up_resp.json().get("id")
                await client.post(f"{WEBUI_INTERNAL_URL}/api/v1/knowledge/workhorse_archive/file/add", headers=headers, json={"file_id": file_id})
        except Exception: pass

@app.post("/v1/files/upload", dependencies=[Depends(verify_api_key)])
async def upload_pdf(req: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    """
    Saves PDF, extracts text synchronously, but enqueues embedding task as async job.
    """
    if not file.filename.lower().endswith(".pdf"): raise HTTPException(status_code=400)
    fid = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{fid}.pdf")
    with open(path, "wb") as b: b.write(await file.read())
    
    text_content = ""
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages: text_content += (p.extract_text() or "") + "\n"
    
    db_factory = req.app.state.db_session_factory
    async with db_factory() as session:
        db_file = UploadedFileModel(id=fid, filename=file.filename, path=path, extracted_text=text_content, page_count=len(pdf.pages))
        session.add(db_file)
        await session.commit()
    
    # Offload embedding to arq worker (Task 5)
    api_key = await _get_user_api_key(user_id, "gemini", req.app) or GEMINI_API_KEY
    await req.app.state.arq_pool.enqueue_job("process_pdf_embedding", fid, api_key)
    
    background_tasks.add_task(sync_file_to_webui, path, file.filename)
    return {"file_id": fid, "status": "processing", "message": "File uploaded and enqueued for embedding."}

@app.get("/v1/files", dependencies=[Depends(verify_api_key)])
async def list_files(req: Request):
    async with req.app.state.db_session_factory() as session:
        res = await session.execute(select(UploadedFileModel))
        files = res.scalars().all()
        return {"files": [{"file_id": f.id, "filename": f.filename} for f in files]}

@app.delete("/v1/files/{file_id}", dependencies=[Depends(verify_api_key)])
async def delete_file(file_id: str, req: Request):
    async with req.app.state.db_session_factory() as session:
        await session.execute(delete(FileEmbedding).where(FileEmbedding.file_id == file_id))
        await session.execute(delete(UploadedFileModel).where(UploadedFileModel.id == file_id))
        await session.commit()
    return {"status": "deleted"}

@app.get("/v1/files/{file_id}/download", dependencies=[Depends(verify_api_key)])
async def download_file(file_id: str, req: Request):
    async with req.app.state.db_session_factory() as session:
        res = await session.execute(select(UploadedFileModel).where(UploadedFileModel.id == file_id))
        f = res.scalar_one_or_none()
        if not f: raise HTTPException(status_code=404)
        return FileResponse(path=f.path, filename=f.filename)
