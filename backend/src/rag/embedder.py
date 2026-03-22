"""Text embedding — converts event summaries to vector representations.

Phase 1: OpenAI text-embedding-3-small
Phase 3: Fine-tuned financial embedding model
"""


async def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a text string.

    TODO: Phase 1 deliverable
    - Call OpenAI embedding API (text-embedding-3-small)
    - Return vector (1536 dimensions)
    - Handle rate limits and retries
    """
    raise NotImplementedError("Text embedder — Phase 1 deliverable")


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    TODO: Phase 1 deliverable
    - Batch API call for efficiency
    - Return list of vectors
    """
    raise NotImplementedError("Batch embedder — Phase 1 deliverable")
