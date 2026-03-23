"""Event schema — the canonical representation of a news/filing event."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.entity import Entity


class EventSource(StrEnum):
    SEC_EDGAR = "SEC_EDGAR"
    GDELT = "GDELT"
    NEWSAPI = "NEWSAPI"


class Event(BaseModel):
    """Canonical event object flowing through the agent pipeline."""

    event_id: str = Field(description="UUID assigned at ingestion")
    timestamp: datetime
    source: EventSource
    url: str
    raw_text: str
    content_hash: str = Field(description="SHA-256 hash for deduplication")
    entities: list[Entity] = Field(default_factory=list)
    event_type: str | None = None
    summary: str | None = None
    confidence: float | None = None
    metadata: dict = Field(default_factory=dict)
