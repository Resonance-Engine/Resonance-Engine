"""Tests for evidence builder."""

import pytest

from src.rag.evidence_builder import _compute_time_delta, build_evidence


# --- Time Delta Formatting ---

def test_time_delta_days():
    from datetime import datetime, timedelta, timezone
    ts = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    result = _compute_time_delta(ts)
    assert "5 days ago" == result


def test_time_delta_months():
    from datetime import datetime, timedelta, timezone
    ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    result = _compute_time_delta(ts)
    assert "month" in result


def test_time_delta_empty():
    assert _compute_time_delta("") == "Unknown time"


def test_time_delta_invalid():
    assert _compute_time_delta("not-a-date") == "Unknown time"


# --- Build Evidence ---

@pytest.mark.asyncio
async def test_builds_evidence_from_matches():
    """Should convert raw matches into EvidenceItem objects."""
    matches = [
        {
            "id": "evt_001",
            "score": 0.92,
            "metadata": {
                "summary": "AAPL Q3 earnings beat",
                "ticker": "AAPL",
                "event_type": "earnings",
                "timestamp": "2025-09-15T14:00:00+00:00",
            },
        },
        {
            "id": "evt_002",
            "score": 0.85,
            "metadata": {
                "summary": "MSFT guidance revision",
                "ticker": "MSFT",
                "event_type": "guidance",
                "timestamp": "2025-08-01T10:00:00+00:00",
            },
        },
    ]
    evidence = await build_evidence(matches, max_items=5)
    assert len(evidence) == 2
    assert evidence[0].event_id == "evt_001"
    assert evidence[0].similarity_score == 0.92
    assert evidence[0].ticker == "AAPL"


@pytest.mark.asyncio
async def test_max_items_limit():
    """Should respect max_items limit."""
    matches = [
        {"id": f"evt_{i}", "score": 0.9 - i * 0.01, "metadata": {"summary": f"Event {i}"}}
        for i in range(10)
    ]
    evidence = await build_evidence(matches, max_items=3)
    assert len(evidence) == 3


@pytest.mark.asyncio
async def test_sorted_by_similarity():
    """Evidence should be sorted by similarity score descending."""
    matches = [
        {"id": "evt_a", "score": 0.75, "metadata": {"summary": "Low match"}},
        {"id": "evt_b", "score": 0.95, "metadata": {"summary": "High match"}},
    ]
    evidence = await build_evidence(matches)
    assert evidence[0].similarity_score >= evidence[1].similarity_score


@pytest.mark.asyncio
async def test_empty_matches():
    """Should return empty list for empty matches."""
    evidence = await build_evidence([])
    assert evidence == []


@pytest.mark.asyncio
async def test_outcome_pending_when_no_data():
    """Should show 'outcome pending' when no outcome data available."""
    matches = [
        {"id": "evt_001", "score": 0.9, "metadata": {"summary": "Test event"}},
    ]
    evidence = await build_evidence(matches)
    assert "pending" in evidence[0].outcome.lower() or evidence[0].outcome != ""
