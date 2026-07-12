"""Market data client — fetches historical price data for event labeling.

Supports Alpha Vantage (free tier: 25 req/day) and Finnhub (free tier: 60 req/min).
Used to label events with actual post-event returns for backtesting and calibration.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from src.config import settings
from src.ingestion.quota import alpha_vantage_quota, finnhub_quota

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
FINNHUB_BASE = "https://finnhub.io/api/v1"

# Windows short enough that daily bars cannot measure them
_INTRADAY_WINDOWS = frozenset({"1h", "4h"})


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


async def _alpha_vantage_get(params: dict) -> dict | None:
    """Issue a quota-gated Alpha Vantage request with throttle detection.

    Alpha Vantage signals rate-limiting with an HTTP 200 body containing a
    "Note"/"Information" key instead of data — treating that as "no data"
    silently kills labeling, so it is detected and logged loudly here.

    Args:
        params: Query parameters (apikey is added here).

    Returns:
        Parsed JSON response, or None if the key is missing, the daily
        quota is exhausted, or the API returned a throttle/error body.
    """
    if not settings.alpha_vantage_api_key:
        logger.warning("No Alpha Vantage API key configured")
        return None

    if not alpha_vantage_quota.allow():
        # allow() already logged the exhaustion warning
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            ALPHA_VANTAGE_BASE,
            params={**params, "apikey": settings.alpha_vantage_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    for throttle_key in ("Note", "Information", "Error Message"):
        if throttle_key in data:
            logger.warning(
                "Alpha Vantage returned %r instead of data (rate-limited or bad request): %s",
                throttle_key, str(data[throttle_key])[:200],
            )
            return None

    return data


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
    data = await _alpha_vantage_get({
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact" if days <= 100 else "full",
    })
    if data is None:
        return []

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
    data = await _alpha_vantage_get({
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": interval,
        "outputsize": "compact",
    })
    if data is None:
        return []

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

    if not finnhub_quota.allow():
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


def _select_pre_price(
    prices_oldest_first: list[PricePoint],
    event_timestamp: datetime,
    daily: bool,
) -> PricePoint | None:
    """Select the last price known strictly BEFORE the event.

    Daily bars are stamped at 00:00 UTC of their trading date, but their
    close happens at the END of that day — using the event-day bar as the
    pre-event price is lookahead bias. For daily series, the pre-event bar
    is therefore the last bar from a PRIOR date.

    Args:
        prices_oldest_first: Price series sorted oldest → newest.
        event_timestamp: When the event occurred.
        daily: True when the series is daily bars.

    Returns:
        The pre-event PricePoint, or None if no bar precedes the event.
    """
    pre = None
    for p in prices_oldest_first:
        if daily:
            if p.timestamp.date() < event_timestamp.date():
                pre = p
            else:
                break
        else:
            if p.timestamp <= event_timestamp:
                pre = p
            else:
                break
    return pre


def _select_post_price(
    prices_oldest_first: list[PricePoint],
    target_time: datetime,
) -> PricePoint | None:
    """Select the first price at/after the window end (never before it).

    Args:
        prices_oldest_first: Price series sorted oldest → newest.
        target_time: End of the impact window.

    Returns:
        The first PricePoint with timestamp >= target_time, or None when the
        window hasn't elapsed within the available data.
    """
    for p in prices_oldest_first:
        if p.timestamp >= target_time:
            return p
    return None


def _compute_window_returns(
    prices: list[PricePoint],
    event_timestamp: datetime,
    windows: list[str],
    daily: bool,
) -> list[ReturnWindow]:
    """Compute returns for the given windows against one price series.

    Args:
        prices: Price series (any order; sorted internally).
        event_timestamp: When the event occurred.
        windows: Window names to compute (must be keys of the delta map).
        daily: True when the series is daily bars (affects pre-price rule).

    Returns:
        ReturnWindow objects for each window that could be measured.
    """
    window_deltas = {
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "24h": timedelta(hours=24),
        "1w": timedelta(weeks=1),
    }

    ordered = sorted(prices, key=lambda p: p.timestamp)
    pre_price = _select_pre_price(ordered, event_timestamp, daily=daily)
    if pre_price is None or pre_price.close <= 0:
        return []

    results = []
    for window in windows:
        delta = window_deltas.get(window)
        if delta is None:
            continue

        post_price = _select_post_price(ordered, event_timestamp + delta)
        if post_price is None:
            continue

        return_pct = (post_price.close - pre_price.close) / pre_price.close
        volatility = (
            (post_price.high - post_price.low) / post_price.open
            if post_price.open > 0 else 0.0
        )

        results.append(ReturnWindow(
            window=window,
            return_pct=round(return_pct, 6),
            pre_price=pre_price.close,
            post_price=post_price.close,
            volatility=round(volatility, 6),
        ))

    return results


async def compute_post_event_returns(
    ticker: str,
    event_timestamp: datetime,
    windows: list[str] | None = None,
) -> list[ReturnWindow]:
    """Compute actual market returns after an event for labeling.

    Fetches price data and computes returns over specified windows.
    Used for backtesting: did the signal's prediction match reality?

    Short windows (1h, 4h) are measured against 60-min intraday bars — daily
    bars cannot resolve them, and mapping them to next-day closes silently
    corrupts labels. If intraday data is unavailable for a short window, the
    window is skipped (left unlabeled) rather than mislabeled.

    Args:
        ticker: Stock ticker symbol.
        event_timestamp: When the event occurred.
        windows: Time windows to compute (default: ["1h", "4h", "24h", "1w"]).

    Returns:
        List of ReturnWindow objects for each successfully computed window.
    """
    if windows is None:
        windows = ["1h", "4h", "24h", "1w"]

    intraday_windows = [w for w in windows if w in _INTRADAY_WINDOWS]
    daily_windows = [w for w in windows if w not in _INTRADAY_WINDOWS]

    results: list[ReturnWindow] = []

    if intraday_windows:
        intraday_prices = await fetch_intraday_prices(ticker, interval="60min")
        if intraday_prices:
            results.extend(_compute_window_returns(
                intraday_prices, event_timestamp, intraday_windows, daily=False,
            ))
        else:
            logger.warning(
                "No intraday data for %s — skipping windows %s rather than "
                "mislabeling from daily bars", ticker, intraday_windows,
            )

    if daily_windows:
        daily_prices = await fetch_daily_prices(ticker, days=10)
        if daily_prices:
            results.extend(_compute_window_returns(
                daily_prices, event_timestamp, daily_windows, daily=True,
            ))

    return results
