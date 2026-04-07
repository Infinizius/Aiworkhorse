"""
test_agent.py – Tests for Phase 1 (Token Vault) and Phase 2 (Streaming Adapter).

Tests cover:
  - /v1/agent/register endpoint (Token Vault)
  - maxclaw-agent model in /v1/models
  - /v1/chat/completions with model=maxclaw-agent (non-streaming + streaming SSE)
  - SSE adapter: LangGraph events → OpenAI-compatible chunks
"""
import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.anyio

CHAT_URL = "/v1/chat/completions"


# ─── Phase 1: Token Vault ─────────────────────────────────────────────────────

async def test_register_agent_returns_registered(auth_client, mock_redis):
    """POST /v1/agent/register stores the encrypted key and returns success."""
    resp = await auth_client.post(
        "/v1/agent/register",
        json={"openwebui_api_key": "sk-test-webui-key-12345"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "registered"
    assert "user_id" in body


async def test_register_agent_rejects_empty_key(auth_client, mock_redis):
    """POST /v1/agent/register with empty key must return 400."""
    resp = await auth_client.post(
        "/v1/agent/register",
        json={"openwebui_api_key": ""},
    )
    assert resp.status_code == 400


async def test_register_agent_rejects_whitespace_key(auth_client, mock_redis):
    """POST /v1/agent/register with whitespace-only key must return 400."""
    resp = await auth_client.post(
        "/v1/agent/register",
        json={"openwebui_api_key": "   "},
    )
    assert resp.status_code == 400


async def test_register_agent_requires_auth(client):
    """POST /v1/agent/register without auth must return 401."""
    resp = await client.post(
        "/v1/agent/register",
        json={"openwebui_api_key": "sk-test"},
    )
    assert resp.status_code == 401


# ─── Phase 2: Models Endpoint includes maxclaw-agent ──────────────────────────

async def test_models_contains_maxclaw_agent(client):
    """The /v1/models endpoint must list maxclaw-agent."""
    resp = await client.get("/v1/models")
    assert resp.status_code == 200
    model_ids = [m["id"] for m in resp.json()["data"]]
    assert "maxclaw-agent" in model_ids


async def test_maxclaw_agent_model_has_correct_owner(client):
    """maxclaw-agent model must be owned by ai-workhorse."""
    resp = await client.get("/v1/models")
    models = resp.json()["data"]
    maxclaw = next((m for m in models if m["id"] == "maxclaw-agent"), None)
    assert maxclaw is not None
    assert maxclaw["owned_by"] == "ai-workhorse"


# ─── Phase 2: Non-Streaming maxclaw-agent ─────────────────────────────────────

async def test_maxclaw_agent_non_streaming(auth_client, mock_redis):
    """Non-streaming maxclaw-agent request returns OpenAI-format JSON with content."""
    with patch("agents.graph.build_supervisor_graph") as mock_graph:
        from agents.dummy_weather import build_dummy_graph
        mock_graph.return_value = build_dummy_graph()
        resp = await auth_client.post(
            CHAT_URL,
            json={
                "model": "maxclaw-agent",
                "messages": [{"role": "user", "content": "Weather in Berlin"}],
                "stream": False,
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["object"] == "chat.completion"
    assert body["model"] == "maxclaw-agent"
    assert len(body["choices"]) == 1
    assert body["choices"][0]["message"]["role"] == "assistant"
    content = body["choices"][0]["message"]["content"]
    assert content  # Must not be empty


# ─── Phase 2: Streaming maxclaw-agent ─────────────────────────────────────────

async def test_maxclaw_agent_streaming_returns_sse(auth_client, mock_redis):
    """Streaming maxclaw-agent request returns valid SSE with data: lines and [DONE]."""
    with patch("agents.graph.build_supervisor_graph") as mock_graph:
        from agents.dummy_weather import build_dummy_graph
        mock_graph.return_value = build_dummy_graph()
        resp = await auth_client.post(
            CHAT_URL,
            json={
                "model": "maxclaw-agent",
                "messages": [{"role": "user", "content": "Weather in Munich"}],
                "stream": True,
            },
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    raw = resp.text
    lines = [l for l in raw.strip().split("\n") if l.startswith("data: ")]
    assert len(lines) >= 2, f"Expected at least 2 SSE lines, got {len(lines)}"

    # Last data line must be [DONE]
    assert lines[-1].strip() == "data: [DONE]"

    # All non-DONE lines must be valid JSON
    chunks = []
    for line in lines:
        payload = line[len("data: "):].strip()
        if payload == "[DONE]":
            continue
        parsed = json.loads(payload)
        assert parsed["object"] == "chat.completion.chunk"
        assert parsed["model"] == "maxclaw-agent"
        assert "choices" in parsed
        chunks.append(parsed)

    # First chunk should have role: assistant
    first_delta = chunks[0]["choices"][0]["delta"]
    assert first_delta.get("role") == "assistant"


async def test_maxclaw_agent_streaming_contains_tool_calls(auth_client, mock_redis):
    """Streaming maxclaw-agent must emit tool_calls chunks for the get_weather tool."""
    with patch("agents.graph.build_supervisor_graph") as mock_graph:
        from agents.dummy_weather import build_dummy_graph
        mock_graph.return_value = build_dummy_graph()
        resp = await auth_client.post(
            CHAT_URL,
            json={
                "model": "maxclaw-agent",
                "messages": [{"role": "user", "content": "Weather in Tokyo"}],
                "stream": True,
            },
        )
    assert resp.status_code == 200
    raw = resp.text

    # Parse all SSE chunks
    found_tool_call = False
    found_content = False
    for line in raw.strip().split("\n"):
        if not line.startswith("data: "):
            continue
        payload = line[len("data: "):].strip()
        if payload == "[DONE]":
            continue
        parsed = json.loads(payload)
        delta = parsed["choices"][0]["delta"]
        if "tool_calls" in delta:
            found_tool_call = True
            tc = delta["tool_calls"][0]
            assert "function" in tc
            assert tc["function"]["name"] == "get_weather"
        if delta.get("content"):
            found_content = True

    assert found_tool_call, "Expected at least one tool_calls chunk in SSE stream"
    assert found_content, "Expected at least one content chunk in SSE stream"


# ─── Unit Tests: SSE Adapter ─────────────────────────────────────────────────

async def test_sse_adapter_produces_valid_openai_chunks():
    """The SSE adapter must produce well-formed OpenAI chunks from LangGraph events."""
    from langchain_core.messages import HumanMessage
    from agents.dummy_weather import build_dummy_graph
    from core.sse_adapter import langgraph_to_openai_sse

    graph = build_dummy_graph()
    messages = [HumanMessage(content="Weather in Paris")]

    chunks = []
    async for chunk in langgraph_to_openai_sse(graph, messages, "maxclaw-agent"):
        chunks.append(chunk)

    # Must end with [DONE]
    assert chunks[-1].strip() == "data: [DONE]"

    # All chunks must be properly formatted SSE lines
    for chunk in chunks:
        assert chunk.startswith("data: ")
        assert chunk.endswith("\n\n")

    # Parse non-DONE chunks
    parsed_chunks = []
    for chunk in chunks:
        payload = chunk.strip()[len("data: "):]
        if payload == "[DONE]":
            continue
        parsed = json.loads(payload)
        assert "id" in parsed
        assert parsed["object"] == "chat.completion.chunk"
        parsed_chunks.append(parsed)

    assert len(parsed_chunks) >= 3  # role chunk + tool call + content


async def test_sse_adapter_finish_reason_stop():
    """The second-to-last chunk before [DONE] must have finish_reason='stop'."""
    from langchain_core.messages import HumanMessage
    from agents.dummy_weather import build_dummy_graph
    from core.sse_adapter import langgraph_to_openai_sse

    graph = build_dummy_graph()
    messages = [HumanMessage(content="Weather in London")]

    chunks = []
    async for chunk in langgraph_to_openai_sse(graph, messages, "maxclaw-agent"):
        chunks.append(chunk)

    # Second-to-last should be the finish chunk
    finish_chunk = chunks[-2].strip()[len("data: "):]
    parsed = json.loads(finish_chunk)
    assert parsed["choices"][0]["finish_reason"] == "stop"


# ─── Unit Tests: Dummy Graph ─────────────────────────────────────────────────

async def test_dummy_graph_invokes_weather_tool():
    """The dummy graph must call get_weather and produce a result."""
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    from agents.dummy_weather import build_dummy_graph

    graph = build_dummy_graph()
    result = await graph.ainvoke({"messages": [HumanMessage(content="Weather in Berlin")]})
    messages = result["messages"]

    # Should have: HumanMessage, AIMessage(tool_calls), ToolMessage, AIMessage(content)
    assert len(messages) >= 3
    # Last message should be an AI message with content (the weather summary)
    last = messages[-1]
    assert isinstance(last, AIMessage)
    assert last.content  # Must not be empty
    assert "Berlin" in last.content or "weather" in last.content.lower()
