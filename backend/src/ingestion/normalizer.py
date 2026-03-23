"""Normalize raw API responses into canonical Event objects."""

import hashlib
import uuid
from datetime import datetime

from src.models.event import Event, EventSource


def generate_content_hash(source: str, url: str, raw_text: str) -> str:
    """SHA-256 hash for deduplication. Deterministic given same inputs."""
    content = f"{source}|{url}|{raw_text[:500]}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def normalize_event(
    source: EventSource,
    url: str,
    raw_text: str,
    timestamp: datetime | None = None,
    metadata: dict | None = None,
) -> Event:
    """Transform a raw ingested item into a canonical Event object.

    Assigns UUID event_id, computes content hash, validates fields.
    """
    return Event(
        event_id=str(uuid.uuid4()),
        timestamp=timestamp or datetime.utcnow(),
        source=source,
        url=url,
        raw_text=raw_text,
        content_hash=generate_content_hash(source, url, raw_text),
        metadata=metadata or {},
    )
