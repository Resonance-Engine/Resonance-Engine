"""Tests for risk gate agent (full agent, not just regex)."""

from src.agents.risk_gate import risk_gate_agent


def _make_state(**overrides) -> dict:
    """Build a valid state that passes all checks."""
    state = {
        "confidence": 0.75,
        "rationale": (
            "A earnings event was detected for AAPL with positive sentiment. "
            "Based on historical patterns, similar events led to price movement."
        ),
        "uncertainty": "Market conditions may override historical patterns. Direction is uncertain.",
        "evidence": [{"event_id": "e1", "similarity_score": 0.9}],
        "primary_ticker": "AAPL",
        "event_type_refined": "earnings",
        "event_type": "earnings",
        "predicted_move": 0.03,
        "impact_window": "4h",
        "event_id": "evt_001",
        "source_url": "https://sec.gov/test",
        "errors": [],
        "agent_chain": ["ingestion", "entity_resolution", "event_extraction", "impact_hypothesis"],
    }
    state.update(overrides)
    return state


def test_approves_valid_signal():
    """Valid state should produce an approved signal."""
    result = risk_gate_agent(_make_state())
    assert result["rejected"] is False
    assert result["signal_id"] is not None
    assert result["signal_text"] is not None
    assert "risk_gate" in result["agent_chain"]


def test_rejects_low_confidence():
    """Confidence below 0.4 should be rejected."""
    result = risk_gate_agent(_make_state(confidence=0.3))
    assert result["rejected"] is True
    assert "confidence" in result["rejection_reason"].lower()


def test_rejects_blocked_language():
    """Investment advice language in rationale should be rejected."""
    result = risk_gate_agent(_make_state(
        rationale="Based on analysis, you should buy this stock immediately to guarantee returns."
    ))
    assert result["rejected"] is True
    assert "investment advice" in result["rejection_reason"].lower()


def test_rejects_short_rationale():
    """Short rationale should be rejected."""
    result = risk_gate_agent(_make_state(rationale="Too short."))
    assert result["rejected"] is True
    assert "rationale" in result["rejection_reason"].lower()


def test_rejects_missing_uncertainty():
    """Missing uncertainty should be rejected."""
    result = risk_gate_agent(_make_state(uncertainty=""))
    assert result["rejected"] is True
    assert "uncertainty" in result["rejection_reason"].lower()


def test_caps_overconfident():
    """Confidence > 0.95 should be capped to 0.95."""
    result = risk_gate_agent(_make_state(confidence=0.99))
    assert result["rejected"] is False
    assert result["confidence"] == 0.95


def test_no_evidence_warning():
    """Missing evidence should add warning but not reject."""
    result = risk_gate_agent(_make_state(evidence=[]))
    assert result["rejected"] is False
    assert any("no evidence" in e for e in result.get("errors", []))


def test_citations_built():
    """Citations should include event and evidence references."""
    result = risk_gate_agent(_make_state())
    assert result["rejected"] is False
    citations = result.get("citations", [])
    assert len(citations) >= 1
    assert any(c["type"] == "event" for c in citations)


def test_disclaimer_present():
    """Approved signal should have disclaimer."""
    result = risk_gate_agent(_make_state())
    assert result["disclaimer"] is not None
    assert "not investment advice" in result["disclaimer"].lower()
