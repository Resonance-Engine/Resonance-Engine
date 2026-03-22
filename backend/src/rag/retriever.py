"""Retriever — queries vector store for similar historical events.

Top-K retrieval with cosine similarity, filtered by event_type or sector.
Returns raw results for evidence_builder to enrich with outcomes.
"""

from src.models.event import Event


async def retrieve_similar_events(
    event: Event,
    top_k: int = 10,
    min_similarity: float = 0.70,
) -> list[dict]:
    """Retrieve similar historical events from the vector store.

    Flow:
    1. Embed event summary via embedder
    2. Query vector store for top-K matches
    3. Filter to similarity > min_similarity
    4. Return raw match dicts for evidence_builder

    TODO: Phase 1 deliverable
    - Wire up embedder.embed_text()
    - Wire up vector_store.query_similar()
    - Apply min_similarity filter
    """
    raise NotImplementedError("Event retrieval — Phase 1 deliverable")
