"""Retriever — queries vector store for similar historical events.

Top-K retrieval with cosine similarity, filtered by event_type or sector.
Returns raw results for evidence_builder to enrich with outcomes.
"""

import logging

from src.models.event import Event
from src.rag.embedder import embed_text, prepare_event_text
from src.rag.vector_store import query_similar

logger = logging.getLogger(__name__)


def _event_query_text(event: Event) -> str:
    """Build the text representation of an event used for query embedding.

    Args:
        event: The event to represent.

    Returns:
        Prepared text for embedding (may be empty if the event has no content).
    """
    # Try to get ticker from entities, fall back to metadata or None
    ticker = None
    if event.entities:
        ticker = event.entities[0].ticker
    elif hasattr(event, "metadata") and isinstance(event.metadata, dict):
        ticker = event.metadata.get("ticker")

    return prepare_event_text({
        "event_type": event.event_type,
        "ticker": ticker,
        "summary": event.summary,
        "raw_text": event.raw_text,
    })


async def retrieve_similar_events(
    event: Event,
    top_k: int = 10,
    min_similarity: float = 0.70,
    namespace: str | None = None,
    filter_dict: dict | None = None,
    query_embedding: list[float] | None = None,
) -> list[dict]:
    """Retrieve similar historical events from the vector store.

    Flow:
    1. Build text representation of the event
    2. Embed via the configured embedding backend (OpenAI or Gemini)
    3. Query Pinecone for top-K matches
    4. Filter to similarity >= min_similarity
    5. Exclude self-matches

    Args:
        event: The current event to find similar events for.
        top_k: Maximum number of results.
        min_similarity: Minimum cosine similarity threshold.
        namespace: Optional namespace filter (sec_edgar, gdelt, newsapi).
        filter_dict: Optional Pinecone metadata filter.
        query_embedding: Optional precomputed embedding for the event text.
            When provided, the embedding API call is skipped — used by
            retrieve_similar_events_multi to embed once across namespaces.

    Returns:
        List of {id, score, metadata} dicts, sorted by score descending.
    """
    if query_embedding is not None:
        embedding = query_embedding
    else:
        event_text = _event_query_text(event)
        if not event_text:
            logger.warning("Empty event text for event %s, skipping retrieval", event.event_id)
            return []
        embedding = await embed_text(event_text)

    # Query vector store
    # Fetch extra to allow for filtering
    results = await query_similar(
        embedding=embedding,
        top_k=top_k + 5,
        namespace=namespace,
        filter_dict=filter_dict,
    )

    # Filter: remove self-matches and below-threshold results
    filtered = []
    for r in results:
        if r["id"] == event.event_id:
            continue
        if r["score"] < min_similarity:
            continue
        filtered.append(r)
        if len(filtered) >= top_k:
            break

    logger.info(
        "Retrieved %d similar events for %s (top_k=%d, min_sim=%.2f)",
        len(filtered), event.event_id, top_k, min_similarity,
    )
    return filtered


async def retrieve_similar_events_multi(
    event: Event,
    namespaces: list[str],
    top_k: int = 5,
    min_similarity: float = 0.70,
) -> list[dict]:
    """Retrieve similar events across multiple namespaces with a single embedding.

    Embeds the event text once, queries every namespace, then merges the
    results — deduplicating by vector id and keeping the top-K by score.
    A namespace that fails (e.g. doesn't exist yet) is skipped, not fatal.

    Args:
        event: The current event to find similar events for.
        namespaces: Namespaces to search (e.g. ["sec_edgar", "gdelt", "newsapi"]).
        top_k: Maximum number of merged results to return.
        min_similarity: Minimum cosine similarity threshold.

    Returns:
        List of {id, score, metadata} dicts, deduplicated across namespaces
        and sorted by score descending, at most top_k items.
    """
    event_text = _event_query_text(event)
    if not event_text:
        logger.warning("Empty event text for event %s, skipping retrieval", event.event_id)
        return []

    # Embed ONCE — identical text must not be re-embedded per namespace
    embedding = await embed_text(event_text)

    merged: list[dict] = []
    seen_ids: set[str] = set()
    for ns in namespaces:
        try:
            ns_results = await retrieve_similar_events(
                event=event,
                top_k=top_k,
                min_similarity=min_similarity,
                namespace=ns,
                query_embedding=embedding,
            )
        except Exception:
            logger.debug("Namespace %s query failed, skipping", ns)
            continue
        for r in ns_results:
            rid = r.get("id", "")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                merged.append(r)

    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return merged[:top_k]


async def retrieve_by_ticker(
    ticker: str,
    event_type: str | None = None,
    top_k: int = 20,
    namespace: str | None = None,
) -> list[dict]:
    """Retrieve historical events for a specific ticker.

    Useful for building a company-specific event history.

    Args:
        ticker: Stock ticker symbol.
        event_type: Optional event type filter.
        top_k: Maximum results.
        namespace: Optional namespace filter.

    Returns:
        List of {id, score, metadata} dicts.
    """
    # Build a simple query embedding
    query_text = f"Ticker: {ticker}"
    if event_type:
        query_text += f"\nEvent type: {event_type}"

    embedding = await embed_text(query_text)

    filter_dict = {"ticker": ticker}
    if event_type:
        filter_dict["event_type"] = event_type

    return await query_similar(
        embedding=embedding,
        top_k=top_k,
        namespace=namespace,
        filter_dict=filter_dict,
    )
