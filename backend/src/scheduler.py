"""Async scheduler — EDGAR, GDELT, NewsAPI polling + feedback loop.

Runs inside the FastAPI process using asyncio tasks. Polls data sources
on a schedule and feeds articles/filings through the LangGraph pipeline.
Also runs a feedback loop that labels expired signals with actual market
moves for downstream evaluation/calibration.

Schedule (US Eastern, Mon–Fri market hours):
  EDGAR:
  - 8-K filings: every 5 minutes
  - 10-K filings: every 60 minutes
  - Form 4 (insider): every 10 minutes
  News:
  - GDELT: every 15 minutes (free, no key)
  - NewsAPI: every 30 minutes (100 req/day quota-tracked)
  Feedback:
  - Label expired signals: every 30 minutes (Alpha Vantage 25 req/day quota)
"""

import asyncio
import logging
from datetime import datetime, timezone

import pytz

logger = logging.getLogger(__name__)

ET = pytz.timezone("US/Eastern")

# EDGAR schedule: (form_type, interval_seconds, max_filings)
EDGAR_SCHEDULE = [
    ("8-K", 300, 100),   # every 5 min
    ("10-K", 3600, 50),  # every 60 min
    ("4", 600, 100),     # every 10 min
]

# News schedule: (source, interval_seconds)
NEWS_SCHEDULE = [
    ("GDELT", 900),      # every 15 min
    ("NEWSAPI", 1800),   # every 30 min
]

# Feedback loop interval (seconds) — labels expired signals with actual_move
FEEDBACK_INTERVAL = 1800  # every 30 min
# Max signals labeled per run. Each label costs one Alpha Vantage request
# (25/day free tier) — the quota tracker hard-blocks at the limit, this
# just keeps a single run from consuming the whole daily budget.
FEEDBACK_BATCH = 10

# Track running tasks so we can cancel on shutdown
_tasks: list[asyncio.Task] = []
_running = False

# Recently processed events per EDGAR form type, persisted ACROSS poll
# cycles so the change gate's story clustering (2h window) can actually
# fire — a per-cycle list on a 5-minute loop could never span the window.
_recent_events_by_form: dict[str, list] = {}


def _remember_recent_event(form_type: str, event) -> None:
    """Track a processed event for cross-cycle story clustering.

    Prunes entries older than the change gate's cluster window.
    """
    from src.ingestion.change_gate import CLUSTER_WINDOW

    events = _recent_events_by_form.setdefault(form_type, [])
    events.append(event)

    now = datetime.now(timezone.utc)
    _recent_events_by_form[form_type] = [
        e for e in events
        if e.timestamp is not None
        and (now - e.timestamp).total_seconds() < CLUSTER_WINDOW.total_seconds()
    ]


def _is_market_hours() -> bool:
    """Check if current time is within extended market hours (Mon–Fri 8–18 ET)."""
    now_et = datetime.now(ET)
    weekday = now_et.weekday()  # 0=Mon, 6=Sun
    hour = now_et.hour
    return weekday < 5 and 8 <= hour < 18


# ── EDGAR Polling ─────────────────────────────────────────────

