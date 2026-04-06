"""Evidence builder — converts retrieved vector matches into EvidenceItem objects.

Enriches raw retrieval results with actual market outcomes from PostgreSQL.
Creates the evidence[] array that makes every signal explainable.
"""

import logging
from datetime import datetime, timezone

from src.models.evidence import EvidenceItem

logger = logging.getLogger(__name__)


async def build_evidence(
    retrieval_results: list[dict],
    max_items: int = 5,
) -> list[EvidenceItem]:
    """Convert raw vector store matches into structured EvidenceItem objects.

    Flow:
    1. For each match, extract metadata (event summary, ticker, outcome)
    2. Look up actual market outcome from signal_repo if available
    3. Compute time_delta (human-readable)
    4. Build EvidenceItem with all fields populated
    5. Return top max_items sorted by similarity_score

    Args:
        retrieval_results: Raw results from vector store query
            (list of {id, score, metadata}).
        max_items: Maximum evidence items to return.

    Returns:
        List of EvidenceItem objects, sorted by similarity_score descending.
    """
    evidence_items: list[EvidenceItem] = []

    for result in retrieval_results[:max_items]:
        event_id = result["id"]
        score = result["score"]
        metadata = result.get("metadata", {})

        # Extract what we can from metadata
        summary = metadata.get("summary", "Historical event")
        ticker = metadata.get("ticker")
        event_type = metadata.get("event_type", "")
        timestamp_str = metadata.get("timestamp", "")

        # Try to look up actual market outcome from signals
        outcome = await _get_outcome(event_id, metadata)

        # Compute human-readable time delta
        time_delta = _compute_time_delta(timestamp_str)

        # Build a descriptive summary if we only have basic metadata
        if summary == "Historical event" and event_type:
            summary = f"{event_type} event"
            if ticker:
                summary = f"{ticker} {summary}"

        evidence_items.append(EvidenceItem(
            event_id=event_id,
            event_summary=summary,
            ticker=ticker,
            outcome=outcome,
            similarity_score=round(score, 4),
            time_delta=time_delta,
        ))

    # Sort by similarity score (should already be sorted, but ensure)
    evidence_items.sort(key=lambda e: e.similarity_score, reverse=True)
    return evidence_items


async def _get_outcome(event_id: str, metadata: dict) -> str:
    """Look up the actual market outcome for a historical event.

    Tries:
    1. Metadata (if the vector store has pre-computed outcomes)
    2. Signal repo (look for signals linked to this event)
    3. Fallback to "outcome pending" if no data available
    """
    # Check if outcome is in vector store metadata
    if metadata.get("outcome"):
        return str(metadata["outcome"])

    if metadata.get("actual_move") is not None:
        move = float(metadata["actual_move"])
        direction = "+" if move >= 0 else ""
        return f"{direction}{move:.1%} move"

    # Try signal repo lookup (lazy import to avoid circular deps)
    try:
        from src.storage.signal_repo import list_signals
        signals = await list_signals(event_id=event_id, limit=1)
        if signals and signals[0].actual_move is not None:
            move = signals[0].actual_move
            direction = "+" if move >= 0 else ""
            return f"{direction}{move:.1%} within {signals[0].impact_window}"
    except Exception:
        pass

    return "Outcome data pending"


def _compute_time_delta(timestamp_str: str) -> str:
    """Convert a timestamp string to human-readable time delta from now.

    Args:
        timestamp_str: ISO format timestamp string.

    Returns:
        Human-readable string like "3 months ago" or "2 days ago".
    """
    if not timestamp_str:
        return "Unknown time"

    try:
        if isinstance(timestamp_str, str):
            # Handle various ISO formats
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            ts = timestamp_str

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        delta = now - ts

        days = delta.days
        if days < 0:
            return "In the future"
        if days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                return "Just now"
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        if days == 1:
            return "1 day ago"
        if days < 7:
            return f"{days} days ago"
        if days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        if days < 365:
            months = days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        years = days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"

    except (ValueError, TypeError):
        return "Unknown time"
