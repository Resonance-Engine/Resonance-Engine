"""Event Extraction Agent — assigns event type, sentiment, and summary.

Tools: FinBERT, Loughran-McDonald lexicon, keyword rules.
Target: F1 >0.60 on test set.
"""

from src.agents.state import PipelineState


async def event_extraction_agent(state: PipelineState) -> PipelineState:
    """Agent 3: Event with entities → Event with event_type, summary, confidence.

    TODO: Phase 0 deliverable
    - Run FinBERT sentiment classification
    - Apply Loughran-McDonald lexicon lookups
    - Classify event type via keyword rules (earnings, guidance, FDA, lawsuit, etc.)
    - Generate summary
    - Assign initial confidence score
    """
    raise NotImplementedError("Event extraction agent — Phase 0 deliverable")
