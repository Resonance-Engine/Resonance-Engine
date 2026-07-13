"""Tests for the calibrated magnitude model and its pipeline wiring.

Model provenance: CRUCIBLE Finding 004 (exp004, fit 2026-07-13). Expected
values below are computed from the published weights, not re-derived from
the code under test.
"""

import math

import pytest

from src.agents.impact_hypothesis import impact_hypothesis_agent
from src.agents.magnitude import (
    extract_item_codes,
    magnitude_probability,
)


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


# --- extract_item_codes ---


def test_extract_item_codes_from_filing_markers():
    text = "[Item 2.02] Results of Operations...\n\n[Item 9.01] Exhibits..."
    assert extract_item_codes(text) == ["2.02", "9.01"]


def test_extract_item_codes_deduplicates_and_matches_bare_mentions():
    text = "Item 2.02 disclosed. See Item 2.02 above; also Item 5.02 applies."
    assert extract_item_codes(text) == ["2.02", "5.02"]


def test_extract_item_codes_empty_when_absent():
    assert extract_item_codes("Apple reports record quarterly earnings.") == []


# --- magnitude_probability ---


def test_earnings_filing_probability_matches_published_weights():
    # bias -1.167 + 2.02 (1.7975) + 9.01 (0.1998) = 0.8303
    expected = _sigmoid(0.8303)
    assert magnitude_probability(["2.02", "9.01"]) == pytest.approx(expected, abs=1e-6)
    assert expected > 0.65  # earnings filings are likely movers


def test_routine_filing_falls_below_risk_gate():
    # Shareholder vote only: bias -1.167 + 5.07 (-0.1059) → ~0.22
    p = magnitude_probability(["5.07"])
    assert p < 0.40  # risk gate's rejection line — routine filings get filtered


def test_unknown_item_codes_are_ignored():
    assert magnitude_probability(["3.03"]) == pytest.approx(
        magnitude_probability([]), abs=1e-9
    )


def test_higher_trailing_vol_raises_probability():
    low = magnitude_probability(["2.02"], trailing_vol=1.0)
    avg = magnitude_probability(["2.02"], trailing_vol=None)  # train-mean assumption
    high = magnitude_probability(["2.02"], trailing_vol=4.0)
    assert low < avg < high


def test_probability_bounds():
    assert 0.0 < magnitude_probability([]) < 1.0
    assert 0.0 < magnitude_probability(list(["2.02"]) * 1, trailing_vol=50.0) < 1.0


# --- pipeline wiring (impact_hypothesis agent) ---


def _base_state(**overrides) -> dict:
    state = {
        "raw_text": "Company discloses quarterly results.",
        "source": "SEC_EDGAR",
        "event_type_refined": "earnings",
        "entities": [],
        "primary_ticker": "TEST",
        "sentiment_label": "neutral",
        "sentiment_score": 0.5,
        "raw_confidence": 0.5,
        "errors": [],
        "agent_chain": [],
    }
    state.update(overrides)
    return state


async def test_agent_uses_magnitude_model_for_8k_with_metadata_item_codes():
    state = _base_state(filing_metadata={"item_codes": ["2.02", "9.01"]})
    result = await impact_hypothesis_agent(state)
    assert result["confidence"] == pytest.approx(
        magnitude_probability(["2.02", "9.01"]), abs=1e-4
    )
    assert "magnitude" in result["uncertainty"]
    assert "2.02" in result["rationale"]


async def test_agent_extracts_item_codes_from_raw_text_fallback():
    state = _base_state(
        raw_text="[Item 5.07] Submission of Matters to a Vote of Security Holders."
    )
    result = await impact_hypothesis_agent(state)
    assert result["confidence"] == pytest.approx(
        magnitude_probability(["5.07"]), abs=1e-4
    )
    assert result["confidence"] < 0.40  # routine filing → below risk gate


async def test_agent_keeps_legacy_formula_for_non_edgar_sources():
    state = _base_state(
        source="NEWSAPI",
        raw_text="Article mentions Item 2.02 of some filing.",
    )
    result = await impact_hypothesis_agent(state)
    # Legacy zero-evidence formula: 0.42 anchor at raw_confidence=0.5
    assert result["confidence"] == pytest.approx(0.42, abs=1e-4)


async def test_agent_keeps_legacy_formula_when_no_item_codes():
    state = _base_state()
    result = await impact_hypothesis_agent(state)
    assert result["confidence"] == pytest.approx(0.42, abs=1e-4)
    assert "magnitude" not in result["uncertainty"]
