"""NewsAPI ingestion — async polling used by the scheduler.

The scheduler calls fetch_top_headlines() directly via asyncio.
This module provides a sync wrapper for Celery compatibility if needed.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


def poll_headlines() -> dict:
    """Poll NewsAPI for recent financial headlines (sync wrapper)."""
    from src.ingestion.newsapi.client import fetch_top_headlines
    return asyncio.get_event_loop().run_until_complete(
        fetch_top_headlines(category="business", page_size=20)
    )
