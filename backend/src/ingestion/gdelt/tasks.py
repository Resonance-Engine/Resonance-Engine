"""Celery tasks for GDELT ingestion (Phase 2)."""

from src.celery_app import app


@app.task(name="gdelt.poll_articles")
def poll_articles() -> dict:
    """Poll GDELT for recent financial news articles.

    TODO: Phase 2 — implement polling + normalize + dedup + store
    """
    raise NotImplementedError("GDELT polling task — Phase 2 deliverable")
