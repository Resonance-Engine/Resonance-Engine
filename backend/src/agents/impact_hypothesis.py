"""Impact Hypothesis Agent (RAG-Powered) — generates evidence-backed market hypotheses.

Combines:
1. Vector store retrieval (semantic similarity — cross-sector analogues)
2. Structured SQL lookups (exact matches — same ticker + event type)
3. Market data APIs (historical returns from Alpha Vantage / Finnhub)

Output: Signal with evidence[], confidence, rationale, uncertainty.
"""

from src.agents.state import PipelineState


async def impact_hypothesis_agent(state: PipelineState) -> PipelineState:
    """Agent 4: Event (typed) → Signal with evidence-backed hypothesis.

    RAG Flow:
    1. Embed event summary via embedder
    2. Retrieve top-K similar historical events from vector store
    3. Query market data for historical returns on matching events
    4. Combine semantic retrieval + SQL lookups
    5. Compute statistical model (avg return, volatility, confidence)
    6. Generate rationale grounded in retrieved evidence
    7. Build evidence[] array (top 3-5 items with outcomes + similarity scores)
    8. Calibrate confidence score

    TODO: Phase 1 deliverable
    - Wire up rag/retriever.py for vector search
    - Wire up rag/evidence_builder.py for evidence construction
    - Integrate with market data APIs
    - Implement confidence calibration
    """
    raise NotImplementedError("Impact hypothesis agent (RAG) — Phase 1 deliverable")
