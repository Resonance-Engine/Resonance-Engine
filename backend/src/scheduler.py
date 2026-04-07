"""Async scheduler — replaces Celery Beat for EDGAR polling.

Runs inside the FastAPI process using asyncio tasks. Polls SEC EDGAR
for new filings on a schedule and feeds them through the LangGraph pipeline.

Schedule (US Eastern, Mon–Fri market hours):
  - 8-K filings: every 5 minutes
  - 10-K filings: every 60 minutes
  - Form 4 (insider): every 10 minutes
"""

import asyncio
import logging
from datetime import datetime, timezone

import pytz

logger = logging.getLogger(__name__)

ET = pytz.timezone("US/Eastern")

# Schedule config: (form_type, interval_seconds, max_filings)
POLL_SCHEDULE = [
    ("8-K", 300, 100),   # every 5 min
    ("10-K", 3600, 50),  # every 60 min
    ("4", 600, 100),     # every 10 min
]

# Track running tasks so we can cancel on shutdown
_tasks: list[asyncio.Task] = []
_running = False


def _is_market_hours() -> bool:
    """Check if current time is within extended market hours (Mon–Fri 8–18 ET)."""
    now_et = datetime.now(ET)
    weekday = now_et.weekday()  # 0=Mon, 6=Sun
    hour = now_et.hour
    return weekday < 5 and 8 <= hour < 18


async def _poll_and_process(form_type: str, limit: int) -> dict:
    """Fetch recent filings from EDGAR and run each through the pipeline.

    Combines the EDGAR task logic with the LangGraph agent pipeline.
    Returns stats dict.
    """
    from src.ingestion.edgar.client import fetch_filing_document, fetch_recent_filings
    from src.ingestion.edgar.parser import parse_8k_filing
    from src.ingestion.edgar.tasks import _filing_to_event

    stats = {
        "fetched": 0, "parsed": 0, "new": 0,
        "pipeline_ok": 0, "pipeline_fail": 0,
        "skipped_dup": 0, "skipped_boilerplate": 0,
    }

    try:
        from datetime import date
        today = date.today().isoformat()
        filings = await fetch_recent_filings(
            form_type=form_type,
            start_date=today,
            end_date=today,
            limit=limit,
        )
        stats["fetched"] = len(filings)
    except Exception:
        logger.exception("Failed to fetch %s filings from EDGAR", form_type)
        return stats

    if not filings:
        return stats

    logger.info("Scheduler: fetched %d %s filings", len(filings), form_type)

    # Import dedup + change gate
    try:
        from src.ingestion.change_gate import is_meaningful_change
        from src.ingestion.deduplicator import is_duplicate
        has_dedup = True
    except Exception:
        has_dedup = False

    # Import pipeline
    from src.agents.pipeline import build_pipeline
    pipeline = build_pipeline()

    recent_events = []

    for filing in filings:
        accession = filing.get("accession_number", "")
        cik = filing.get("cik", "")
        file_url = filing.get("file_url", "")

        # Fetch full document
        try:
            raw_text = await fetch_filing_document(accession, cik)
        except Exception:
            logger.debug("Failed to fetch filing %s", accession)
            continue

        # Parse
        try:
            parsed = parse_8k_filing(raw_text)
            stats["parsed"] += 1
        except Exception:
            logger.debug("Failed to parse filing %s", accession)
            continue

        # Skip boilerplate
        if parsed.get("is_boilerplate", False):
            stats["skipped_boilerplate"] += 1
            continue

        # Build event for dedup check
        event = _filing_to_event(parsed, file_url)

        # Dedup
        if has_dedup:
            try:
                if is_duplicate(event.content_hash):
                    stats["skipped_dup"] += 1
                    continue
                if not is_meaningful_change(event, recent_events):
                    stats["skipped_dup"] += 1
                    continue
            except Exception:
                pass  # Redis down — skip dedup, process anyway

        stats["new"] += 1

        # Run through LangGraph pipeline (this embeds to Pinecone + stores signal)
        try:
            result = await pipeline.ainvoke({
                "raw_text": event.raw_text,
                "source": "SEC_EDGAR",
                "source_url": file_url,
            })
            confidence = result.get("confidence", 0)
            ticker = result.get("primary_ticker", "?")
            n_evidence = len(result.get("evidence", []))
            logger.info(
                "Scheduler: %s %s → confidence=%.2f%% evidence=%d",
                ticker, form_type, confidence * 100, n_evidence,
            )
            stats["pipeline_ok"] += 1
            recent_events.append(event)
        except Exception:
            logger.exception("Pipeline failed for filing %s", accession)
            stats["pipeline_fail"] += 1

    return stats


async def _polling_loop(form_type: str, interval: int, limit: int) -> None:
    """Run a single polling loop for a given form type."""
    logger.info("Scheduler: started %s polling loop (every %ds)", form_type, interval)

    while _running:
        try:
            if _is_market_hours():
                stats = await _poll_and_process(form_type, limit)
                logger.info(
                    "Scheduler [%s]: fetched=%d parsed=%d new=%d ok=%d fail=%d",
                    form_type, stats["fetched"], stats["parsed"],
                    stats["new"], stats["pipeline_ok"], stats["pipeline_fail"],
                )
            else:
                logger.debug("Scheduler [%s]: outside market hours, sleeping", form_type)
        except Exception:
            logger.exception("Scheduler [%s] loop error", form_type)

        # Sleep in small increments so shutdown is responsive
        for _ in range(interval):
            if not _running:
                break
            await asyncio.sleep(1)

    logger.info("Scheduler: %s polling loop stopped", form_type)


async def start_scheduler() -> None:
    """Start all polling loops as background asyncio tasks."""
    global _running
    if _running:
        logger.warning("Scheduler already running")
        return

    _running = True
    logger.info("Scheduler: starting EDGAR polling loops")

    for form_type, interval, limit in POLL_SCHEDULE:
        task = asyncio.create_task(
            _polling_loop(form_type, interval, limit),
            name=f"scheduler-{form_type}",
        )
        _tasks.append(task)

    logger.info("Scheduler: %d polling loops started", len(_tasks))


async def stop_scheduler() -> None:
    """Gracefully stop all polling loops."""
    global _running
    _running = False
    logger.info("Scheduler: stopping %d polling loops", len(_tasks))

    for task in _tasks:
        task.cancel()

    await asyncio.gather(*_tasks, return_exceptions=True)
    _tasks.clear()
    logger.info("Scheduler: all loops stopped")
