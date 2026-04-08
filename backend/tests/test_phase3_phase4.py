"""
test_phase3_phase4.py – Tests for Phase 3 (Agent Tools, Core Memory) and Phase 4 (Dashboard).

Tests cover:
  - Path traversal security in write_workspace_file tool
  - Safe path resolution for workspace files
  - Core memory injection into system prompt
  - Dashboard JWT creation and verification
  - /workspace command interception
  - Dashboard HTML endpoint
  - Workspace file API endpoints
"""
import os
import tempfile
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.anyio


# ─── Phase 3: Path Traversal Security ────────────────────────────────────────

class TestPathTraversalSecurity:
    """Critical: write_workspace_file MUST prevent path traversal attacks."""

    def test_safe_path_normal_file(self):
        """Normal relative path should resolve inside workspace."""
        from agents.tools import _safe_workspace_path
        result = _safe_workspace_path("user123", "notes.md")
        assert result.endswith("user123/notes.md")

    def test_safe_path_nested_file(self):
        """Nested relative path should resolve inside workspace."""
        from agents.tools import _safe_workspace_path
        result = _safe_workspace_path("user123", "docs/report.md")
        assert "user123/docs/report.md" in result

    def test_path_traversal_dotdot_blocked(self):
        """../../../etc/passwd MUST be blocked."""
        from agents.tools import _safe_workspace_path, PathTraversalError
        with pytest.raises(PathTraversalError):
            _safe_workspace_path("user123", "../../../etc/passwd")

    def test_path_traversal_dotdot_to_other_user_blocked(self):
        """../other_user/secret.txt MUST be blocked."""
        from agents.tools import _safe_workspace_path, PathTraversalError
        with pytest.raises(PathTraversalError):
            _safe_workspace_path("user123", "../other_user/secret.txt")

    def test_path_traversal_absolute_path_blocked(self):
        """Absolute path /etc/passwd MUST be blocked."""
        from agents.tools import _safe_workspace_path, PathTraversalError
        with pytest.raises(PathTraversalError):
            _safe_workspace_path("user123", "/etc/passwd")

    def test_path_traversal_dotdot_in_middle_blocked(self):
        """Path with ../ in the middle escaping workspace MUST be blocked."""
        from agents.tools import _safe_workspace_path, PathTraversalError
        with pytest.raises(PathTraversalError):
            _safe_workspace_path("user123", "docs/../../other/file.txt")

    def test_write_workspace_file_blocks_traversal(self):
        """The write_workspace_file tool must return an error for traversal paths."""
        from agents.tools import write_workspace_file
        result = write_workspace_file.invoke({
            "user_id": "user123",
            "file_path": "../../../etc/crontab",
            "content": "malicious",
        })
        assert "Access denied" in result or "Error" in result

    def test_read_workspace_file_blocks_traversal(self):
        """The read_workspace_file tool must return an error for traversal paths."""
        from agents.tools import read_workspace_file
        result = read_workspace_file.invoke({
            "user_id": "user123",
            "file_path": "../../../etc/passwd",
        })
        assert "Access denied" in result or "Error" in result

    def test_write_and_read_workspace_file(self):
        """Write and read a file in a temporary workspace."""
        from agents.tools import write_workspace_file, read_workspace_file

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("agents.tools.WORKSPACE_ROOT", tmpdir):
                write_result = write_workspace_file.invoke({
                    "user_id": "testuser",
                    "file_path": "hello.txt",
                    "content": "Hello World",
                })
                assert "successfully" in write_result

                read_result = read_workspace_file.invoke({
                    "user_id": "testuser",
                    "file_path": "hello.txt",
                })
                assert read_result == "Hello World"

    def test_read_nonexistent_file(self):
        """Reading a non-existent file should return an error."""
        from agents.tools import read_workspace_file

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("agents.tools.WORKSPACE_ROOT", tmpdir):
                result = read_workspace_file.invoke({
                    "user_id": "testuser",
                    "file_path": "nonexistent.txt",
                })
                assert "does not exist" in result


