"""Vector store client — Pinecone wrapper for event embeddings.

Namespaces: sec_edgar, gdelt, newsapi (one per source for filtered retrieval).
Role: Supplementary similarity index — PostgreSQL remains source of truth.
"""

import logging
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)

_index: Any = None


def _get_index():
    """Lazy-initialize the Pinecone index."""
    global _index
    if _index is None:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        _index = pc.Index(settings.pinecone_index_name)
        logger.info("Connected to Pinecone index: %s", settings.pinecone_index_name)
    return _index


async def upsert_event(
    event_id: str,
    embedding: list[float],
    metadata: dict,
    namespace: str = "sec_edgar",
) -> None:
    """Upsert an event embedding into the vector store.

    Every event that passes the meaningful change gate gets embedded and stored.
    Builds proprietary historical knowledge base over time.

    Args:
        event_id: Unique event identifier (used as vector ID).
        embedding: Vector representation of the event.
        metadata: Searchable metadata (ticker, event_type, timestamp, source, summary).
        namespace: Source namespace for filtered retrieval.
    """
    index = _get_index()

    # Pinecone metadata values must be strings, numbers, booleans, or lists thereof
    clean_metadata = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            clean_metadata[k] = v
        elif isinstance(v, list):
            clean_metadata[k] = [str(item) for item in v]
        elif v is not None:
            clean_metadata[k] = str(v)

    index.upsert(
        vectors=[{"id": event_id, "values": embedding, "metadata": clean_metadata}],
        namespace=namespace,
    )
    logger.debug("Upserted event %s to namespace %s", event_id, namespace)


async def upsert_batch(
    items: list[dict],
    namespace: str = "sec_edgar",
    batch_size: int = 100,
) -> int:
    """Batch upsert events to the vector store.

    Args:
        items: List of dicts with keys: id, values (embedding), metadata.
        namespace: Source namespace.
        batch_size: Pinecone batch size limit.

    Returns:
        Number of vectors upserted.
    """
    index = _get_index()
    total = 0

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        vectors = []
        for item in batch:
            clean_meta = {}
            for k, v in item.get("metadata", {}).items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif isinstance(v, list):
                    clean_meta[k] = [str(x) for x in v]
                elif v is not None:
                    clean_meta[k] = str(v)
            vectors.append({
                "id": item["id"],
                "values": item["values"],
                "metadata": clean_meta,
            })
        index.upsert(vectors=vectors, namespace=namespace)
        total += len(vectors)

    logger.info("Batch upserted %d vectors to namespace %s", total, namespace)
    return total


async def query_similar(
    embedding: list[float],
    top_k: int = 10,
    namespace: str | None = None,
    filter_dict: dict | None = None,
) -> list[dict]:
    """Query the vector store for top-K similar events.

    Args:
        embedding: Query vector.
        top_k: Number of results to return.
        namespace: Source namespace filter. None queries all namespaces.
        filter_dict: Pinecone metadata filter (e.g., {"event_type": "earnings"}).

    Returns:
        List of {id, score, metadata} dicts sorted by similarity (descending).
    """
    index = _get_index()

    query_params = {
        "vector": embedding,
        "top_k": top_k,
        "include_metadata": True,
    }
    if namespace:
        query_params["namespace"] = namespace
    if filter_dict:
        query_params["filter"] = filter_dict

    results = index.query(**query_params)

    return [
        {
            "id": match.id,
            "score": match.score,
            "metadata": match.metadata or {},
        }
        for match in results.matches
    ]


async def delete_event(event_id: str, namespace: str = "sec_edgar") -> None:
    """Delete an event from the vector store.

    Args:
        event_id: Vector ID to delete.
        namespace: Source namespace.
    """
    index = _get_index()
    index.delete(ids=[event_id], namespace=namespace)
    logger.debug("Deleted event %s from namespace %s", event_id, namespace)


async def get_stats() -> dict:
    """Get vector store statistics (total vectors, namespaces, etc.)."""
    index = _get_index()
    stats = index.describe_index_stats()
    return {
        "total_vector_count": stats.total_vector_count,
        "namespaces": {
            ns: {"vector_count": ns_stats.vector_count}
            for ns, ns_stats in (stats.namespaces or {}).items()
        },
        "dimension": stats.dimension,
    }