async def _poll_edgar(form_type: str, limit: int) -> dict:
    """Fetch recent filings from EDGAR and run each through the pipeline."""
    from src.ingestion.edgar.client import fetch_filing_document, fetch_recent_filings
    from src.ingestion.edgar.events import filing_to_event
    from src.ingestion.edgar.parser import parse_8k_filing

    stats = {
        "fetched": 0, "parsed": 0, "new": 0,
        "pipeline_ok": 0, "pipeline_fail": 0,
        "skipped_dup": 0, "skipped_boilerplate": 0,
    }

    try:
        from datetime import date
        today = date.today().isoformat()
        filings = await fetch_recent_filings(
            form_type=form_type, start_date=today, end_date=today, limit=limit,
        )
        stats["fetched"] = len(filings)
    except Exception:
        logger.exception("Failed to fetch %s filings from EDGAR", form_type)
        return stats

    if not filings:
        return stats

    logger.info("Scheduler: fetched %d %s filings", len(filings), form_type)

    try:
        from src.ingestion.change_gate import is_meaningful_change
        from src.ingestion.deduplicator import claim, release
        has_dedup = True
    except Exception:
        logger.warning("Dedup/change-gate unavailable — duplicates will not be filtered")
        has_dedup = False

    from src.agents.pipeline import build_pipeline
    pipeline = build_pipeline()
    # Cross-cycle memory so the 2h clustering window actually spans cycles
    recent_events = _recent_events_by_form.get(form_type, [])

    for filing in filings:
        accession = filing.get("accession_number", "")
        cik = filing.get("cik", "")
        file_url = filing.get("file_url", "")

        try:
            raw_text = await fetch_filing_document(accession, cik)
        except Exception:
            logger.debug("Failed to fetch filing %s", accession)
            continue

        try:
            parsed = parse_8k_filing(raw_text)
            stats["parsed"] += 1
        except Exception:
            logger.debug("Failed to parse filing %s", accession)
            continue

        if parsed.get("is_boilerplate", False):
            stats["skipped_boilerplate"] += 1
            continue

        event = filing_to_event(parsed, file_url)

        claimed = False
        if has_dedup:
            try:
                # Atomically claim the hash; released below if the pipeline fails
                if not claim(event.content_hash):
                    stats["skipped_dup"] += 1
                    continue
                claimed = True
                if not is_meaningful_change(event, recent_events):
                    stats["skipped_dup"] += 1
                    continue
            except Exception:
                logger.warning(
                    "Dedup check failed for filing %s — processing anyway", accession,
                )

        stats["new"] += 1

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
            _remember_recent_event(form_type, event)
        except Exception:
            logger.exception("Pipeline failed for filing %s", accession)
            stats["pipeline_fail"] += 1
            if claimed:
                # Release the claim so a later poll can retry this filing
                try:
                    release(event.content_hash)
                except Exception:
                    logger.debug("Failed to release dedup claim for %s", accession)

    return stats


# ── News Polling (GDELT + NewsAPI) ────────────────────────────

async def _poll_news(source: str) -> dict:
    """Fetch recent news articles and run each through the pipeline.

    Args:
        source: "GDELT" or "NEWSAPI"

    Returns:
        Stats dict with fetched/new/pipeline_ok/pipeline_fail/skipped_dup counts.
    """
    stats = {
        "fetched": 0, "new": 0,
        "pipeline_ok": 0, "pipeline_fail": 0,
        "skipped_dup": 0,
    }

    # Fetch articles from the appropriate source
    articles: list[dict] = []
    try:
        if source == "GDELT":
            from src.ingestion.gdelt.client import search_financial_news as gdelt_search
            articles = await gdelt_search(timespan="30min", max_per_query=10)
        elif source == "NEWSAPI":
            from src.ingestion.newsapi.client import fetch_top_headlines
            articles = await fetch_top_headlines(category="business", page_size=20)
        stats["fetched"] = len(articles)
    except Exception:
        logger.exception("Failed to fetch from %s", source)
        return stats

    if not articles:
        return stats

    logger.info("Scheduler: fetched %d articles from %s", len(articles), source)

    # Dedup check
    try:
        from src.ingestion.deduplicator import claim, release
        has_dedup = True
    except Exception:
        logger.warning("Dedup unavailable — duplicate articles will not be filtered")
        has_dedup = False

    from src.agents.pipeline import build_pipeline
    pipeline = build_pipeline()

    for article in articles:
        raw_text = article.get("raw_text", "")
        url = article.get("url", "")
        if not raw_text or len(raw_text) < 20:
            continue

        # Dedup by content hash — claimed atomically, released on failure
        content_hash = ""
        claimed = False
        if has_dedup:
            try:
                from src.ingestion.normalizer import generate_content_hash
                content_hash = generate_content_hash(source, url, raw_text)
                if not claim(content_hash):
                    stats["skipped_dup"] += 1
                    continue
                claimed = True
            except Exception:
                logger.warning(
                    "Dedup check failed for %s article — processing anyway", source,
                )

        stats["new"] += 1

        try:
            result = await pipeline.ainvoke({
                "raw_text": raw_text,
                "source": source,
                "source_url": url,
            })
            confidence = result.get("confidence", 0)
            ticker = result.get("primary_ticker", "?")
            rejected = result.get("rejected", False)
            if not rejected:
                logger.info(
                    "Scheduler [%s]: %s → confidence=%.2f%% ticker=%s",
                    source, article.get("title", "")[:50], confidence * 100, ticker,
                )
            stats["pipeline_ok"] += 1
        except Exception:
            logger.exception("Pipeline failed for %s article: %s", source, url[:80])
            stats["pipeline_fail"] += 1
            if claimed and content_hash:
                # Release the claim so a later poll can retry this article
                try:
                    release(content_hash)
                except Exception:
                    logger.debug("Failed to release dedup claim for %s", url[:80])

    return stats