# ─── Phase 3: Core Memory Injection ──────────────────────────────────────────

class TestCoreMemoryInjection:
    """Core memory must be injected into the system prompt."""

    def test_system_message_without_memory(self):
        """System message without core memory should not include memory section."""
        from agents.graph import _build_system_message
        msg = _build_system_message("")
        assert "MaxClaw" in msg.content
        assert "GEDÄCHTNIS" not in msg.content

    def test_system_message_with_memory(self):
        """System message with core memory must include the memory section."""
        from agents.graph import _build_system_message
        msg = _build_system_message("User prefers German. User works in Berlin.")
        assert "MaxClaw" in msg.content
        assert "GEDÄCHTNIS" in msg.content
        assert "User prefers German" in msg.content
        assert "User works in Berlin" in msg.content

    def test_system_message_whitespace_only_memory(self):
        """Whitespace-only core memory should not include memory section."""
        from agents.graph import _build_system_message
        msg = _build_system_message("   \n  ")
        assert "GEDÄCHTNIS" not in msg.content


# ─── Phase 3: Core Memory Tool ───────────────────────────────────────────────

class TestCoreMemoryTool:
    """The update_core_memory tool must return a JSON marker string."""

    def test_update_core_memory_returns_marker(self):
        import json
        from agents.tools import update_core_memory, CORE_MEMORY_MARKER_PREFIX
        result = update_core_memory.invoke({
            "user_id": "user123",
            "memory_content": "User likes Python",
        })
        assert result.startswith(CORE_MEMORY_MARKER_PREFIX)
        payload = json.loads(result[len(CORE_MEMORY_MARKER_PREFIX):])
        assert payload["user_id"] == "user123"
        assert payload["content"] == "User likes Python"

    def test_update_core_memory_handles_pipes_in_content(self):
        """Content with pipe characters must be handled correctly (JSON serialization)."""
        import json
        from agents.tools import update_core_memory, CORE_MEMORY_MARKER_PREFIX
        result = update_core_memory.invoke({
            "user_id": "user123",
            "memory_content": "User likes A | B | C",
        })
        payload = json.loads(result[len(CORE_MEMORY_MARKER_PREFIX):])
        assert payload["content"] == "User likes A | B | C"


# ─── Phase 4: Dashboard JWT ──────────────────────────────────────────────────

class TestDashboardJWT:
    """JWT creation and verification for the workspace dashboard."""

    def test_create_and_verify_jwt(self):
        """A freshly created JWT must be verifiable and return the user_id."""
        from dashboard import create_dashboard_jwt, verify_dashboard_jwt
        token = create_dashboard_jwt("alice@example.com")
        user_id = verify_dashboard_jwt(token)
        assert user_id == "alice@example.com"

    def test_expired_jwt_rejected(self):
        """An expired JWT must be rejected."""
        from dashboard import verify_dashboard_jwt, _b64url_encode, _get_jwt_secret
        import hashlib
        import hmac
        import json

        secret = _get_jwt_secret()
        header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = _b64url_encode(json.dumps({
            "sub": "alice@example.com",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }).encode())
        signing_input = f"{header}.{payload}"
        signature = hmac.new(
            secret.encode(), signing_input.encode(), hashlib.sha256
        ).digest()
        token = f"{signing_input}.{_b64url_encode(signature)}"

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_dashboard_jwt(token)
        assert exc_info.value.status_code == 401

    def test_tampered_jwt_rejected(self):
        """A JWT with tampered payload must be rejected."""
        from dashboard import create_dashboard_jwt, verify_dashboard_jwt
        from fastapi import HTTPException

        token = create_dashboard_jwt("alice@example.com")
        parts = token.split(".")
        # Tamper with the payload
        tampered = parts[0] + "." + parts[1] + "X" + "." + parts[2]
        with pytest.raises(HTTPException) as exc_info:
            verify_dashboard_jwt(tampered)
        assert exc_info.value.status_code == 401

    def test_invalid_format_rejected(self):
        """A malformed token must be rejected."""
        from dashboard import verify_dashboard_jwt
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            verify_dashboard_jwt("not-a-valid-token")
        assert exc_info.value.status_code == 401


