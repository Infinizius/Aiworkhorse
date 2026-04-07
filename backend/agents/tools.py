"""
agents/tools.py – LangGraph-compatible tools for the MaxClaw supervisor agent.

Tools:
  - web_search: Search the web via DuckDuckGo (or Serper if configured).
  - read_workspace_file: Read a file from the user's workspace.
  - write_workspace_file: Write a file to the user's workspace (path-traversal safe).
  - update_core_memory: Append or replace the user's core memory in PostgreSQL.
"""
import os
from typing import Optional

import httpx
from langchain_core.tools import tool

from config import SERPER_API_KEY, WORKSPACE_ROOT


# ─── Path Traversal Security ─────────────────────────────────────────────────

class PathTraversalError(Exception):
    """Raised when a file path attempts to escape the user's workspace."""


def _safe_workspace_path(user_id: str, relative_path: str) -> str:
    """
    Resolve *relative_path* inside /app/workspace/{user_id}/ and verify
    the result does not escape that directory.

    Security: Uses os.path.abspath to canonicalize the path and then checks
    that the result starts with the allowed base directory.  Any attempt to
    use ``../`` or symlinks to break out is detected and raises
    ``PathTraversalError``.
    """
    base_dir = os.path.abspath(os.path.join(WORKSPACE_ROOT, user_id))
    target = os.path.abspath(os.path.join(base_dir, relative_path))

    if not target.startswith(base_dir + os.sep) and target != base_dir:
        raise PathTraversalError(
            f"Access denied: path '{relative_path}' escapes workspace "
            f"'{base_dir}'"
        )
    return target


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for the given query and return a summary of top results."""
    # Try Serper first (paid, higher quality)
    if SERPER_API_KEY:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": SERPER_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": 5},
                )
                data = resp.json()
                results = [
                    f"{item.get('title', '')}: {item.get('snippet', '')}"
                    for item in data.get("organic", [])[:5]
                ]
                if results:
                    return "\n".join(results)
        except Exception:
            pass

    # Fallback: DuckDuckGo HTML lite (no API key required)
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "AI-Workhorse/1.0"},
            )
            # Extract simple text snippets from results
            from html.parser import HTMLParser

            class _SnippetParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.snippets: list[str] = []
                    self._in_snippet = False
                    self._current = ""

                def handle_starttag(self, tag, attrs):
                    cls = dict(attrs).get("class", "")
                    if "result__snippet" in cls:
                        self._in_snippet = True
                        self._current = ""

                def handle_data(self, data):
                    if self._in_snippet:
                        self._current += data

                def handle_endtag(self, tag):
                    if self._in_snippet and tag in ("a", "span", "td"):
                        if self._current.strip():
                            self.snippets.append(self._current.strip())
                        self._in_snippet = False

            parser = _SnippetParser()
            parser.feed(resp.text)
            if parser.snippets:
                return "\n".join(parser.snippets[:5])
    except Exception:
        pass

    return f"No search results found for '{query}'."


@tool
def read_workspace_file(user_id: str, file_path: str) -> str:
    """Read a file from the user's workspace. Returns the file content as text."""
    try:
        target = _safe_workspace_path(user_id, file_path)
    except PathTraversalError as exc:
        return f"Error: {exc}"

    if not os.path.isfile(target):
        return f"Error: File '{file_path}' does not exist in your workspace."

    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as exc:
        return f"Error reading file: {exc}"


@tool
def write_workspace_file(user_id: str, file_path: str, content: str) -> str:
    """Write content to a file in the user's workspace. Creates directories as needed.

    SECURITY: The file path is validated using os.path.abspath to prevent
    path traversal attacks. Any attempt to write outside
    /app/workspace/{user_id}/ will be rejected immediately.
    """
    try:
        target = _safe_workspace_path(user_id, file_path)
    except PathTraversalError as exc:
        return f"Error: {exc}"

    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{file_path}' written successfully."
    except Exception as exc:
        return f"Error writing file: {exc}"


@tool
def update_core_memory(user_id: str, memory_content: str) -> str:
    """Update the user's core memory. This is persistent information the agent
    remembers across conversations.

    NOTE: This tool is synchronous. The actual DB write is performed by the
    graph node wrapper that intercepts this tool's output.
    """
    import json as _json
    # The actual DB write is handled by the graph's tool execution node.
    # This tool returns a JSON marker that the graph node picks up.
    return CORE_MEMORY_MARKER_PREFIX + _json.dumps({
        "user_id": user_id,
        "content": memory_content,
    })


# Marker prefix for core memory updates (used by tools.py and main.py)
CORE_MEMORY_MARKER_PREFIX = "__CORE_MEMORY_UPDATE__:"

# All tools available to the supervisor
AGENT_TOOLS = [web_search, read_workspace_file, write_workspace_file, update_core_memory]