# ── Polling Loops ─────────────────────────────────────────────

async def _edgar_loop(form_type: str, interval: int, limit: int) -> None:
    """Run a single EDGAR polling loop."""
    logger.info("Scheduler: started EDGAR %s loop (every %ds)", form_type, interval)

    while _running:
        try:
            if _is_market_hours():
                stats = await _poll_edgar(form_type, limit)
                logger.info(
                    "Scheduler [EDGAR %s]: fetched=%d parsed=%d new=%d ok=%d fail=%d",
                    form_type, stats["fetched"], stats["parsed"],
                    stats["new"], stats["pipeline_ok"], stats["pipeline_fail"],
                )
            else:
                logger.debug("Scheduler [EDGAR %s]: outside market hours", form_type)
        except Exception:
            logger.exception("Scheduler [EDGAR %s] loop error", form_type)

        for _ in range(interval):
            if not _running:
                break
            await asyncio.sleep(1)

    logger.info("Scheduler: EDGAR %s loop stopped", form_type)


async def _news_loop(source: str, interval: int) -> None:
    """Run a single news polling loop (GDELT or NewsAPI)."""
    logger.info("Scheduler: started %s loop (every %ds)", source, interval)

    while _running:
        try:
            if _is_market_hours():
                stats = await _poll_news(source)
                logger.info(
                    "Scheduler [%s]: fetched=%d new=%d ok=%d fail=%d skipped=%d",
                    source, stats["fetched"], stats["new"],
                    stats["pipeline_ok"], stats["pipeline_fail"], stats["skipped_dup"],
                )
            else:
                logger.debug("Scheduler [%s]: outside market hours", source)
        except Exception:
            logger.exception("Scheduler [%s] loop error", source)

        for _ in range(interval):
            if not _running:
                break
            await asyncio.sleep(1)

    logger.info("Scheduler: %s loop stopped", source)


async def _feedback_loop(interval: int, batch_size: int) -> None:
    """Run the feedback loop — label expired signals with actual market moves."""
    from src.ingestion.feedback_loop import label_expired_signals

    logger.info("Scheduler: started feedback loop (every %ds)", interval)

    while _running:
        try:
            if _is_market_hours():
                stats = await label_expired_signals(batch_size=batch_size)
                if stats["scanned"] > 0:
                    logger.info(
                        "Scheduler [feedback]: scanned=%d labeled=%d no_data=%d errors=%d",
                        stats["scanned"], stats["labeled"],
                        stats["no_data"], stats["errors"],
                    )
            else:
                logger.debug("Scheduler [feedback]: outside market hours")
        except Exception:
            logger.exception("Scheduler [feedback] loop error")

        for _ in range(interval):
            if not _running:
                break
            await asyncio.sleep(1)

    logger.info("Scheduler: feedback loop stopped")


# ── Start / Stop ──────────────────────────────────────────────

async def start_scheduler() -> None:
    """Start all polling loops as background asyncio tasks."""
    global _running
    if _running:
        logger.warning("Scheduler already running")
        return

    _running = True

    # EDGAR polling loops
    for form_type, interval, limit in EDGAR_SCHEDULE:
        task = asyncio.create_task(
            _edgar_loop(form_type, interval, limit),
            name=f"scheduler-edgar-{form_type}",
        )
        _tasks.append(task)

    # News polling loops
    for source, interval in NEWS_SCHEDULE:
        task = asyncio.create_task(
            _news_loop(source, interval),
            name=f"scheduler-news-{source.lower()}",
        )
        _tasks.append(task)

    # Feedback loop — labels expired signals with actual market moves
    feedback_task = asyncio.create_task(
        _feedback_loop(FEEDBACK_INTERVAL, FEEDBACK_BATCH),
        name="scheduler-feedback",
    )
    _tasks.append(feedback_task)

    logger.info(
        "Scheduler: %d loops started (EDGAR: %d, News: %d, Feedback: 1)",
        len(_tasks), len(EDGAR_SCHEDULE), len(NEWS_SCHEDULE),
    )


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
