"""
test_goals.py – Tests für die Phase-2 Goal-Engine Endpoints und Guards.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import app
from models import GoalTask


pytestmark = pytest.mark.anyio

AUTH_HEADERS = {"Authorization": "Bearer workhorse-test"}


def _mock_db_factory(mock_session):
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)
    return factory


async def test_create_goal_returns_pending_goal(auth_client, mock_redis):
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock(return_value=None)

    with patch.object(app.state, "db_session_factory", _mock_db_factory(mock_session)):
        resp = await auth_client.post(
            "/v1/goals",
            json={"goal": "Prüfe jeden Morgen neue RAG-Paper", "schedule_minutes": 1440},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["goal"] == "Prüfe jeden Morgen neue RAG-Paper"
    assert body["status"] == "pending"
    assert body["schedule_minutes"] == 1440
    assert body["id"]


async def test_list_goals_returns_serialized_goals(auth_client, mock_redis):
    now = datetime.now(timezone.utc)
    mock_goal = GoalTask(
        id="goal-1",
        user_id="system_default",
        goal="Prüfe arXiv",
        model="gemini-3-flash-preview",
        status="pending",
        schedule_minutes=60,
        next_run_at=now,
        last_run_at=None,
        last_result=None,
        last_error=None,
        run_count=2,
        created_at=now,
        updated_at=now,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_goal]

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch.object(app.state, "db_session_factory", _mock_db_factory(mock_session)):
        resp = await auth_client.get("/v1/goals")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["goals"][0]["id"] == "goal-1"
    assert body["goals"][0]["run_count"] == 2


async def test_internal_tool_endpoint_requires_goal_engine_header(client, mock_redis):
    resp = await client.post(
        "/internal/tools/execute",
        headers=AUTH_HEADERS,
        json={"tool_name": "web_search", "arguments": {"query": "phase 2"}},
    )
    assert resp.status_code == 403


async def test_internal_tool_endpoint_executes_search_for_goal_engine(client, mock_redis):
    with patch("main.tool_web_search", AsyncMock(return_value="Treffer")) as mock_search:
        resp = await client.post(
            "/internal/tools/execute",
            headers={**AUTH_HEADERS, "X-Source": "goal-engine"},
            json={"tool_name": "web_search", "arguments": {"query": "phase 2"}},
        )

    assert resp.status_code == 200
    assert resp.json()["result"] == "Treffer"
    mock_search.assert_awaited_once_with("phase 2")


async def test_goal_engine_requests_skip_hitl_tool_loop(client, mock_redis):
    with patch("main.tool_web_search", AsyncMock(return_value="Treffer")) as mock_search:
        resp = await client.post(
            "/v1/chat/completions",
            headers={**AUTH_HEADERS, "X-Source": "goal-engine"},
            json={
                "model": "gemini-3-flash-preview",
                "stream": True,
                "messages": [{"role": "user", "content": "search latest rag papers"}],
            },
        )

    assert resp.status_code == 200
    assert "Tool-Freigabe erforderlich" not in resp.text
    assert "[TOOL]" not in resp.text
    mock_search.assert_not_awaited()
