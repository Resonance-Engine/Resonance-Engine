"""Tests for RAG-powered impact hypothesis agent."""

import pytest

from src.agents.impact_hypothesis import (
    _build_rationale,
    _build_uncertainty,
    _compute_predicted_move,
    _determine_impact_window,
    impact_hypothesis_agent,
)


# --- Predicted Move Computation ---

def test_predicted_move_from_evidence():
    """Should compute average move from evidence outcomes."""
    evidence = [
        {"outcome": "+3.2% move", "similarity_score": 0.9},
        {"outcome": "-1.5% move", "similarity_score": 0.85},
    ]
    move = _compute_predicted_move(evidence, "positive")
    assert move is not None
    assert isinstance(move, float)


def test_predicted_move_no_evidence():
    """Should fall back to sentiment-based estimate without evidence."""
    move = _compute_predicted_move([], "positive")
    assert move == 0.02

    move = _compute_predicted_move([], "negative")
    assert move == -0.02


def test_predicted_move_neutral():
    """Neutral sentiment with no evidence returns None."""
    move = _compute_predicted_move([], "neutral")
    assert move is None


# --- Impact Window ---

def test_impact_window_earnings():
    assert _determine_impact_window("earnings") == "4h"


def test_impact_window_merger():
    assert _determine_impact_window("merger_acquisition") == "1w"


def test_impact_window_default():
    assert _determine_impact_window("unknown_type") == "24h"


# --- Rationale Building ---

def test_rationale_includes_ticker():
    rationale = _build_rationale("AAPL", "earnings", "positive", 0.85, 0.03, [], 0)
    assert "AAPL" in rationale


def test_rationale_includes_evidence():
    evidence = [
        {"event_summary": "Q3 earnings beat", "outcome": "+2.5% move", "similarity_score": 0.9},
    ]
    rationale = _build_rationale("AAPL", "earnings", "positive", 0.85, 0.025, evidence, 1)
    assert "Q3 earnings beat" in rationale
    assert "historical" in rationale.lower()


def test_rationale_no_evidence_fallback():
    """When no evidence, rationale should mention sentiment-based analysis."""
    rationale = _build_rationale("AAPL", "earnings", "positive", 0.85, 0.03, [], 0)
    # Disclaimer is appended by risk_gate agent, not here
    assert "sentiment" in rationale.lower()


# --- Uncertainty Building ---

def test_uncertainty_low_evidence():
    uncertainty = _build_uncertainty("earnings", 1, "positive")
    assert "limited" in uncertainty.lower()


def test_uncertainty_neutral_sentiment():
    uncertainty = _build_uncertainty("earnings", 5, "neutral")
    assert "uncertain" in uncertainty.lower()


def test_uncertainty_event_specific():
    uncertainty = _build_uncertainty("fda_approval", 5, "positive")
    assert "binary" in uncertainty.lower() or "regulatory" in uncertainty.lower()


# --- Full Agent (without RAG dependencies) ---

@pytest.mark.asyncio
async def test_agent_generates_hypothesis():
    """Agent should produce a hypothesis even without RAG (fallback mode)."""
    state = {
        "event_id": "evt_test_001",
        "raw_text": "Apple reports record quarterly earnings.",
        "source": "SEC_EDGAR",
        "source_url": "https://sec.gov/test",
        "content_hash": "abc123",
        "event_type_refined": "earnings",
        "primary_ticker": "AAPL",
        "sentiment_label": "positive",
        "sentiment_score": 0.85,
        "raw_confidence": 0.75,
        "summary": "Apple Q2 earnings",
        "errors": [],
        "agent_chain": ["ingestion", "entity_resolution", "event_extraction"],
    }
    result = await impact_hypothesis_agent(state)
    assert "impact_hypothesis" in result["agent_chain"]
    assert result.get("confidence") is not None
    assert 0.0 <= result["confidence"] <= 1.0
    assert result.get("rationale") is not None
    assert len(result["rationale"]) >= 50
    assert result.get("uncertainty") is not None
    assert result.get("impact_window") in ("1h", "4h", "24h", "1w")


@pytest.mark.asyncio
async def test_agent_confidence_capped():
    """Confidence should never exceed 0.95."""
    state = {
        "event_id": "evt_test_002",
        "raw_text": "Test event",
        "source": "SEC_EDGAR",
        "source_url": "",
        "content_hash": "xyz",
        "event_type_refined": "earnings",
        "primary_ticker": "TST",
        "sentiment_label": "positive",
        "sentiment_score": 1.0,
        "raw_confidence": 1.0,
        "summary": "test",
        "errors": [],
        "agent_chain": [],
    }
    result = await impact_hypothesis_agent(state)
    assert result["confidence"] <= 0.95
