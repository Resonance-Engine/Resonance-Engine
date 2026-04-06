"""Pipeline routes — POST /pipeline/run to trigger signal generation."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
logger = logging.getLogger(__name__)


class PipelineRequest(BaseModel):
    raw_text: str
    source: str = "SEC_EDGAR"
    url: str = ""
    filing_type: str | None = None
    cik: str | None = None


class PipelineResponse(BaseModel):
    status: str
    signal_id: str | None = None
    event_id: str | None = None
    rejection_reason: str | None = None


@router.post("/run")
async def run_pipeline(
    body: PipelineRequest,
    _user: str = Depends(get_current_user),
) -> PipelineResponse:
    """Run the LangGraph agent pipeline on raw input text.

    Returns the generated signal_id on success, or rejection_reason if
    the pipeline rejected the input at ingestion or risk gate.
    """
    try:
        from src.agents.pipeline import run_pipeline

        result = await run_pipeline({
            "raw_text": body.raw_text,
            "source": body.source,
            "url": body.url,
            "filing_type": body.filing_type,
            "cik": body.cik,
        })

        if result.get("rejected"):
            return PipelineResponse(
                status="rejected",
                event_id=result.get("event_id"),
                rejection_reason=result.get("rejection_reason", "Unknown"),
            )

        return PipelineResponse(
            status="completed",
            signal_id=result.get("signal_id"),
            event_id=result.get("event_id"),
        )

    except Exception as e:
        logger.exception("Pipeline execution failed")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}") from e
