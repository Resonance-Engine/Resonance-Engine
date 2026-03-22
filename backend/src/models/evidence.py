"""EvidenceItem schema — a retrieved similar historical event backing a signal."""

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """A single piece of retrieved evidence from the vector store."""

    event_id: str = Field(description="ID of the historical event in our database")
    event_summary: str = Field(description="What happened (human-readable)")
    ticker: str | None = Field(default=None, description="Which company (null for sector-wide)")
    outcome: str = Field(description="What was the market reaction")
    similarity_score: float = Field(ge=0.0, le=1.0, description="Cosine similarity to trigger event")
    time_delta: str = Field(description="How long ago this happened (human-readable)")
