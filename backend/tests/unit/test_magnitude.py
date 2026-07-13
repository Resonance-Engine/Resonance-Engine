"""Tests for the calibrated magnitude model and its pipeline wiring.

Model provenance: CRUCIBLE Findings 004/007 (v2 weights, exp007, fit
2026-07-13 on the S&P 500 universe). Expected values below are computed
from the published weights, not re-derived from the code under test.
"""

import math

import pytest

from src.agents.impact_hypothesis import impact_hypothesis_agent
from src.agents.magnitude import (
    extract_item_codes,
    magnitude_probability,
    major_move_probability,
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
    # v2: bias -1.2436 + 2.02 (1.8769) + 9.01 (0.0735) = 0.7068
    expected = _sigmoid(0.7068)
    assert magnitude_probability(["2.02", "9.01"]) == pytest.approx(expected, abs=1e-6)
    assert expected > 0.65  # earnings filings are likely movers


def test_routine_filing_falls_below_risk_gate():
    # Shareholder vote only: v2 bias -1.2436 + 5.07 (-0.4124) → ~0.16
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


# --- major_move_probability (Finding 009) ---


def test_major_earnings_filing_matches_published_weights():
    # v bias -2.4142 + 2.02 (2.0024) + 9.01 (-0.1342) = -0.546
    expected = _sigmoid(-0.546)
    assert major_move_probability(["2.02", "9.01"]) == pytest.approx(expected, abs=1e-6)


def test_major_sector_weight_uses_two_digit_sic_group():
    base = major_move_probability(["2.02"])
    software = major_move_probability(["2.02"], sic_code="7372")  # sic 73: +0.4693
    utility = major_move_probability(["2.02"], sic_code="4911")  # sic 49: -0.6874
    unknown = major_move_probability(["2.02"], sic_code="9999")  # not in table
    assert software > base > utility
    assert unknown == pytest.approx(base, abs=1e-9)


def test_major_is_rarer_than_material():
    # P(>=5%) must be below P(>=2%) for the same filing — sanity ordering
    for items in (["2.02", "9.01"], ["5.07"], ["8.01"]):
        assert major_move_probability(items) < magnitude_probability(items)


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
    assert result["major_move_probability"] == pytest.approx(
        major_move_probability(["2.02", "9.01"]), abs=1e-4
    )


async def test_agent_major_tier_uses_entity_sic_and_flags_rationale():
    # Software sector (SIC 73) pushes an earnings 8-K over the 0.40 alert line
    state = _base_state(
        filing_metadata={"item_codes": ["2.02"]},
        entities=[{"ticker": "TEST", "sic_code": "7372"}],
    )
    result = await impact_hypothesis_agent(state)
    expected = major_move_probability(["2.02"], sic_code="7372")
    assert result["major_move_probability"] == pytest.approx(expected, abs=1e-4)
    assert expected >= 0.40
    assert "MAJOR IMPACT TIER" in result["rationale"]


async def test_agent_major_tier_absent_for_non_calibrated_events():
    result = await impact_hypothesis_agent(_base_state())
    assert result["major_move_probability"] is None
    assert "MAJOR IMPACT TIER" not in (result["rationale"] or "")


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