# ─── Phase 4: /workspace Command ─────────────────────────────────────────────

class TestWorkspaceCommand:
    """The /workspace command must return a magic-link."""

    async def test_workspace_command_returns_magic_link(self, auth_client, mock_redis):
        """POST /v1/chat/completions with /workspace must return a dashboard link."""
        resp = await auth_client.post(
            "/v1/chat/completions",
            json={
                "model": "maxclaw-agent",
                "messages": [{"role": "user", "content": "/workspace"}],
                "stream": False,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        content = body["choices"][0]["message"]["content"]
        assert "Workspace" in content
        assert "/dashboard?token=" in content

    async def test_workspace_command_case_insensitive(self, auth_client, mock_redis):
        """The /workspace command should be case-insensitive."""
        resp = await auth_client.post(
            "/v1/chat/completions",
            json={
                "model": "maxclaw-agent",
                "messages": [{"role": "user", "content": "/WORKSPACE"}],
                "stream": False,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        content = body["choices"][0]["message"]["content"]
        assert "/dashboard?token=" in content


# ─── Phase 4: Dashboard Endpoints ────────────────────────────────────────────

class TestDashboardEndpoints:
    """Test the dashboard HTML and API endpoints."""

    async def test_dashboard_html_served_with_valid_token(self, client):
        """GET /dashboard with valid JWT must return HTML."""
        from dashboard import create_dashboard_jwt
        token = create_dashboard_jwt("alice@example.com")
        resp = await client.get(f"/dashboard?token={token}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "AI-Workhorse Workspace" in resp.text
        assert "alice@example.com" in resp.text

    async def test_dashboard_html_rejected_without_token(self, client):
        """GET /dashboard without token must fail."""
        resp = await client.get("/dashboard")
        assert resp.status_code == 422  # Missing required query param

    async def test_dashboard_html_rejected_with_bad_token(self, client):
        """GET /dashboard with invalid token must return 401."""
        resp = await client.get("/dashboard?token=bad-token")
        assert resp.status_code == 401

    async def test_workspace_files_empty_listing(self, client):
        """GET /v1/workspace/files with valid token returns empty when no workspace dir."""
        from dashboard import create_dashboard_jwt
        token = create_dashboard_jwt("alice@example.com")
        resp = await client.get(f"/v1/workspace/files?token={token}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["files"] == []

    async def test_workspace_files_listing_with_files(self, client):
        """GET /v1/workspace/files lists real files from workspace dir."""
        from dashboard import create_dashboard_jwt
        token = create_dashboard_jwt("testuser_files")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dashboard.WORKSPACE_ROOT", tmpdir):
                user_dir = os.path.join(tmpdir, "testuser_files")
                os.makedirs(user_dir)
                with open(os.path.join(user_dir, "test.md"), "w") as f:
                    f.write("# Hello")

                resp = await client.get(f"/v1/workspace/files?token={token}")
                assert resp.status_code == 200
                body = resp.json()
                assert body["total"] == 1
                assert body["files"][0]["path"] == "test.md"

    async def test_workspace_file_read(self, client):
        """GET /v1/workspace/files/{path} reads file content."""
        from dashboard import create_dashboard_jwt
        token = create_dashboard_jwt("testuser_read")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dashboard.WORKSPACE_ROOT", tmpdir):
                user_dir = os.path.join(tmpdir, "testuser_read")
                os.makedirs(user_dir)
                with open(os.path.join(user_dir, "data.txt"), "w") as f:
                    f.write("Important data here")

                resp = await client.get(f"/v1/workspace/files/data.txt?token={token}")
                assert resp.status_code == 200
                body = resp.json()
                assert body["content"] == "Important data here"

    async def test_workspace_file_delete(self, client):
        """DELETE /v1/workspace/files/{path} deletes the file."""
        from dashboard import create_dashboard_jwt
        token = create_dashboard_jwt("testuser_delete")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dashboard.WORKSPACE_ROOT", tmpdir):
                user_dir = os.path.join(tmpdir, "testuser_delete")
                os.makedirs(user_dir)
                fpath = os.path.join(user_dir, "delete_me.txt")
                with open(fpath, "w") as f:
                    f.write("delete me")

                resp = await client.delete(f"/v1/workspace/files/delete_me.txt?token={token}")
                assert resp.status_code == 200
                assert not os.path.exists(fpath)

    async def test_workspace_file_read_404_for_missing(self, client):
        """GET /v1/workspace/files/{path} returns 404 for non-existent file."""
        from dashboard import create_dashboard_jwt
        token = create_dashboard_jwt("testuser_404")
        resp = await client.get(f"/v1/workspace/files/nonexistent.txt?token={token}")
        assert resp.status_code == 404


# ─── Phase 4: Magic Link Endpoint ────────────────────────────────────────────

class TestMagicLinkEndpoint:
    """Test the /v1/workspace/magic-link endpoint."""

    async def test_magic_link_with_header(self, client):
        """POST /v1/workspace/magic-link with X-User-Email returns a link."""
        resp = await client.post(
            "/v1/workspace/magic-link",
            headers={"X-User-Email": "bob@example.com"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "url" in body
        assert "token" in body
        assert "expires_in" in body
        assert "/dashboard?token=" in body["url"]

    async def test_magic_link_with_json_body(self, client):
        """POST /v1/workspace/magic-link with JSON body returns a link."""
        resp = await client.post(
            "/v1/workspace/magic-link",
            json={"user_id": "charlie@example.com"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "/dashboard?token=" in body["url"]

    async def test_magic_link_rejects_missing_user(self, client):
        """POST /v1/workspace/magic-link without user_id must return 400."""
        resp = await client.post("/v1/workspace/magic-link")
        assert resp.status_code == 400


# ─── Phase 3: Supervisor Graph Structure ─────────────────────────────────────

class TestSupervisorGraph:
    """Test the supervisor graph compiles correctly."""

    def test_graph_compiles(self):
        """The supervisor graph must compile without errors."""
        from agents.graph import build_supervisor_graph
        graph = build_supervisor_graph()
        assert graph is not None

    def test_graph_has_correct_nodes(self):
        """The supervisor graph must have supervisor and tools nodes."""
        from agents.graph import build_supervisor_graph
        graph = build_supervisor_graph()
        # The compiled graph should have the expected nodes
        node_names = list(graph.nodes.keys())
        assert "supervisor" in node_names
        assert "tools" in node_names


# ─── Phase 3: Web Interaction Tools ──────────────────────────────────────────

class TestVisitWebpage:
    """Tests for the visit_webpage tool."""

    def test_visit_webpage_returns_content(self):
        """visit_webpage must return page text for a successful HTTP response."""
        from agents.tools import visit_webpage
        from unittest.mock import MagicMock, patch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = "<html><body><p>Hello World</p></body></html>"

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = visit_webpage.invoke({"url": "http://localhost:3000"})

        assert "HTTP 200" in result
        assert "Hello World" in result

    def test_visit_webpage_json_response(self):
        """visit_webpage returns raw body for non-HTML responses."""
        from agents.tools import visit_webpage
        from unittest.mock import MagicMock, patch
        import json

        payload = json.dumps({"status": "ok", "version": "1.0"})
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.text = payload

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = visit_webpage.invoke({"url": "http://localhost:8000/health"})

        assert "HTTP 200" in result
        assert '"status": "ok"' in result

    def test_visit_webpage_handles_network_error(self):
        """visit_webpage returns an error string when the request fails."""
        from agents.tools import visit_webpage
        from unittest.mock import patch
        import httpx

        with patch("agents.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.side_effect = httpx.ConnectError("refused")
            result = visit_webpage.invoke({"url": "http://localhost:9999"})

        assert "Error" in result

    def test_visit_webpage_truncates_long_content(self):
        """visit_webpage must truncate responses longer than 5000 chars."""
        from agents.tools import visit_webpage
        from unittest.mock import MagicMock, patch

        long_text = "A" * 6000
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.text = long_text

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = visit_webpage.invoke({"url": "http://localhost:3000/big"})

        assert "truncated" in result
        # Result must not exceed status line + 5000 chars + truncation marker
        assert len(result) < 6100


class TestHttpRequest:
    """Tests for the http_request tool."""

    def test_http_request_get(self):
        """http_request GET must return status code and body."""
        from agents.tools import http_request
        from unittest.mock import MagicMock, patch
        import json

        payload = json.dumps({"healthy": True})
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.text = payload

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = http_request.invoke({
                "url": "http://localhost:8000/health",
                "method": "GET",
            })

        assert "HTTP 200" in result
        assert "GET" in result
        assert '"healthy": true' in result

    def test_http_request_post_with_body(self):
        """http_request POST with JSON body must include body in the request."""
        from agents.tools import http_request
        from unittest.mock import MagicMock, patch, call

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.text = '{"id": 42}'

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = http_request.invoke({
                "url": "http://localhost:3000/api/items",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": '{"name": "test"}',
            })

        assert "HTTP 201" in result
        assert "POST" in result
        mock_client.request.assert_called_once()
        _, kwargs = mock_client.request.call_args
        assert kwargs.get("content") == '{"name": "test"}'

    def test_http_request_normalises_method_to_uppercase(self):
        """http_request must accept lowercase method names and normalise them."""
        from agents.tools import http_request
        from unittest.mock import MagicMock, patch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.text = "OK"

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = http_request.invoke({"url": "http://localhost/ping", "method": "get"})

        assert "GET" in result

    def test_http_request_handles_network_error(self):
        """http_request returns an error string when the request fails."""
        from agents.tools import http_request
        from unittest.mock import patch
        import httpx

        with patch("agents.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.side_effect = httpx.ConnectError("refused")
            result = http_request.invoke({"url": "http://localhost:9999/api"})

        assert "Error" in result

    def test_http_request_truncates_long_body(self):
        """http_request must truncate response bodies longer than 5000 chars."""
        from agents.tools import http_request
        from unittest.mock import MagicMock, patch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.text = "B" * 6000

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.request.return_value = mock_resp

        with patch("agents.tools.httpx.Client", return_value=mock_client):
            result = http_request.invoke({"url": "http://localhost/big", "method": "GET"})

        assert "truncated" in result


class TestAgentToolsRegistration:
    """Verify that the new tools are properly registered in AGENT_TOOLS."""

    def test_visit_webpage_in_agent_tools(self):
        """visit_webpage must be present in AGENT_TOOLS."""
        from agents.tools import AGENT_TOOLS
        names = [t.name for t in AGENT_TOOLS]
        assert "visit_webpage" in names

    def test_http_request_in_agent_tools(self):
        """http_request must be present in AGENT_TOOLS."""
        from agents.tools import AGENT_TOOLS
        names = [t.name for t in AGENT_TOOLS]
        assert "http_request" in names

    def test_all_original_tools_still_present(self):
        """Existing tools must not have been removed from AGENT_TOOLS."""
        from agents.tools import AGENT_TOOLS
        names = [t.name for t in AGENT_TOOLS]
        for expected in ("web_search", "read_workspace_file", "write_workspace_file", "update_core_memory"):
            assert expected in names, f"Tool '{expected}' is missing from AGENT_TOOLS"

