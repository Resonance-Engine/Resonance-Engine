"""Vector store client — Pinecone/Qdrant wrapper for event embeddings.

Namespaces: sec_edgar, gdelt, newsapi (one per source for filtered retrieval).
Role: Supplementary similarity index — PostgreSQL remains source of truth.
"""


async def upsert_event(event_id: str, embedding: list[float], metadata: dict, namespace: str) -> None:
    """Upsert an event embedding into the vector store.

    Every event that passes the meaningful change gate gets embedded and stored.
    Builds proprietary historical knowledge base over time.

    TODO: Phase 1 deliverable
    - Initialize Pinecone client
    - Upsert vector with event_id as ID
    - Include metadata: ticker, event_type, timestamp, source, summary
    """
    raise NotImplementedError("Vector store upsert — Phase 1 deliverable")


async def query_similar(
    embedding: list[float],
    top_k: int = 10,
    namespace: str | None = None,
    filter_dict: dict | None = None,
) -> list[dict]:
    """Query the vector store for top-K similar events.

    Returns list of {id, score, metadata} dicts sorted by similarity.

    TODO: Phase 1 deliverable
    - Query Pinecone with cosine similarity
    - Apply namespace + metadata filters
    - Return results with scores
    """
    raise NotImplementedError("Vector store query — Phase 1 deliverable")
