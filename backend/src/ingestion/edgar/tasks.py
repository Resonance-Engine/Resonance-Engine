"""Celery tasks for EDGAR ingestion — scheduled polling + processing.

DEPRECATED as a runtime: the async scheduler (src/scheduler.py) replaced
Celery Beat (incompatible with Python 3.14). Kept only until Celery is
formally removed. Live code must import filing_to_event from
src.ingestion.edgar.events, NOT from this module.
"""

import asyncio
import logging
from datetime import date

from src.celery_app import app
from src.ingestion.change_gate import is_meaningful_change
from src.ingestion.deduplicator import is_duplicate
from src.ingestion.edgar.client import fetch_filing_document, fetch_recent_filings
from src.ingestion.edgar.events import filing_to_event
from src.ingestion.edgar.parser import parse_8k_filing

logger = logging.getLogger(__name__)

# Backward-compatible alias (previous private name)
_filing_to_event = filing_to_event


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
        event = filing_to_event(parsed, file_url)

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
