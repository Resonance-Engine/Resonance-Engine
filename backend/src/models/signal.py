"""Signal schema — a testable, actionable statement derived from an event."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.evidence import EvidenceItem


class SignalType(StrEnum):
    VOLATILITY_SPIKE = "volatility_spike"
    POSITIVE_DRIFT = "positive_drift"
    NEGATIVE_DRIFT = "negative_drift"
    VOLUME_SURGE = "volume_surge"
    WATCH = "watch"


class Citation(BaseModel):
    """Source reference for provenance chain."""

    type: str  # "event", "historical_data", "vector_retrieval"
    id: str | None = None
    url: str | None = None
    description: str | None = None


class Signal(BaseModel):
    """A structured signal with confidence, rationale, evidence, and uncertainty."""

    signal_id: str = Field(description="UUID")
    event_id: str = Field(description="FK to triggering event")
    timestamp: datetime
    ticker: str
    signal_type: SignalType
    signal_text: str
    confidence: float = Field(ge=0.0, le=1.0, description="Calibrated probability")
    rationale: str = Field(min_length=50, description="Why this signal was generated")
    uncertainty: str = Field(min_length=20, description="Known unknowns")
    impact_window: str = Field(pattern=r"^(1h|4h|24h|1w)$")
    predicted_move: float | None = None
    actual_move: float | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
