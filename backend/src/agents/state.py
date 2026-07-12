"""Pipeline state — shared typed state passed between agents via LangGraph."""

from typing import TypedDict



class PipelineState(TypedDict, total=False):
    """Shared state object flowing through the LangGraph agent pipeline.

    Each agent reads from and writes to this state. LangGraph manages
    the state transitions and ensures type safety.
    """

    # Input (set by caller)
    raw_text: str
    source_url: str
    source: str  # "SEC_EDGAR", "GDELT", "NEWSAPI"
    form_type: str  # "8-K", "10-K", "4", etc.
    filing_metadata: dict  # Raw metadata from source API

    # Set by ingestion agent
    event_id: str
    timestamp: str  # ISO format
    content_hash: str
    event_type: str | None
    summary: str | None
    raw_confidence: float | None

    # Set by entity resolution agent
    entities: list[dict]  # Serialized Entity objects
    primary_ticker: str | None

    # Set by event extraction agent
    sentiment_label: str | None  # "positive", "negative", "neutral"
    sentiment_score: float | None
    lm_scores: dict | None  # Loughran-McDonald category scores
    event_type_refined: str | None  # More specific than initial classification

    # Set by impact hypothesis agent (RAG)
    evidence: list[dict]  # Serialized EvidenceItem objects
    predicted_move: float | None
    impact_window: str | None  # "1h", "4h", "24h", "1w"
    confidence: float | None  # Calibrated confidence score
    rationale: str | None
    uncertainty: str | None

    # Set by risk gate agent
    signal_id: str | None
    signal_text: str | None
    citations: list[dict]  # Serialized Citation objects
    rejected: bool
    rejection_reason: str | None
    disclaimer: str | None

    # Pipeline metadata
    errors: list[str]
    agent_chain: list[str]  # Which agents ran
