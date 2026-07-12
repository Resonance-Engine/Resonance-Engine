"""Normalize raw API responses into canonical Event objects."""

import hashlib
import uuid
from datetime import datetime, timezone

from src.models.entity import Entity
from src.models.event import Event, EventSource


def generate_content_hash(source: str, url: str, raw_text: str) -> str:
    """SHA-256 hash (truncated to 16 hex chars) for deduplication.

    Deterministic given same inputs.
    """
    content = f"{source}|{url}|{raw_text[:500]}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def normalize_event(
    source: EventSource,
    url: str,
    raw_text: str,
    timestamp: datetime | None = None,
    metadata: dict | None = None,
    event_type: str | None = None,
    entities: list[Entity] | None = None,
) -> Event:
    """Transform a raw ingested item into a canonical Event object.

    Assigns UUID event_id, computes content hash, validates fields.

    Args:
        source: Origin of the event (SEC_EDGAR, GDELT, NEWSAPI).
        url: Source URL.
        raw_text: Raw event text.
        timestamp: Event time (defaults to now, UTC).
        metadata: Source-specific extras.
        event_type: Typed classification (e.g. "8k_item_2_02"). Required
            for the change gate's story clustering — leaving it unset
            disables clustering for this event.
        entities: Resolved entities. Also required by the change gate.

    Returns:
        Canonical Event.
    """
    return Event(
        event_id=str(uuid.uuid4()),
        timestamp=timestamp or datetime.now(timezone.utc),
        source=source,
        url=url,
        raw_text=raw_text,
        content_hash=generate_content_hash(source, url, raw_text),
        event_type=event_type,
        entities=entities or [],
        metadata=metadata or {},
    )
