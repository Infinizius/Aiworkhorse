import asyncio
import os
import uuid
from typing import List

from arq import create_pool
from arq.connections import RedisSettings
from google import genai
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models import Base, FileEmbedding, UploadedFile as UploadedFileModel

from config import DATABASE_URL, GEMINI_API_KEY, validate_config

# Configuration validation at import for the worker process
try:
    validate_config()
except Exception as e:
    # BUG-09 fix: re-raise so arq refuses to start with an invalid configuration
    # rather than silently running in a broken state.
    print(f"Worker config validation failed: {e}")
    raise

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def startup(ctx):
    """Worker startup hook to validate DB connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Worker: DB connection verified.")
    except Exception as e:
        print(f"Worker: DB connection FAILED: {e}")
        raise

async def shutdown(ctx):
    """Worker shutdown hook."""
    await engine.dispose()
    print("Worker: DB engine disposed.")

def _split_into_chunks(text_content: str, chunk_size: int = 500, overlap: int = 50):
    words = text_content.split()
    chunks: List[str] = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

async def process_pdf_embedding(ctx, file_id: str, api_key: str = None):
    """
    Background Task: Extrahiert Text (bereits im DB-Record) und erzeugt Embeddings.
    """
    effective_api_key = api_key or GEMINI_API_KEY
    client = genai.Client(api_key=effective_api_key)
    
    async with AsyncSessionLocal() as session:
        # Fetch file record
        res = await session.execute(
            UploadedFileModel.__table__.select().where(UploadedFileModel.id == file_id)
        )
        file_record = res.fetchone()
        if not file_record:
            return f"Error: File {file_id} not found."

        text_content = file_record.extracted_text
        if not text_content:
            return f"Error: No text extracted for {file_id}."

        chunks = _split_into_chunks(text_content)
        for i, chunk in enumerate(chunks):
            response = await asyncio.to_thread(
                client.models.embed_content,
                model="text-embedding-004",
                contents=chunk,
                config={"task_type": "RETRIEVAL_DOCUMENT"},
            )
            embedding_vec = response.embeddings[0].values
            
            db_chunk = FileEmbedding(
                file_id=file_id,
                chunk_text=chunk,
                chunk_index=i,
                embedding=embedding_vec,
            )
            session.add(db_chunk)
        
        await session.commit()
    return f"Successfully processed {len(chunks)} chunks for {file_id}."

class WorkerSettings:
    functions = [process_pdf_embedding]
    redis_settings = RedisSettings(host="redis", port=6379)
    on_startup = startup
    on_shutdown = shutdown
