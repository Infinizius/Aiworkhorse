"""
dashboard.py – Phase 4: Workspace Dashboard with JWT-based magic links.

Endpoints:
  - POST /v1/workspace/magic-link: Generate a JWT magic-link for the dashboard.
  - GET /dashboard: Verify JWT and serve the workspace dashboard HTML.
  - GET /v1/workspace/files: List files in the user's workspace (JSON API).
  - GET /v1/workspace/files/{file_path:path}: Read a file (JSON API).
  - DELETE /v1/workspace/files/{file_path:path}: Delete a file (JSON API).
"""
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config import DASHBOARD_JWT_SECRET, ENCRYPTION_KEY, WORKSPACE_ROOT

logger = logging.getLogger("ai_workhorse.dashboard")

router = APIRouter()

# ─── Lightweight JWT (HMAC-SHA256, no external dependency) ────────────────────

_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_SECONDS = 3600  # 1 hour


def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _get_jwt_secret() -> str:
    """Return the JWT signing secret, falling back to ENCRYPTION_KEY."""
    secret = DASHBOARD_JWT_SECRET or ENCRYPTION_KEY
    if not secret:
        raise RuntimeError("No JWT secret configured (set DASHBOARD_JWT_SECRET or ENCRYPTION_KEY)")
    return secret


def create_dashboard_jwt(user_id: str) -> str:
    """Create a signed JWT token for dashboard access."""
    secret = _get_jwt_secret()
    header = _b64url_encode(json.dumps({"alg": _JWT_ALGORITHM, "typ": "JWT"}).encode())
    now = int(time.time())
    payload = _b64url_encode(json.dumps({
        "sub": user_id,
        "iat": now,
        "exp": now + _JWT_EXPIRY_SECONDS,
    }).encode())
    signing_input = f"{header}.{payload}"
    signature = hmac.new(
        secret.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def verify_dashboard_jwt(token: str) -> str:
    """Verify a JWT token and return the user_id (sub claim).

    Raises HTTPException(401) on invalid or expired tokens.
    """
    secret = _get_jwt_secret()
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid token format")

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_sig = hmac.new(
        secret.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    actual_sig = _b64url_decode(parts[2])

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    try:
        payload = json.loads(_b64url_decode(parts[1]))
    except (json.JSONDecodeError, Exception):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user identity")

    return user_id


# ─── Path-safe workspace helper ──────────────────────────────────────────────

def _safe_workspace_path(user_id: str, relative_path: str) -> str:
    """Resolve and validate a path inside the user's workspace."""
    base_dir = os.path.abspath(os.path.join(WORKSPACE_ROOT, user_id))
    target = os.path.abspath(os.path.join(base_dir, relative_path))

    if not target.startswith(base_dir + os.sep) and target != base_dir:
        raise HTTPException(
            status_code=403, detail="Access denied: path escapes workspace"
        )
    return target


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/v1/workspace/magic-link")
async def generate_magic_link(request: Request):
    """
    Called when the user sends /workspace in chat.
    Expects JSON body: {"user_id": "..."} or reads from X-User-Email header.
    Returns a JWT-signed magic link to the dashboard.
    """
    user_id = request.headers.get("X-User-Email")
    if not user_id:
        try:
            body = await request.json()
            user_id = body.get("user_id")
        except Exception:
            pass
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    token = create_dashboard_jwt(user_id)
    # Build the dashboard URL
    base_url = str(request.base_url).rstrip("/")
    dashboard_url = f"{base_url}/dashboard?token={token}"

    return {"url": dashboard_url, "token": token, "expires_in": _JWT_EXPIRY_SECONDS}


@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(token: str = Query(..., description="JWT access token")):
    """Verify the JWT and serve the workspace dashboard as a single HTML page."""
    user_id = verify_dashboard_jwt(token)
    return HTMLResponse(content=_render_dashboard_html(user_id, token))


@router.get("/v1/workspace/files")
async def list_workspace_files(token: str = Query(...)):
    """List all files in the user's workspace."""
    user_id = verify_dashboard_jwt(token)
    base_dir = os.path.abspath(os.path.join(WORKSPACE_ROOT, user_id))

    if not os.path.isdir(base_dir):
        return {"files": [], "total": 0}

    files = []
    for root, _dirs, filenames in os.walk(base_dir):
        for fname in filenames:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, base_dir)
            stat = os.stat(full)
            files.append({
                "path": rel,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            })

    return {"files": files, "total": len(files)}


@router.get("/v1/workspace/files/{file_path:path}")
async def read_workspace_file_endpoint(file_path: str, token: str = Query(...)):
    """Read a specific file from the user's workspace."""
    user_id = verify_dashboard_jwt(token)
    target = _safe_workspace_path(user_id, file_path)

    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": file_path, "content": content}
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=415, detail="File is not a text file"
        )


@router.delete("/v1/workspace/files/{file_path:path}")
async def delete_workspace_file_endpoint(file_path: str, token: str = Query(...)):
    """Delete a file from the user's workspace."""
    user_id = verify_dashboard_jwt(token)
    target = _safe_workspace_path(user_id, file_path)

    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(target)
    return {"status": "deleted", "path": file_path}


