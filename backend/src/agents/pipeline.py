"""LangGraph workflow orchestration — the 6-agent pipeline.

Ingestion → Entity Resolution → Event Extraction → Impact Hypothesis (RAG) → Risk Gate → Signal Store
"""

# TODO: Phase 1 — implement LangGraph StateGraph workflow
# from langgraph.graph import StateGraph, END
# from src.agents.state import PipelineState


def build_pipeline():
    """Build and return the LangGraph agent pipeline.

    TODO: Phase 1 deliverable
    - Add nodes for each agent
    - Wire edges (sequential flow)
    - Set entry point to ingestion_agent
    - Return compiled workflow
    """
    raise NotImplementedError("Agent pipeline — Phase 1 deliverable")


async def run_pipeline(raw_event: dict) -> dict:
    """Run an event through the full agent pipeline.

    TODO: Phase 1 deliverable
    - Build pipeline
    - Execute with raw_event as input
    - Return final state (signal or rejection)
    """
    raise NotImplementedError("Pipeline execution — Phase 1 deliverable")
