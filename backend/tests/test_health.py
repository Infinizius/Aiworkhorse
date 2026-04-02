"""
test_health.py – Tests für /readyz und /health Endpunkte (Meilenstein 7 verification).
"""
import pytest
from unittest.mock import AsyncMock, patch


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
