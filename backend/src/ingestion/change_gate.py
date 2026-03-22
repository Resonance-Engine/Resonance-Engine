"""Meaningful change gating — filter noise before events enter the agent pipeline.

Only pass events that represent material new information. Saves compute on
expensive downstream agents (entity resolution, NLP, RAG retrieval).

Patterns borrowed from AgentPredict's delta-threshold design.
"""

from datetime import timedelta

from src.models.event import Event

# Events within this time window + same entity + same type are considered duplicates
CLUSTER_WINDOW = timedelta(hours=2)

# Minimum text delta to consider an amended filing as meaningful
MIN_TEXT_DELTA_RATIO = 0.05  # 5%


def is_meaningful_change(event: Event, recent_events: list[Event]) -> bool:
    """Gate: only pass events that represent material new information.

    Checks:
    1. Content hash dedup (exact duplicate)
    2. Story clustering (same entity + event_type + time window)
    3. TODO: Amended filing text-diff (Phase 0, when EDGAR parser is ready)
    """
    # Check 1: Exact content hash match
    recent_hashes = {e.content_hash for e in recent_events}
    if event.content_hash in recent_hashes:
        return False

    # Check 2: Story clustering — same primary entity + event type within window
    if event.event_type is not None and event.entities:
        primary_ticker = event.entities[0].ticker if event.entities else None
        for recent in recent_events:
            recent_ticker = recent.entities[0].ticker if recent.entities else None
            if (
                primary_ticker
                and primary_ticker == recent_ticker
                and event.event_type == recent.event_type
                and abs((event.timestamp - recent.timestamp).total_seconds())
                < CLUSTER_WINDOW.total_seconds()
            ):
                return False

    return True
