"""Ingestion Agent — transforms raw API responses into canonical Event objects."""

from src.agents.state import PipelineState


async def ingestion_agent(state: PipelineState) -> PipelineState:
    """Agent 1: Raw input → normalized Event.

    Pure transformation, no external tools.
    Validates via Pydantic schema enforcement.

    TODO: Phase 1 — implement transformation logic
    """
    raise NotImplementedError("Ingestion agent — Phase 1 deliverable")
