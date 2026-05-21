"""GDELT ingestion — async polling used by the scheduler.

The scheduler calls search_financial_news() directly via asyncio.
This module provides a sync wrapper for Celery compatibility if needed.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


def poll_articles() -> dict:
    """Poll GDELT for recent financial news articles (sync wrapper)."""
    from src.ingestion.gdelt.client import search_financial_news
    return asyncio.get_event_loop().run_until_complete(
        search_financial_news(timespan="30min", max_per_query=10)
    )
