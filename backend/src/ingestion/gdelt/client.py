"""GDELT DOC 2.0 API client — global news event detection.

Free API, no key required. Rate-limited to ~1 req/sec to be respectful.
Searches for financial news articles and returns structured results.

GDELT DOC 2.0 API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

# Rate limiting: 1 req/sec to be respectful (GDELT has no published limit)
_rate_semaphore = asyncio.Semaphore(1)
_MIN_REQUEST_INTERVAL = 1.0

_BASE_URL = settings.gdelt_base_url

# Financial keyword sets — each query is searched separately
FINANCIAL_QUERIES = [
    "earnings report SEC filing",
    "merger acquisition deal",
    "IPO stock offering",
    "CEO executive resignation appointment",
    "bankruptcy restructuring",
    "FDA drug approval",
    "stock buyback dividend",
]

_HEADERS = {
    "User-Agent": "Resonance Engine (financial research, team@resonance-engine.com)",
}


async def _throttled_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """HTTP GET with rate-limit throttling."""
    async with _rate_semaphore:
        resp = await client.get(url, **kwargs)
        await asyncio.sleep(_MIN_REQUEST_INTERVAL)
    resp.raise_for_status()
    return resp


async def search_articles(
    query: str,
    timespan: str = "15min",
    max_records: int = 25,
) -> list[dict]:
    """Search GDELT DOC 2.0 API for recent articles matching a query.

    Args:
        query: Search keywords (e.g., "earnings report SEC").
        timespan: How far back to search (e.g., "15min", "1h", "2d").
        max_records: Maximum articles to return (capped at 250 by GDELT).

    Returns:
        List of article dicts with keys: url, title, source_name,
        language, domain, timestamp, raw_text.
    """
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "timespan": timespan,
        "maxrecords": min(max_records, 250),
        "sort": "datedesc",
    }

    async with httpx.AsyncClient(headers=_HEADERS, timeout=30.0) as client:
        try:
            resp = await _throttled_get(client, f"{_BASE_URL}/doc/doc", params=params)
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("GDELT API error %s: %s", e.response.status_code, e)
            return []
        except (httpx.RequestError, Exception) as e:
            logger.warning("GDELT request failed: %s", e)
            return []

    articles = data.get("articles", [])
    results: list[dict] = []
    for article in articles:
        title = article.get("title", "").strip()
        url = article.get("url", "")
        if not title or not url:
            continue

        # Parse GDELT timestamp (YYYYMMDDTHHmmSSZ format)
        ts_str = article.get("seendate", "")
        try:
            ts = datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            ts = datetime.now(timezone.utc)

        results.append({
            "url": url,
            "title": title,
            "source_name": article.get("domain", "unknown"),
            "language": article.get("language", "English"),
            "domain": article.get("domain", ""),
            "timestamp": ts.isoformat(),
            "raw_text": title,
        })

    logger.info("GDELT search '%s' returned %d articles", query[:40], len(results))
    return results


async def search_financial_news(
    timespan: str = "30min",
    max_per_query: int = 15,
) -> list[dict]:
    """Search GDELT for recent financial news across all keyword categories.

    Runs each financial query sequentially (rate-limited) and deduplicates by URL.

    Args:
        timespan: How far back to search.
        max_per_query: Max articles per query (keeps total volume manageable).

    Returns:
        Deduplicated list of article dicts.
    """
    seen_urls: set[str] = set()
    all_articles: list[dict] = []

    for query in FINANCIAL_QUERIES:
        articles = await search_articles(query, timespan=timespan, max_records=max_per_query)
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                all_articles.append(article)

    logger.info(
        "GDELT financial scan: %d unique articles from %d queries",
        len(all_articles), len(FINANCIAL_QUERIES),
    )
    return all_articles
