"""Text embedding — converts event summaries to vector representations.

Uses OpenAI text-embedding-3-small (1536 dimensions, $0.02/1M tokens).
Lazy-loaded client to avoid import-time API key validation.
"""

import logging
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
MAX_BATCH_SIZE = 100
MAX_TEXT_LENGTH = 8000  # ~2000 tokens, well within 8191 token limit

_client: Any = None


def _get_client():
    """Lazy-initialize the OpenAI client."""
    global _client
    if _client is None:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string.

    Args:
        text: Text to embed (truncated to MAX_TEXT_LENGTH chars).

    Returns:
        Vector of DIMENSIONS floats.
    """
    text = text[:MAX_TEXT_LENGTH].strip()
    if not text:
        return [0.0] * DIMENSIONS

    client = _get_client()
    response = await client.embeddings.create(
        input=[text],
        model=MODEL,
        dimensions=DIMENSIONS,
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
        response = await client.embeddings.create(
            input=batch,
            model=MODEL,
            dimensions=DIMENSIONS,
        )
        # Sort by index to preserve order
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
        # Use first 2000 chars of raw text
        parts.append(f"Content: {event_data['raw_text'][:2000]}")

    return "\n".join(parts) if parts else ""
