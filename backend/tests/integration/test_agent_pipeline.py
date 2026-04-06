"""Integration test: full agent pipeline end-to-end.

Tests the LangGraph pipeline with real agents but mocked external services
(no Pinecone, no OpenAI, no PostgreSQL required).
"""

import pytest

from src.agents.pipeline import build_pipeline, run_pipeline


@pytest.mark.asyncio
async def test_pipeline_builds():
    """Pipeline should compile without errors."""
    pipeline = build_pipeline()
    assert pipeline is not None


@pytest.mark.asyncio
async def test_full_pipeline_earnings_event():
    """Full pipeline should process an earnings event end-to-end."""
    raw_event = {
        "raw_text": (
            "Apple Inc. reported quarterly earnings per share of $1.52, "
            "beating analyst expectations of $1.47. Revenue came in at "
            "$94.8 billion, up 5% year-over-year. The company issued "
            "favorable guidance for Q3 with expected revenue growth."
        ),
        "source_url": "https://sec.gov/cgi-bin/test",
        "source": "SEC_EDGAR",
        "form_type": "8-K",
        "filing_metadata": {
            "item_codes": ["2.02"],
            "company_name": "Apple Inc.",
            "cik": "320193",
        },
    }

    result = await run_pipeline(raw_event)

    # Pipeline should complete (may reject due to missing RAG, but should not crash)
    assert "agent_chain" in result
    assert "ingestion" in result["agent_chain"]
    assert "entity_resolution" in result["agent_chain"]
    assert "event_extraction" in result["agent_chain"]

    # Event ID should be generated
    assert result.get("event_id") is not None

    # Sentiment should be extracted
    assert result.get("sentiment_label") in ("positive", "negative", "neutral")


@pytest.mark.asyncio
async def test_pipeline_empty_text_rejected():
    """Empty raw text should be rejected at ingestion stage."""
    raw_event = {
        "raw_text": "",
        "source_url": "",
        "source": "SEC_EDGAR",
        "form_type": "8-K",
        "filing_metadata": {},
    }
    result = await run_pipeline(raw_event)
    assert result.get("rejected") is True


@pytest.mark.asyncio
async def test_pipeline_generates_signal():
    """Pipeline should generate a signal for a substantive event."""
    raw_event = {
        "raw_text": (
            "Tesla Inc. announced a major restructuring plan involving "
            "a workforce reduction of 10,000 employees. The restructuring "
            "is expected to result in charges of approximately $500 million. "
            "CEO stated that the layoff was necessary due to declining demand "
            "and increasing competition in the electric vehicle market."
        ),
        "source_url": "https://sec.gov/test/tesla",
        "source": "SEC_EDGAR",
        "form_type": "8-K",
        "filing_metadata": {
            "item_codes": ["2.05"],
            "company_name": "Tesla Inc.",
        },
    }
    result = await run_pipeline(raw_event)

    # Should reach at least impact_hypothesis
    assert "impact_hypothesis" in result.get("agent_chain", [])

    # Should have confidence and rationale
    if not result.get("rejected"):
        assert result.get("signal_id") is not None
        assert result.get("confidence") is not None
        assert 0.0 <= result["confidence"] <= 0.95
        assert result.get("rationale") is not None
        assert result.get("uncertainty") is not None


@pytest.mark.asyncio
async def test_pipeline_risk_gate_runs():
    """Risk gate should always run for non-rejected events."""
    raw_event = {
        "raw_text": (
            "Company X has entered into a definitive merger agreement "
            "to acquire Company Y for $2 billion. The acquisition is "
            "expected to close in Q4 pending regulatory approval."
        ),
        "source_url": "https://sec.gov/test",
        "source": "SEC_EDGAR",
        "form_type": "8-K",
        "filing_metadata": {"item_codes": ["1.01"]},
    }
    result = await run_pipeline(raw_event)
    assert "risk_gate" in result.get("agent_chain", [])
