"""Entity Resolution Agent — maps company mentions to canonical tickers/CIKs.

Tools: SEC companyfacts.zip, fuzzy matching, disambiguation rules.
Target: >85% precision on test set.
"""

from src.agents.state import PipelineState


async def entity_resolution_agent(state: PipelineState) -> PipelineState:
    """Agent 2: Event with raw text → Event with entities populated.

    TODO: Phase 0-1 deliverable
    - Extract company name mentions from raw_text
    - Look up in SEC companyfacts.zip (ticker → CIK mapping)
    - Fuzzy match for typos/abbreviations
    - Disambiguate (e.g., "Apple" → AAPL vs APLE)
    - Populate event.entities list
    """
    raise NotImplementedError("Entity resolution agent — Phase 0 deliverable")
