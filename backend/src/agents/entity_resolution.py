"""Entity Resolution Agent — maps company mentions to canonical tickers/CIKs.

Agent 2 in the pipeline. Uses the SEC entity resolver for ticker/CIK lookups,
plus free-text extraction for additional entities mentioned in filings.
"""

import logging

from src.agents.state import PipelineState
from src.nlp.entity_resolver import resolve_by_cik, resolve_entities

logger = logging.getLogger(__name__)


def entity_resolution_agent(state: PipelineState) -> dict:
    """Agent 2: Event with raw text → Event with resolved entities.

    Reads: raw_text, filing_metadata
    Writes: entities, primary_ticker
    """
    errors = list(state.get("errors", []))
    agent_chain = list(state.get("agent_chain", []))
    agent_chain.append("entity_resolution")

    try:
        raw_text = state.get("raw_text", "")
        metadata = state.get("filing_metadata", {})
        resolved: list[dict] = []

        # Strategy 1: CIK-based resolution (most reliable for SEC filings)
        cik = metadata.get("cik", "")
        if cik:
            entity = resolve_by_cik(str(cik))
            if entity:
                resolved.append(entity.model_dump())

        # Strategy 2: Free-text entity extraction from raw text
        if raw_text:
            text_entities = resolve_entities(raw_text[:5000])
            existing_tickers = {e.get("ticker") for e in resolved}
            for ent in text_entities:
                if ent.ticker and ent.ticker not in existing_tickers:
                    resolved.append(ent.model_dump())
                    existing_tickers.add(ent.ticker)

        # Strategy 3: Company name from metadata as fallback
        if not resolved and metadata.get("company_name"):
            from src.nlp.entity_resolver import resolve_by_name
            entity = resolve_by_name(metadata["company_name"])
            if entity:
                resolved.append(entity.model_dump())
            else:
                # Keep raw data even without ticker resolution
                resolved.append({
                    "ticker": "",
                    "cik": cik,
                    "name": metadata["company_name"],
                    "sic_code": metadata.get("sic_code"),
                })

        primary_ticker = resolved[0].get("ticker") if resolved else None

        logger.info(
            "Resolved %d entities, primary_ticker=%s",
            len(resolved), primary_ticker,
        )

        return {
            "entities": resolved,
            "primary_ticker": primary_ticker,
            "errors": errors,
            "agent_chain": agent_chain,
        }

    except Exception as e:
        logger.exception("Entity resolution agent error")
        errors.append(f"entity_resolution_agent: {e}")
        return {"entities": [], "primary_ticker": None, "errors": errors,
                "agent_chain": agent_chain}
