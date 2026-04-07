"""
Embedding utilities for AI-Workhorse.

Uses the NVIDIA NIM embeddings endpoint (OpenAI-compatible) with the
nvidia/llama-3.2-nv-embedqa-1b-v2 model (2048 dimensions, optimised for RAG).
"""
from typing import Literal

import httpx

NVIDIA_EMBED_URL = "https://integrate.api.nvidia.com/v1/embeddings"
NVIDIA_EMBED_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"

EmbedInputType = Literal["passage", "query"]


async def nvidia_embed(text: str, input_type: EmbedInputType, api_key: str) -> list:
    """
    Call the NVIDIA NIM embeddings endpoint and return the embedding vector.

    Args:
        text:       The text to embed.
        input_type: "passage" for documents stored in the vector DB,
                    "query"   for search/RAG queries.
        api_key:    NVIDIA API key (from https://build.nvidia.com).

    Returns:
        A list of 2048 floats representing the embedding.

    Raises:
        httpx.HTTPStatusError: If the NVIDIA API returns a non-2xx response.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                NVIDIA_EMBED_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": NVIDIA_EMBED_MODEL,
                    "input": text,
                    "input_type": input_type,
                    "encoding_format": "float",
                },
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
    except httpx.HTTPStatusError as exc:
        raise httpx.HTTPStatusError(
            f"NVIDIA embedding API error for input_type={input_type!r} "
            f"(text snippet: {text[:80]!r}): {exc.response.status_code} {exc.response.text}",
            request=exc.request,
            response=exc.response,
        ) from exc
