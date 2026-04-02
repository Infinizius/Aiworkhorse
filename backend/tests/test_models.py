"""
test_models.py - Tests for the /v1/models endpoint.
"""
import pytest


pytestmark = pytest.mark.anyio

REQUIRED_MODELS = [
    "gemini-3-flash-preview",
    "gemma-3-27b-it",
    "deepseek-v3.2-non-reasoning",
    "deepseek-v3.2-reasoning",
    "mistral-large-latest",
    "mistral-small-latest",
    "codestral-latest",
]


async def test_models_endpoint_returns_200(client):
    """/v1/models is publicly accessible (no API key required)."""
    resp = await client.get("/v1/models")
    assert resp.status_code == 200


async def test_models_response_has_openai_format(client):
    """Response must conform to the OpenAI-compatible format."""
    resp = await client.get("/v1/models")
    body = resp.json()
    assert body["object"] == "list"
    assert "data" in body
    assert isinstance(body["data"], list)


async def test_models_contains_all_providers(client):
    """All configured models (Gemini, DeepSeek, Mistral) must be present."""
    resp = await client.get("/v1/models")
    model_ids = [m["id"] for m in resp.json()["data"]]
    for required_model in REQUIRED_MODELS:
        assert required_model in model_ids, f"Model '{required_model}' missing from /v1/models"


async def test_models_have_required_fields(client):
    """Every model object must contain id, object, created, and owned_by."""
    resp = await client.get("/v1/models")
    for model in resp.json()["data"]:
        assert "id" in model
        assert "object" in model
        assert "created" in model
        assert "owned_by" in model
        assert model["object"] == "model"
