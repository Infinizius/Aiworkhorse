"""
conftest.py – Central pytest fixtures for AI-Workhorse backend tests.

Strategy:
  - Environment variables are set BEFORE main.py is imported to pass startup checks.
  - The real lifespan (DB, Alembic, Gemini init) is replaced by a lightweight
    mock_lifespan that sets app.state directly.
  - redis_client is patched per-test via the `mock_redis` fixture.
"""
import os
import sys
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ─── Set required env vars BEFORE importing app ──────────────────────────────
# Force-override to ensure the test key is always used, even inside the container
# where the real API_KEY env var may already be set.
os.environ["API_KEY"] = "workhorse-test"
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "test-gemini-key-not-real")
os.environ["DATABASE_URL"] = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test_db",
)

# Add backend root to sys.path so `from main import app` works when running
# pytest from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app  # noqa: E402

# ─── Constants ────────────────────────────────────────────────────────────────
TEST_API_KEY = "workhorse-test"
AUTH_HEADER = {"Authorization": f"Bearer {TEST_API_KEY}"}

# Pre-populate app.state so tests that don't trigger the lifespan still work.
_mock_model = MagicMock()
_mock_model.generate_content.return_value = iter([MagicMock(text="hello")])
app.state.gemini_model = _mock_model
app.state.approval_events = {}

# Mock DB session factory
_mock_session = AsyncMock()
_mock_session.execute = AsyncMock(return_value=MagicMock())
_mock_factory = MagicMock()
_mock_factory.return_value.__aenter__ = AsyncMock(return_value=_mock_session)
_mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)
app.state.db_session_factory = _mock_factory
app.state.db_engine = AsyncMock()


# ─── Mock Lifespan ────────────────────────────────────────────────────────────
@asynccontextmanager
async def _mock_lifespan(app_instance):
    """
    Lightweight lifespan for tests.
    Sets all required app.state attributes without real infrastructure.
    """
    mock_model = MagicMock()
    # generate_content (non-streaming): returns a response with .text
    mock_response = MagicMock()
    mock_response.text = "Mocked Gemini response."
    mock_model.generate_content.return_value = mock_response
    # generate_content(stream=True): returns an iterable of chunks
    mock_chunk = MagicMock()
    mock_chunk.text = "Hello"
    mock_model.generate_content.return_value = iter([mock_chunk])

    # Async DB session
    mock_session = AsyncMock()
    # Make SELECT 1 return a truthy result for the health check
    mock_scalar_result = MagicMock()
    mock_scalar_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_scalar_result)

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    app_instance.state.gemini_model = mock_model
    app_instance.state.db_engine = AsyncMock()
    app_instance.state.db_session_factory = mock_factory
    app_instance.state.approval_events = {}

    yield


# Override the real lifespan globally for the test session.
app.router.lifespan_context = _mock_lifespan


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    """
    Patches the module-level redis_client in main.py.
    Simulates a healthy Redis instance with an empty bucket (no rate limiting).
    """
    with patch("main.redis_client") as mock:
        mock.ping = AsyncMock(return_value=True)
        # Empty bucket → fresh user, full tokens
        mock.hgetall = AsyncMock(return_value={})
        mock.hset = AsyncMock(return_value=True)
        mock.expire = AsyncMock(return_value=True)
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        yield mock


@pytest_asyncio.fixture
async def client():
    """Unauthenticated HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client():
    """Authenticated HTTP test client with valid Bearer token."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=AUTH_HEADER,
    ) as ac:
        yield ac
