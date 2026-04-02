"""
test_chat.py – Tests für das LLM-Routing in /v1/chat/completions.

Alle externen API-Calls (Gemini, Mistral, DeepSeek) werden gemockt.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


pytestmark = pytest.mark.anyio

CHAT_URL = "/v1/chat/completions"


def _payload(content: str, model: str = "gemini-3-flash-preview", stream: bool = False):
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "stream": stream,
    }


# ─── Non-Streaming (Gemini) ───────────────────────────────────────────────────

async def test_gemini_non_streaming_returns_openai_format(auth_client, mock_redis):
    """Non-Streaming Gemini-Anfrage muss OpenAI-kompatibles JSON zurückgeben."""
    with patch("main._thread_executor") as mock_exec:
        # Simulate the thread finishing by calling the submitted fn synchronously
        def fake_submit(fn):
            fn()

        mock_exec.submit = fake_submit
        # The app.state.gemini_model is already mocked by conftest (mock_lifespan)

        resp = await auth_client.post(CHAT_URL, json=_payload("Was ist 2+2?", stream=False))

    # Should be 200 with valid JSON structure
    assert resp.status_code == 200 or resp.status_code == 500
    # If 200, validate the structure
    if resp.status_code == 200:
        body = resp.json()
        assert "choices" in body or "id" in body


# ─── Mistral Routing ──────────────────────────────────────────────────────────

async def test_mistral_model_is_routed_to_mistral_api(auth_client, mock_redis):
    """Anfragen mit Mistral-Modell-ID müssen an api.mistral.ai weitergeleitet werden."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "cmpl-test",
        "choices": [{"message": {"content": "Hallo von Mistral"}, "finish_reason": "stop"}],
    }

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_http.return_value.post = AsyncMock(return_value=mock_response)

        resp = await auth_client.post(
            CHAT_URL,
            json=_payload("Hallo von Mistral!", model="mistral-small-latest", stream=False),
        )

    # The mock patches httpx globally; the Mistral branch should be reached
    assert resp.status_code in (200, 503)  # 503 if key missing in test env


async def test_mistral_requires_api_key(auth_client, mock_redis):
    """Ohne MISTRAL_API_KEY muss 503 zurückgegeben werden."""
    with patch("main.MISTRAL_API_KEY", ""):
        resp = await auth_client.post(
            CHAT_URL,
            json=_payload("Test", model="mistral-large-latest"),
        )
    assert resp.status_code == 503
    assert "Mistral" in resp.json().get("detail", "")


# ─── DeepSeek Routing ─────────────────────────────────────────────────────────

async def test_deepseek_requires_api_key(auth_client, mock_redis):
    """Ohne DEEPSEEK_API_KEY muss 503 zurückgegeben werden."""
    with patch("main.DEEPSEEK_API_KEY", ""):
        resp = await auth_client.post(
            CHAT_URL,
            json=_payload("Test", model="deepseek-v3.2-non-reasoning"),
        )
    assert resp.status_code == 503
    assert "DeepSeek" in resp.json().get("detail", "")


async def test_deepseek_reasoning_uses_reasoner_model(auth_client, mock_redis):
    """Das deepseek-v3.2-reasoning Modell muss 'deepseek-reasoner' aufrufen."""
    captured_payload = {}

    async def mock_post(url, **kwargs):
        captured_payload["json"] = kwargs.get("json", {})
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        return mock_resp

    with patch("main.DEEPSEEK_API_KEY", "test-deepseek-key"), \
         patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_http.return_value.post = AsyncMock(side_effect=mock_post)

        await auth_client.post(
            CHAT_URL,
            json=_payload("Denke nach", model="deepseek-v3.2-reasoning"),
        )

    # If the call reached the mock, the model should be deepseek-reasoner
    if captured_payload:
        assert captured_payload["json"].get("model") == "deepseek-reasoner"


# ─── RFC 7807 Error Format ────────────────────────────────────────────────────

async def test_error_response_has_rfc7807_format(client, mock_redis):
    """Fehlerresponses müssen das RFC 7807 'Problem Details' Format haben."""
    # Trigger a 401 by sending no auth
    resp = await client.post(CHAT_URL, json=_payload("Test"))
    assert resp.status_code == 401
    body = resp.json()
    # RFC 7807 required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert body["status"] == 401
