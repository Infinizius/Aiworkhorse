"""
test_health.py – Tests für /readyz und /health Endpunkte (Meilenstein 7 verification).
"""
from contextlib import asynccontextmanager
import pytest
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch

import main


pytestmark = pytest.mark.anyio


async def test_readyz_requires_no_auth(client):
    """GET /readyz muss ohne API-Key erreichbar sein (für Docker-Healthchecks)."""
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_health_requires_auth(client):
    """GET /health ohne API-Key muss 401 zurückgeben."""
    resp = await client.get("/health")
    assert resp.status_code == 401


async def test_health_ok_when_all_connected(auth_client, mock_redis):
    """GET /health mit gültigem Key und funktionierender DB + Redis."""
    resp = await auth_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["redis"] == "connected"


async def test_health_503_when_redis_down(auth_client):
    """GET /health gibt 503 zurück, wenn Redis nicht erreichbar ist."""
    with patch("main.redis_client") as mock_redis_down:
        mock_redis_down.ping = AsyncMock(side_effect=ConnectionError("Redis offline"))
        resp = await auth_client.get("/health")
    assert resp.status_code == 503
    body = resp.json()
    assert body["detail"]["status"] == "error"


async def test_lifespan_shutdown_closes_background_clients():
    """Der echte Lifespan schließt Redis, arq und DB beim Shutdown explizit."""
    app_instance = FastAPI()
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    mock_conn = AsyncMock()

    @asynccontextmanager
    async def _mock_begin():
        yield mock_conn

    mock_engine.begin.return_value = _mock_begin()
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))
    mock_proc.returncode = 0
    mock_arq_pool = AsyncMock()
    mock_redis = MagicMock()
    mock_redis.aclose = AsyncMock()

    with (
        patch("main.validate_config"),
        patch("security_utils.verify_encryption_setup"),
        patch("main.genai.Client", return_value=MagicMock()),
        patch("main.create_async_engine", return_value=mock_engine),
        patch("main.asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)),
        patch("arq.create_pool", AsyncMock(return_value=mock_arq_pool)),
        patch("main.redis_client", mock_redis),
        patch.object(main, "_thread_executor") as mock_executor,
    ):
        async with main.lifespan(app_instance):
            assert app_instance.state.arq_pool is mock_arq_pool

    mock_executor.shutdown.assert_called_once_with(wait=True)
    mock_arq_pool.aclose.assert_awaited_once()
    mock_redis.aclose.assert_awaited_once()
    mock_engine.dispose.assert_awaited_once()
