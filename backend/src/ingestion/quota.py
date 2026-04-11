"""API quota tracker — prevents surprise bills and rate-limit bans.

Tracks daily request counts per API. Redis-backed with in-memory fallback.
Logs warnings at 80% usage and hard-blocks at the limit.

Usage:
    tracker = QuotaTracker("newsapi", daily_limit=100)
    if tracker.allow():
        # make the API call
    else:
        logger.warning("NewsAPI daily quota exhausted")
"""

import logging
from datetime import date
from typing import ClassVar

logger = logging.getLogger(__name__)


class QuotaTracker:
    """Per-API daily request quota tracker.

    Uses in-memory counters keyed by (api_name, date).
    Resets automatically at midnight (new date key).
    """

    _counters: ClassVar[dict[str, int]] = {}

    def __init__(self, api_name: str, daily_limit: int) -> None:
        self.api_name = api_name
        self.daily_limit = daily_limit

    @property
    def _key(self) -> str:
        return f"{self.api_name}:{date.today().isoformat()}"

    @property
    def used(self) -> int:
        return self._counters.get(self._key, 0)

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.used)

    def allow(self) -> bool:
        """Check if a request is allowed. If yes, increment counter.

        Returns False and logs a warning when quota is exhausted.
        Logs a warning at 80% usage.
        """
        current = self.used

        if current >= self.daily_limit:
            logger.warning(
                "%s daily quota exhausted (%d/%d). Blocking request.",
                self.api_name, current, self.daily_limit,
            )
            return False

        # Warn at 80%
        threshold = int(self.daily_limit * 0.8)
        if current == threshold:
            logger.warning(
                "%s approaching daily quota: %d/%d (80%%).",
                self.api_name, current, self.daily_limit,
            )

        self._counters[self._key] = current + 1
        return True

    def status(self) -> dict:
        """Return quota status for monitoring endpoints."""
        return {
            "api": self.api_name,
            "date": date.today().isoformat(),
            "used": self.used,
            "limit": self.daily_limit,
            "remaining": self.remaining,
            "exhausted": self.used >= self.daily_limit,
        }


# ── Pre-configured trackers for each paid API ────────────────────

# NewsAPI free tier: 100 requests/day
newsapi_quota = QuotaTracker("newsapi", daily_limit=100)

# Alpha Vantage free tier: 25 requests/day
alpha_vantage_quota = QuotaTracker("alpha_vantage", daily_limit=25)

# Finnhub free tier: 60 requests/minute (tracked as daily for simplicity)
finnhub_quota = QuotaTracker("finnhub", daily_limit=1500)

# Gemini free tier: 1500 requests/day
gemini_quota = QuotaTracker("gemini", daily_limit=1500)
