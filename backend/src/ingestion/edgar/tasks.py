"""Celery tasks for EDGAR ingestion — scheduled polling + processing."""

from src.celery_app import app


@app.task(name="edgar.poll_recent_filings")
def poll_recent_filings(form_type: str = "8-K", limit: int = 100) -> dict:
    """Poll EDGAR for recent filings, normalize, dedup, and store.

    Scheduled via Celery Beat (every 5 minutes during market hours).

    TODO: Call client.fetch_recent_filings()
    TODO: Parse each filing via parser module
    TODO: Normalize to Event via normalizer
    TODO: Dedup via deduplicator
    TODO: Gate via change_gate.is_meaningful_change()
    TODO: Store in PostgreSQL via event_repo
    """
    raise NotImplementedError("EDGAR polling task — Phase 0 deliverable")
