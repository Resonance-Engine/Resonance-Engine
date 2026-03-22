"""Shared test fixtures — DB sessions, Redis mocks, test data factories."""

import pytest

from src.models.entity import Entity
from src.models.event import Event, EventSource
from src.models.evidence import EvidenceItem
from src.models.signal import Citation, Signal, SignalType


@pytest.fixture
def sample_entity() -> Entity:
    return Entity(ticker="AAPL", cik="0000320193", name="Apple Inc.", sic_code="3571")


@pytest.fixture
def sample_event(sample_entity) -> Event:
    from datetime import datetime

    return Event(
        event_id="evt_test_001",
        timestamp=datetime(2026, 3, 9, 14, 30, 0),
        source=EventSource.SEC_EDGAR,
        url="https://sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193",
        raw_text="Apple Inc. has filed an 8-K current report regarding Q2 guidance revision.",
        content_hash="abc123def456",
        entities=[sample_entity],
        event_type="guidance_revision",
        summary="Apple Q2 guidance cut by 5%, supply chain concerns cited.",
        confidence=0.85,
    )


@pytest.fixture
def sample_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            event_id="evt_20250815_042",
            event_summary="AAPL Q3 2025 guidance cut by 3%",
            ticker="AAPL",
            outcome="+2.8% intraday move",
            similarity_score=0.94,
            time_delta="7 months ago",
        ),
        EvidenceItem(
            event_id="evt_20241120_019",
            event_summary="MSFT Q4 2024 guidance revision downward by 4%",
            ticker="MSFT",
            outcome="-3.2% intraday move",
            similarity_score=0.87,
            time_delta="16 months ago",
        ),
    ]


@pytest.fixture
def sample_signal(sample_evidence) -> Signal:
    from datetime import datetime

    return Signal(
        signal_id="sig_test_001",
        event_id="evt_test_001",
        timestamp=datetime(2026, 3, 9, 14, 35, 0),
        ticker="AAPL",
        signal_type=SignalType.VOLATILITY_SPIKE,
        signal_text="High probability of short-term volatility increase for AAPL in next 4 hours",
        confidence=0.78,
        rationale=(
            "Historical precedent: guidance cuts typically trigger 2-5% intraday moves. "
            "Apple's Q2 guidance cut by 5% is material. Across 23 similar guidance revisions, "
            "median intraday move was 3.1%."
        ),
        uncertainty=(
            "Direction uncertain (could move up or down). Supply chain issues are complex "
            "and market reaction depends on broader tech sector sentiment."
        ),
        impact_window="4h",
        evidence=sample_evidence,
        citations=[
            Citation(type="event", id="evt_test_001", url="https://sec.gov/..."),
            Citation(type="vector_retrieval", description="Top-2 similar guidance revisions"),
        ],
        metadata={
            "model_version": "v0.1.0",
            "agent_chain": ["ingestion", "entity_resolution", "event_extraction", "impact_hypothesis", "risk_gate"],
            "evidence_count": 2,
            "avg_similarity": 0.905,
        },
    )
