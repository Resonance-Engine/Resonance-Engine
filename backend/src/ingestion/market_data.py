"""Market data client — fetches historical price data for event labeling.

Supports Alpha Vantage (free tier: 25 req/day) and Finnhub (free tier: 60 req/min).
Used to label events with actual post-event returns for backtesting and calibration.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
FINNHUB_BASE = "https://finnhub.io/api/v1"


@dataclass
class PricePoint:
    """A single price data point."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class ReturnWindow:
    """Market return over a specific time window after an event."""

    window: str  # "1h", "4h", "24h", "1w"
    return_pct: float  # e.g., 0.032 for +3.2%
    pre_price: float  # Price before event
    post_price: float  # Price at end of window
    volatility: float  # Intraday high-low range as % of open


async def fetch_daily_prices(
    ticker: str,
    days: int = 30,
) -> list[PricePoint]:
    """Fetch daily OHLCV data from Alpha Vantage.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        days: Number of trading days to fetch.

    Returns:
        List of PricePoint objects, most recent first.
    """
    if not settings.alpha_vantage_api_key:
        logger.warning("No Alpha Vantage API key configured")
        return []

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact" if days <= 100 else "full",
        "apikey": settings.alpha_vantage_api_key,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(ALPHA_VANTAGE_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    time_series = data.get("Time Series (Daily)", {})
    if not time_series:
        logger.warning("No daily data returned for %s", ticker)
        return []

    prices = []
    for date_str, values in sorted(time_series.items(), reverse=True)[:days]:
        try:
            prices.append(PricePoint(
                timestamp=datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc),
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"]),
            ))
        except (ValueError, KeyError):
            continue

    return prices


async def fetch_intraday_prices(
    ticker: str,
    interval: str = "60min",
) -> list[PricePoint]:
    """Fetch intraday OHLCV data from Alpha Vantage.

    Args:
        ticker: Stock ticker symbol.
        interval: Time interval (1min, 5min, 15min, 30min, 60min).

    Returns:
        List of PricePoint objects, most recent first.
    """
    if not settings.alpha_vantage_api_key:
        logger.warning("No Alpha Vantage API key configured")
        return []

    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": interval,
        "outputsize": "compact",
        "apikey": settings.alpha_vantage_api_key,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(ALPHA_VANTAGE_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    series_key = f"Time Series ({interval})"
    time_series = data.get(series_key, {})
    if not time_series:
        logger.warning("No intraday data returned for %s", ticker)
        return []

    prices = []
    for dt_str, values in sorted(time_series.items(), reverse=True):
        try:
            prices.append(PricePoint(
                timestamp=datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                ),
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"]),
            ))
        except (ValueError, KeyError):
            continue

    return prices


async def fetch_quote_finnhub(ticker: str) -> dict | None:
    """Fetch current quote from Finnhub.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Dict with c (current), h (high), l (low), o (open), pc (previous close),
        or None if unavailable.
    """
    if not settings.finnhub_api_key:
        logger.warning("No Finnhub API key configured")
        return None

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{FINNHUB_BASE}/quote",
            params={"symbol": ticker, "token": settings.finnhub_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("c", 0) == 0:
        return None

    return data


async def compute_post_event_returns(
    ticker: str,
    event_timestamp: datetime,
    windows: list[str] | None = None,
) -> list[ReturnWindow]:
    """Compute actual market returns after an event for labeling.

    Fetches price data and computes returns over specified windows.
    Used for backtesting: did the signal's prediction match reality?

    Args:
        ticker: Stock ticker symbol.
        event_timestamp: When the event occurred.
        windows: Time windows to compute (default: ["1h", "4h", "24h", "1w"]).

    Returns:
        List of ReturnWindow objects for each successfully computed window.
    """
    if windows is None:
        windows = ["1h", "4h", "24h", "1w"]

    # Map window strings to timedeltas
    window_deltas = {
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "24h": timedelta(hours=24),
        "1w": timedelta(weeks=1),
    }

    # Fetch price data
    daily_prices = await fetch_daily_prices(ticker, days=10)
    if not daily_prices:
        return []

    # Find the closest price before the event
    pre_price = None
    for p in daily_prices:
        if p.timestamp <= event_timestamp:
            pre_price = p
            break

    if pre_price is None and daily_prices:
        pre_price = daily_prices[-1]  # Use oldest available

    if pre_price is None:
        return []

    results = []
    for window in windows:
        delta = window_deltas.get(window)
        if delta is None:
            continue

        target_time = event_timestamp + delta

        # Find closest price at/after the target time
        post_price = None
        for p in daily_prices:
            if p.timestamp >= target_time:
                post_price = p
            elif p.timestamp <= target_time:
                post_price = p
                break

        if post_price is None:
            continue

        return_pct = (post_price.close - pre_price.close) / pre_price.close
        volatility = (post_price.high - post_price.low) / post_price.open if post_price.open > 0 else 0.0

        results.append(ReturnWindow(
            window=window,
            return_pct=round(return_pct, 6),
            pre_price=pre_price.close,
            post_price=post_price.close,
            volatility=round(volatility, 6),
        ))

    return results