# ─── Dashboard HTML ──────────────────────────────────────────────────────────

def _render_dashboard_html(user_id: str, token: str) -> str:
    """Render the workspace dashboard as a single HTML page with Tailwind CSS."""
    return f"""<!DOCTYPE html>
<html lang="de" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Workhorse Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #0f172a; }}
        .file-row:hover {{ background: rgba(59, 130, 246, 0.1); }}
        pre {{ white-space: pre-wrap; word-break: break-word; }}
    </style>
</head>
<body class="min-h-screen text-gray-200">
    <nav class="border-b border-gray-700 bg-gray-900/80 backdrop-blur px-6 py-4">
        <div class="max-w-5xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-3">
                <span class="text-2xl">&#128218;</span>
                <h1 class="text-xl font-bold text-gray-100">AI-Workhorse Workspace</h1>
            </div>
            <span class="text-sm text-gray-400">{_escape_html(user_id)}</span>
        </div>
    </nav>

    <main class="max-w-5xl mx-auto px-6 py-8">
        <div id="file-list" class="space-y-2">
            <p class="text-gray-500">Lade Dateien...</p>
        </div>

        <!-- File viewer modal -->
        <div id="viewer" class="hidden fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-6">
            <div class="bg-gray-800 rounded-2xl border border-gray-700 w-full max-w-3xl max-h-[80vh] flex flex-col">
                <div class="flex items-center justify-between px-6 py-4 border-b border-gray-700">
                    <h2 id="viewer-title" class="font-semibold text-gray-100 truncate"></h2>
                    <button onclick="closeViewer()" class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
                </div>
                <pre id="viewer-content" class="px-6 py-4 overflow-auto text-sm text-gray-300 flex-1"></pre>
            </div>
        </div>
    </main>

    <script>
        const TOKEN = "{token}";
        const API = "/v1/workspace/files?token=" + TOKEN;

        async function loadFiles() {{
            try {{
                const res = await fetch(API);
                const data = await res.json();
                const container = document.getElementById("file-list");

                if (data.total === 0) {{
                    container.innerHTML = '<div class="text-center py-12"><p class="text-gray-500 text-lg">Noch keine Dateien im Workspace.</p><p class="text-gray-600 text-sm mt-2">Der Agent erstellt hier Dateien f\\u00fcr dich.</p></div>';
                    return;
                }}

                container.innerHTML = data.files.map(f => `
                    <div class="file-row flex items-center justify-between rounded-xl border border-gray-700 bg-gray-800/40 px-5 py-3 transition-all">
                        <div class="flex items-center gap-3 min-w-0">
                            <span class="text-blue-400">&#128196;</span>
                            <div class="min-w-0">
                                <p class="font-medium text-gray-100 truncate">${{f.path}}</p>
                                <p class="text-xs text-gray-500">${{formatSize(f.size)}} &middot; ${{formatDate(f.modified)}}</p>
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="viewFile('${{f.path}}')" class="px-3 py-1 text-sm rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 transition">Ansehen</button>
                            <button onclick="deleteFile('${{f.path}}')" class="px-3 py-1 text-sm rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 transition">L\\u00f6schen</button>
                        </div>
                    </div>
                `).join("");
            }} catch (err) {{
                document.getElementById("file-list").innerHTML = '<p class="text-red-400">Fehler beim Laden der Dateien.</p>';
            }}
        }}

        async function viewFile(path) {{
            const res = await fetch("/v1/workspace/files/" + encodeURIComponent(path) + "?token=" + TOKEN);
            if (!res.ok) {{ alert("Datei konnte nicht geladen werden."); return; }}
            const data = await res.json();
            document.getElementById("viewer-title").textContent = data.path;
            document.getElementById("viewer-content").textContent = data.content;
            document.getElementById("viewer").classList.remove("hidden");
        }}

        function closeViewer() {{
            document.getElementById("viewer").classList.add("hidden");
        }}

        async function deleteFile(path) {{
            if (!confirm("Datei '" + path + "' wirklich l\\u00f6schen?")) return;
            const res = await fetch("/v1/workspace/files/" + encodeURIComponent(path) + "?token=" + TOKEN, {{ method: "DELETE" }});
            if (res.ok) loadFiles();
            else alert("L\\u00f6schen fehlgeschlagen.");
        }}

        function formatSize(bytes) {{
            if (bytes < 1024) return bytes + " B";
            if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
            return (bytes / 1048576).toFixed(1) + " MB";
        }}

        function formatDate(iso) {{
            return new Date(iso).toLocaleString("de-DE", {{
                day: "2-digit", month: "2-digit", year: "numeric",
                hour: "2-digit", minute: "2-digit"
            }});
        }}

        // Load files on page load
        loadFiles();
    </script>
</body>
</html>"""


def _escape_html(text: str) -> str:
    """Basic HTML entity escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
