"""Tests for event extraction agent."""

from src.agents.event_extraction import EVENT_TYPE_RULES, event_extraction_agent


async def test_earnings_classification():
    """Earnings-related text should be classified as 'earnings'."""
    state = {
        "raw_text": "Apple Inc. reported quarterly earnings of $1.52 per share, beating estimates by $0.05.",
        "event_type": "8k_item_2_02",
        "summary": "Apple Q2 earnings report",
        "primary_ticker": "AAPL",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert result["event_type_refined"] == "earnings"
    assert result["sentiment_label"] in ("positive", "negative", "neutral")


async def test_lawsuit_classification():
    """Litigation text should be classified as 'lawsuit'."""
    state = {
        "raw_text": "The company has been sued in a class action lawsuit alleging securities fraud and litigation damages.",
        "event_type": None,
        "summary": "",
        "primary_ticker": "XYZ",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert result["event_type_refined"] == "lawsuit"


async def test_fda_classification():
    """FDA-related text should be classified as 'fda_approval'."""
    state = {
        "raw_text": "The FDA has granted approval for the company's new drug treatment following successful clinical trial phase 3.",
        "event_type": None,
        "summary": "",
        "primary_ticker": "PFE",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert result["event_type_refined"] == "fda_approval"


async def test_merger_classification():
    """M&A text should be classified as 'merger_acquisition'."""
    state = {
        "raw_text": "Company A has entered into a definitive agreement to acquire Company B for $5 billion in a merger deal.",
        "event_type": None,
        "summary": "",
        "primary_ticker": "ACQA",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert result["event_type_refined"] == "merger_acquisition"


async def test_sentiment_negative():
    """Negative financial text should produce negative sentiment."""
    state = {
        "raw_text": "The company reported a loss and negative revenue decline with impairment charges and restructuring costs.",
        "event_type": None,
        "summary": "",
        "primary_ticker": "BAD",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert result["sentiment_label"] == "negative"


async def test_lm_scores_populated():
    """LM lexicon scores should be populated in result."""
    state = {
        "raw_text": "Revenue increased substantially with favorable growth prospects.",
        "event_type": None,
        "summary": "",
        "primary_ticker": "TST",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert "lm_scores" in result
    assert "net_sentiment" in result["lm_scores"]
    assert "total_words" in result["lm_scores"]


async def test_summary_enriched_with_ticker():
    """Summary should include ticker and event type when available."""
    state = {
        "raw_text": "Apple Inc. reported quarterly earnings beating analyst expectations.",
        "event_type": "8k_item_2_02",
        "summary": "Earnings report filed",
        "primary_ticker": "AAPL",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert "AAPL" in result["summary"]


async def test_confidence_in_bounds():
    """Raw confidence should be between 0 and 1."""
    state = {
        "raw_text": "Company announced major restructuring and layoff of 5000 employees.",
        "event_type": None,
        "summary": "",
        "primary_ticker": "TST",
        "errors": [],
        "agent_chain": [],
    }
    result = await event_extraction_agent(state)
    assert 0.0 <= result.get("raw_confidence", 0) <= 1.0


async def test_agent_chain_updated():
    """Agent chain should include event_extraction."""
    state = {
        "raw_text": "Test text",
        "event_type": None,
        "summary": "",
        "errors": [],
        "agent_chain": ["ingestion", "entity_resolution"],
    }
    result = await event_extraction_agent(state)
    assert "event_extraction" in result["agent_chain"]
