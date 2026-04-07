"""Text embedding — converts event summaries to vector representations.

Supports two backends:
  1. Google Gemini text-embedding-004 (768 dimensions) — preferred
  2. OpenAI text-embedding-3-small (1536 dimensions) — fallback

Set GEMINI_API_KEY to use Gemini, or OPENAI_API_KEY for OpenAI.
Lazy-loaded client to avoid import-time API key validation.
"""

import logging
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)

# Gemini embedding config
GEMINI_MODEL = "models/gemini-embedding-001"
GEMINI_DIMENSIONS = 3072

# OpenAI embedding config (fallback)
OPENAI_MODEL = "text-embedding-3-small"
OPENAI_DIMENSIONS = 1536

MAX_BATCH_SIZE = 100
MAX_TEXT_LENGTH = 8000

_client: Any = None
_backend: str = ""


def _get_backend() -> str:
    """Determine which embedding backend to use."""
    if settings.gemini_api_key:
        return "gemini"
    if settings.openai_api_key:
        return "openai"
    return "none"


def get_dimensions() -> int:
    """Return the embedding dimensions for the active backend."""
    backend = _get_backend()
    if backend == "gemini":
        return GEMINI_DIMENSIONS
    return OPENAI_DIMENSIONS


def _get_client():
    """Lazy-initialize the embedding client."""
    global _client, _backend
    backend = _get_backend()

    if _client is None or _backend != backend:
        _backend = backend
        if backend == "gemini":
            from google import genai
            _client = genai.Client(api_key=settings.gemini_api_key)
        elif backend == "openai":
            from openai import AsyncOpenAI
            _client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            raise RuntimeError("No embedding API key configured (set GEMINI_API_KEY or OPENAI_API_KEY)")

    return _client


async def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string.

    Args:
        text: Text to embed (truncated to MAX_TEXT_LENGTH chars).

    Returns:
        Vector of floats (768 for Gemini, 1536 for OpenAI).
    """
    text = text[:MAX_TEXT_LENGTH].strip()
    if not text:
        return [0.0] * get_dimensions()

    client = _get_client()

    if _backend == "gemini":
        response = client.models.embed_content(
            model=GEMINI_MODEL,
            contents=text,
        )
        return response.embeddings[0].values
    else:
        response = await client.embeddings.create(
            input=[text],
            model=OPENAI_MODEL,
            dimensions=OPENAI_DIMENSIONS,
        )
        return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: List of texts to embed. Batched in groups of MAX_BATCH_SIZE.

    Returns:
        List of embedding vectors, one per input text.
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []
    client = _get_client()

    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = [t[:MAX_TEXT_LENGTH].strip() or " " for t in texts[i:i + MAX_BATCH_SIZE]]

        if _backend == "gemini":
            response = client.models.embed_content(
                model=GEMINI_MODEL,
                contents=batch,
            )
            all_embeddings.extend(e.values for e in response.embeddings)
        else:
            response = await client.embeddings.create(
                input=batch,
                model=OPENAI_MODEL,
                dimensions=OPENAI_DIMENSIONS,
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend(d.embedding for d in sorted_data)

    return all_embeddings


def prepare_event_text(event_data: dict) -> str:
    """Prepare event data for embedding by creating a rich text representation.

    Combines event metadata into a single string optimized for semantic search.

    Args:
        event_data: Dict with event fields (event_type, summary, raw_text, entities, etc.)

    Returns:
        Concatenated text suitable for embedding.
    """
    parts = []

    if event_data.get("event_type"):
        parts.append(f"Event type: {event_data['event_type']}")

    if event_data.get("ticker"):
        parts.append(f"Ticker: {event_data['ticker']}")

    if event_data.get("summary"):
        parts.append(f"Summary: {event_data['summary']}")

    if event_data.get("raw_text"):
        parts.append(f"Content: {event_data['raw_text'][:2000]}")

    return "\n".join(parts) if parts else ""
