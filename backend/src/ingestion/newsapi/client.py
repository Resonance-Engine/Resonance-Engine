"""NewsAPI client — breaking financial news aggregation.

Free tier: 100 requests/day. Quota-tracked to prevent overages.
Rate-limited to ~1 req/sec. Fetches business headlines and financial news.

NewsAPI docs: https://newsapi.org/docs/endpoints
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from src.config import settings
from src.ingestion.quota import newsapi_quota

logger = logging.getLogger(__name__)

_BASE_URL = "https://newsapi.org/v2"

# Rate limiting: 1 req/sec
_rate_semaphore = asyncio.Semaphore(1)
_MIN_REQUEST_INTERVAL = 1.0

# Financial keywords for the /everything endpoint
FINANCIAL_KEYWORDS = [
    "earnings report",
    "SEC filing",
    "merger acquisition",
    "stock market IPO",
    "Federal Reserve interest rate",
    "quarterly revenue profit",
]


def _get_headers() -> dict[str, str]:
    """Build request headers with API key."""
    return {
        "X-Api-Key": settings.newsapi_key,
        "User-Agent": "Resonance Engine (financial research)",
    }


async def _throttled_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """HTTP GET with rate-limit throttling and quota check."""
    if not newsapi_quota.allow():
        raise RuntimeError(
            f"NewsAPI daily quota exhausted ({newsapi_quota.used}/{newsapi_quota.daily_limit})"
        )

    async with _rate_semaphore:
        resp = await client.get(url, **kwargs)
        await asyncio.sleep(_MIN_REQUEST_INTERVAL)
    resp.raise_for_status()
    return resp


async def fetch_top_headlines(
    category: str = "business",
    country: str = "us",
    page_size: int = 20,
) -> list[dict]:
    """Fetch top headlines from NewsAPI.

    Args:
        category: News category (business, technology, science, health).
        country: 2-letter country code.
        page_size: Number of articles (max 100).

    Returns:
        List of article dicts with keys: url, title, description,
        source_name, timestamp, raw_text.
    """
    if not settings.newsapi_key:
        logger.warning("NewsAPI key not configured — skipping")
        return []

    params = {
        "category": category,
        "country": country,
        "pageSize": min(page_size, 100),
    }

    async with httpx.AsyncClient(headers=_get_headers(), timeout=30.0) as client:
        try:
            resp = await _throttled_get(client, f"{_BASE_URL}/top-headlines", params=params)
            data = resp.json()
        except RuntimeError as e:
            logger.warning("NewsAPI quota block: %s", e)
            return []
        except httpx.HTTPStatusError as e:
            logger.warning("NewsAPI error %s: %s", e.response.status_code, e)
            return []
        except (httpx.RequestError, Exception) as e:
            logger.warning("NewsAPI request failed: %s", e)
            return []

    if data.get("status") != "ok":
        logger.warning("NewsAPI returned status=%s: %s", data.get("status"), data.get("message"))
        return []

    return _parse_articles(data.get("articles", []))


async def search_financial_news(
    query: str | None = None,
    page_size: int = 20,
    sort_by: str = "publishedAt",
) -> list[dict]:
    """Search NewsAPI /everything endpoint for financial news.

    Args:
        query: Search keywords (uses default financial keywords if None).
        page_size: Number of articles (max 100).
        sort_by: Sort order (publishedAt, relevancy, popularity).

    Returns:
        List of article dicts.
    """
    if not settings.newsapi_key:
        logger.warning("NewsAPI key not configured — skipping")
        return []

    if query is None:
        query = " OR ".join(f'"{kw}"' for kw in FINANCIAL_KEYWORDS[:3])

    params = {
        "q": query,
        "language": "en",
        "sortBy": sort_by,
        "pageSize": min(page_size, 100),
    }

    async with httpx.AsyncClient(headers=_get_headers(), timeout=30.0) as client:
        try:
            resp = await _throttled_get(client, f"{_BASE_URL}/everything", params=params)
            data = resp.json()
        except RuntimeError as e:
            logger.warning("NewsAPI quota block: %s", e)
            return []
        except httpx.HTTPStatusError as e:
            logger.warning("NewsAPI error %s: %s", e.response.status_code, e)
            return []
        except (httpx.RequestError, Exception) as e:
            logger.warning("NewsAPI request failed: %s", e)
            return []

    if data.get("status") != "ok":
        logger.warning("NewsAPI returned status=%s: %s", data.get("status"), data.get("message"))
        return []

    return _parse_articles(data.get("articles", []))


def _parse_articles(articles: list[dict]) -> list[dict]:
    """Normalize NewsAPI article objects into our standard format."""
    results: list[dict] = []
    for article in articles:
        title = (article.get("title") or "").strip()
        description = (article.get("description") or "").strip()
        url = article.get("url", "")
        if not title or not url:
            continue

        # Parse timestamp
        ts_str = article.get("publishedAt", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            ts = datetime.now(timezone.utc)

        # Combine title + description for richer text
        raw_text = f"{title}. {description}" if description else title

        results.append({
            "url": url,
            "title": title,
            "description": description,
            "source_name": article.get("source", {}).get("name", "unknown"),
            "author": article.get("author"),
            "timestamp": ts.isoformat(),
            "raw_text": raw_text,
        })

    logger.info("NewsAPI: parsed %d articles", len(results))
    return results
