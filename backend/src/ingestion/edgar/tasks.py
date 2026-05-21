"""Celery tasks for EDGAR ingestion — scheduled polling + processing."""

import asyncio
import logging
from datetime import date, datetime, timezone

from src.celery_app import app
from src.ingestion.change_gate import is_meaningful_change
from src.ingestion.deduplicator import is_duplicate
from src.ingestion.edgar.client import fetch_filing_document, fetch_recent_filings
from src.ingestion.edgar.parser import parse_8k_filing
from src.ingestion.normalizer import normalize_event
from src.models.entity import Entity
from src.models.event import EventSource
from src.nlp.entity_resolver import resolve_by_cik, resolve_entities

logger = logging.getLogger(__name__)


def _filing_to_event(parsed: dict, file_url: str):
    """Convert a parsed filing dict into a normalized Event."""
    # Build entity from parsed filing data, resolving ticker via entity resolver
    entities = []
    cik = parsed.get("cik", "")
    company_name = parsed.get("company_name", "")

    # Try CIK-based resolution first (most reliable for SEC filings)
    if cik:
        resolved = resolve_by_cik(cik)
        if resolved:
            entities.append(Entity(
                ticker=resolved.ticker,
                cik=cik,
                name=resolved.name,
                sic_code=parsed.get("sic_code") or resolved.sic_code,
            ))

    # Fallback: resolve from filing text (catches additional mentioned entities)
    if not entities and company_name:
        text_entities = resolve_entities(company_name)
        if text_entities:
            entities.append(Entity(
                ticker=text_entities[0].ticker,
                cik=cik or text_entities[0].cik,
                name=text_entities[0].name,
                sic_code=parsed.get("sic_code") or text_entities[0].sic_code,
            ))

    # Last resort: use raw parsed data with empty ticker
    if not entities and company_name:
        entities.append(Entity(
            ticker="",
            cik=cik,
            name=company_name,
            sic_code=parsed.get("sic_code"),
        ))

    # Also extract any additional entities mentioned in the filing text
    raw_text_for_resolution = ""
    for item in parsed.get("items", []):
        raw_text_for_resolution += item.get("text", "") + " "
    if raw_text_for_resolution.strip():
        additional = resolve_entities(raw_text_for_resolution)
        existing_tickers = {e.ticker for e in entities}
        for ent in additional:
            if ent.ticker and ent.ticker not in existing_tickers:
                entities.append(ent)
                existing_tickers.add(ent.ticker)

    # Determine event type from 8-K item codes
    event_type = None
    item_codes = parsed.get("item_codes", [])
    if item_codes:
        # Map primary item code to a human-readable event type
        primary = item_codes[0]
        event_type = f"8k_item_{primary.replace('.', '_')}"

    # Parse filed date
    filed_str = parsed.get("filed_date", "")
    timestamp = None
    if filed_str and len(filed_str) == 8:
        try:
            timestamp = datetime.strptime(filed_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if filed_str and len(filed_str) == 10:
        try:
            timestamp = datetime.strptime(filed_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # Build the raw text: item texts joined, fallback to full_text
    raw_text = ""
    for item in parsed.get("items", []):
        raw_text += f"[Item {item['item_code']}] {item['text']}\n\n"
    if not raw_text:
        raw_text = parsed.get("full_text", "")[:10000]

    return normalize_event(
        source=EventSource.SEC_EDGAR,
        url=file_url,
        raw_text=raw_text,
        timestamp=timestamp,
        metadata={
            "form_type": parsed.get("form_type", "8-K"),
            "accession_number": parsed.get("accession_number", ""),
            "item_codes": item_codes,
            "is_boilerplate": parsed.get("is_boilerplate", False),
            "entities_raw": [e.model_dump() for e in entities],
        },
    )


@app.task(name="edgar.poll_recent_filings", bind=True, max_retries=3)
def poll_recent_filings(self, form_type: str = "8-K", limit: int = 100) -> dict:
    """Poll EDGAR for recent filings, normalize, dedup, and store.

    Scheduled via Celery Beat (every 5 minutes during market hours).

    Returns:
        Summary dict with counts: fetched, parsed, new, stored, skipped.
    """
    return asyncio.get_event_loop().run_until_complete(
        _poll_recent_filings_async(form_type, limit)
    )


async def _poll_recent_filings_async(form_type: str, limit: int) -> dict:
    """Async implementation of the polling task."""
    from src.storage.event_repo import insert_event

    stats = {"fetched": 0, "parsed": 0, "new": 0, "stored": 0, "skipped_dup": 0, "skipped_boilerplate": 0}
    recent_events = []

    # 1. Fetch recent filing metadata
    today = date.today().isoformat()
    filings = await fetch_recent_filings(
        form_type=form_type,
        start_date=today,
        end_date=today,
        limit=limit,
    )
    stats["fetched"] = len(filings)
    logger.info("Fetched %d %s filings from EDGAR", len(filings), form_type)

    for filing in filings:
        accession = filing.get("accession_number", "")
        cik = filing.get("cik", "")
        file_url = filing.get("file_url", "")

        # 2. Fetch full filing document
        try:
            raw_text = await fetch_filing_document(accession, cik)
        except Exception:
            logger.exception("Failed to fetch filing %s", accession)
            continue

        # 3. Parse the filing
        try:
            parsed = parse_8k_filing(raw_text)
            stats["parsed"] += 1
        except Exception:
            logger.exception("Failed to parse filing %s", accession)
            continue

        # 4. Skip boilerplate
        if parsed.get("is_boilerplate", False):
            stats["skipped_boilerplate"] += 1
            logger.debug("Skipping boilerplate filing %s", accession)
            continue

        # 5. Convert to Event
        event = _filing_to_event(parsed, file_url)

        # 6. Dedup via Redis
        if is_duplicate(event.content_hash):
            stats["skipped_dup"] += 1
            continue

        # 7. Change gate
        if not is_meaningful_change(event, recent_events):
            stats["skipped_dup"] += 1
            continue

        stats["new"] += 1

        # 8. Store in PostgreSQL
        try:
            await insert_event(event)
            stats["stored"] += 1
            recent_events.append(event)
        except Exception:
            logger.exception("Failed to store event for filing %s", accession)

    logger.info(
        "EDGAR poll complete: %d fetched, %d parsed, %d new, %d stored, %d skipped",
        stats["fetched"], stats["parsed"], stats["new"], stats["stored"],
        stats["skipped_dup"] + stats["skipped_boilerplate"],
    )
    return stats
