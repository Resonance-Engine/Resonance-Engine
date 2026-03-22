"""Celery tasks for NewsAPI ingestion (Phase 2)."""

from src.celery_app import app


@app.task(name="newsapi.poll_headlines")
def poll_headlines() -> dict:
    """Poll NewsAPI for recent financial headlines.

    TODO: Phase 2 — implement polling + normalize + dedup + store
    """
    raise NotImplementedError("NewsAPI polling task — Phase 2 deliverable")
