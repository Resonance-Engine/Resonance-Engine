"""Ingestion Agent — transforms raw API responses into normalized event data.

Agent 1 in the pipeline. Pure transformation, no external API calls.
Validates and normalizes the raw input into a structured event representation.
"""

import logging

from src.agents.state import PipelineState
from src.ingestion.normalizer import normalize_event
from src.models.event import EventSource

logger = logging.getLogger(__name__)


def ingestion_agent(state: PipelineState) -> dict:
    """Agent 1: Raw input → normalized event fields in state.

    Reads: raw_text, source_url, source, filing_metadata
    Writes: event_id, timestamp, content_hash, event_type, summary
    """
    errors = list(state.get("errors", []))
    agent_chain = list(state.get("agent_chain", []))
    agent_chain.append("ingestion")

    try:
        raw_text = state.get("raw_text", "")
        source = state.get("source", "SEC_EDGAR")
        source_url = state.get("source_url", "")
        metadata = state.get("filing_metadata", {})

        if not raw_text:
            errors.append("ingestion_agent: empty raw_text")
            return {"errors": errors, "agent_chain": agent_chain, "rejected": True,
                    "rejection_reason": "Empty raw text"}

        # Normalize the event (assigns UUID, computes content hash)
        event = normalize_event(
            source=EventSource(source),
            url=source_url,
            raw_text=raw_text,
            metadata=metadata,
        )

        # Extract initial event type from form type or metadata
        form_type = state.get("form_type", "")
        event_type = None
        if form_type == "8-K":
            item_codes = metadata.get("item_codes", [])
            if item_codes:
                event_type = f"8k_item_{item_codes[0].replace('.', '_')}"
        elif form_type == "10-K":
            event_type = "annual_report"
        elif form_type == "4":
            event_type = "insider_transaction"

        # Generate a basic summary from the first 200 chars
        summary = raw_text[:200].strip()
        if len(raw_text) > 200:
            summary += "..."

        return {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "content_hash": event.content_hash,
            "event_type": event_type,
            "summary": summary,
            "errors": errors,
            "agent_chain": agent_chain,
        }

    except Exception as e:
        logger.exception("Ingestion agent error")
        errors.append(f"ingestion_agent: {e}")
        return {"errors": errors, "agent_chain": agent_chain}
