"""
Embedding utilities for AI-Workhorse.

Uses the NVIDIA NIM embeddings endpoint (OpenAI-compatible) with the
nvidia/nv-embedqa-e5-v5 model (1024 dimensions, optimised for RAG).
"""
import httpx

NVIDIA_EMBED_URL = "https://integrate.api.nvidia.com/v1/embeddings"
NVIDIA_EMBED_MODEL = "nvidia/nv-embedqa-e5-v5"


async def nvidia_embed(text: str, input_type: str, api_key: str) -> list:
    """
    Call the NVIDIA NIM embeddings endpoint and return the embedding vector.

    Args:
        text:       The text to embed.
        input_type: "passage" for documents stored in the vector DB,
                    "query"   for search/RAG queries.
        api_key:    NVIDIA API key (from https://build.nvidia.com).

    Returns:
        A list of 1024 floats representing the embedding.
    """
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
