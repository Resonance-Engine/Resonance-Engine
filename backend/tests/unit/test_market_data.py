"""Tests for market data client — window returns, quota gating, throttle detection.

Regression coverage for three labeling bugs:
1. Intraday windows (1h/4h) were computed from daily bars → labels measured
   over ~a day instead of the stated window.
2. Post-price selection returned the bar BEFORE the window end.
3. Pre-price used the event day's own daily bar (whose close is after the
   event) — lookahead bias.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

import src.ingestion.market_data as md
from src.ingestion.market_data import (
    PricePoint,
    _compute_window_returns,
    _select_post_price,
    _select_pre_price,
    compute_post_event_returns,
)
from src.ingestion.quota import QuotaTracker


def _bar(ts: datetime, close: float, open_: float | None = None) -> PricePoint:
    o = open_ if open_ is not None else close
    return PricePoint(
        timestamp=ts, open=o, high=max(o, close) * 1.01,
        low=min(o, close) * 0.99, close=close, volume=1000,
    )


def _daily_bar(day: str, close: float) -> PricePoint:
    ts = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return _bar(ts, close)


EVENT_TS = datetime(2026, 7, 8, 14, 30, tzinfo=timezone.utc)


# --- Pre/post price selection ---


def test_pre_price_daily_excludes_event_day_bar():
    """Regression: the event day's daily close happens AFTER the event —
    using it as the pre-event price is lookahead bias."""
    bars = [
        _daily_bar("2026-07-06", 100.0),
        _daily_bar("2026-07-07", 102.0),
        _daily_bar("2026-07-08", 110.0),  # event day — close is post-event
    ]
    pre = _select_pre_price(bars, EVENT_TS, daily=True)
    assert pre is not None
    assert pre.close == 102.0


def test_pre_price_intraday_uses_last_bar_at_or_before_event():
    bars = [
        _bar(EVENT_TS - timedelta(hours=2), 100.0),
        _bar(EVENT_TS - timedelta(hours=1), 101.0),
        _bar(EVENT_TS + timedelta(hours=1), 105.0),
    ]
    pre = _select_pre_price(bars, EVENT_TS, daily=False)
    assert pre is not None
    assert pre.close == 101.0


def test_pre_price_none_when_no_prior_bar():
    bars = [_bar(EVENT_TS + timedelta(hours=1), 105.0)]
    assert _select_pre_price(bars, EVENT_TS, daily=False) is None


def test_post_price_first_bar_at_or_after_target():
    """Regression: the old loop returned the bar BEFORE the target."""
    target = EVENT_TS + timedelta(hours=4)
    bars = [
        _bar(EVENT_TS + timedelta(hours=1), 101.0),
        _bar(EVENT_TS + timedelta(hours=3), 102.0),  # before target — must NOT win
        _bar(EVENT_TS + timedelta(hours=5), 104.0),  # first at/after target
        _bar(EVENT_TS + timedelta(hours=7), 108.0),
    ]
    post = _select_post_price(bars, target)
    assert post is not None
    assert post.close == 104.0


def test_post_price_none_when_window_not_elapsed():
    bars = [_bar(EVENT_TS + timedelta(hours=1), 101.0)]
    assert _select_post_price(bars, EVENT_TS + timedelta(hours=4)) is None


# --- Window return computation ---


def test_window_return_computed_from_correct_bars():
    bars = [
        _bar(EVENT_TS - timedelta(hours=1), 100.0),
        _bar(EVENT_TS + timedelta(hours=2), 103.0),
        _bar(EVENT_TS + timedelta(hours=5), 104.0),
    ]
    results = _compute_window_returns(bars, EVENT_TS, ["4h"], daily=False)
    assert len(results) == 1
    assert results[0].window == "4h"
    assert results[0].pre_price == 100.0
    assert results[0].post_price == 104.0
    assert results[0].return_pct == pytest.approx(0.04)


def test_unelapsed_window_is_skipped_not_mislabeled():
    bars = [
        _bar(EVENT_TS - timedelta(hours=1), 100.0),
        _bar(EVENT_TS + timedelta(hours=2), 103.0),
    ]
    results = _compute_window_returns(bars, EVENT_TS, ["1h", "24h"], daily=False)
    assert [r.window for r in results] == ["1h"]


# --- compute_post_event_returns routing ---


async def test_intraday_windows_use_intraday_series(monkeypatch):
    """Regression: 1h/4h must never be measured against daily bars."""
    intraday = [
        _bar(EVENT_TS - timedelta(hours=1), 100.0),
        _bar(EVENT_TS + timedelta(hours=2), 102.0),
    ]
    intraday_mock = AsyncMock(return_value=intraday)
    daily_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(md, "fetch_intraday_prices", intraday_mock)
    monkeypatch.setattr(md, "fetch_daily_prices", daily_mock)

    results = await compute_post_event_returns("AAPL", EVENT_TS, windows=["1h"])

    intraday_mock.assert_awaited_once()
    daily_mock.assert_not_awaited()
    assert len(results) == 1
    assert results[0].return_pct == pytest.approx(0.02)


async def test_intraday_unavailable_skips_short_window(monkeypatch):
    """No intraday data → 1h/4h left unlabeled, NOT computed from daily bars."""
    monkeypatch.setattr(md, "fetch_intraday_prices", AsyncMock(return_value=[]))
    daily_mock = AsyncMock(return_value=[
        _daily_bar("2026-07-07", 100.0),
        _daily_bar("2026-07-09", 105.0),
    ])
    monkeypatch.setattr(md, "fetch_daily_prices", daily_mock)

    results = await compute_post_event_returns("AAPL", EVENT_TS, windows=["4h"])
    assert results == []
    daily_mock.assert_not_awaited()


async def test_daily_windows_use_daily_series(monkeypatch):
    intraday_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(md, "fetch_intraday_prices", intraday_mock)
    monkeypatch.setattr(md, "fetch_daily_prices", AsyncMock(return_value=[
        _daily_bar("2026-07-07", 100.0),
        _daily_bar("2026-07-08", 101.0),
        _daily_bar("2026-07-10", 106.0),
    ]))

    results = await compute_post_event_returns("AAPL", EVENT_TS, windows=["24h"])

    intraday_mock.assert_not_awaited()
    assert len(results) == 1
    # pre = 07-07 close (prior date), post = 07-10 (first bar >= event+24h)
    assert results[0].pre_price == 100.0
    assert results[0].post_price == 106.0
    assert results[0].return_pct == pytest.approx(0.06)


# --- Alpha Vantage quota + throttle handling ---


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str, params: dict | None = None) -> _FakeResponse:
        return _FakeResponse(self._payload)


@pytest.fixture
def fresh_quota(monkeypatch):
    """Isolated AV quota so tests don't share global counter state."""
    tracker = QuotaTracker("alpha_vantage_test", daily_limit=25)
    tracker._counters = {}
    monkeypatch.setattr(md, "alpha_vantage_quota", tracker)
    monkeypatch.setattr(md.settings, "alpha_vantage_api_key", "test-key")
    return tracker


async def test_av_throttle_note_detected_as_failure(monkeypatch, fresh_quota):
    """Regression: AV returns HTTP 200 with a "Note" body when throttled —
    it must be treated as a failure, not as an empty time series."""
    monkeypatch.setattr(
        md.httpx, "AsyncClient",
        lambda **kw: _FakeClient({"Note": "API call frequency exceeded"}),
    )
    assert await md.fetch_daily_prices("AAPL") == []


async def test_av_information_body_detected(monkeypatch, fresh_quota):
    monkeypatch.setattr(
        md.httpx, "AsyncClient",
        lambda **kw: _FakeClient({"Information": "rate limit"}),
    )
    assert await md.fetch_intraday_prices("AAPL") == []


async def test_av_quota_blocks_request(monkeypatch, fresh_quota):
    """Once the daily quota is exhausted, no HTTP request is made."""
    calls = []

    def make_client(**kw):
        calls.append(1)
        return _FakeClient({"Time Series (Daily)": {}})

    monkeypatch.setattr(md.httpx, "AsyncClient", make_client)
    for _ in range(25):
        fresh_quota.allow()

    assert await md.fetch_daily_prices("AAPL") == []
    assert calls == []


async def test_av_quota_incremented_per_request(monkeypatch, fresh_quota):
    monkeypatch.setattr(
        md.httpx, "AsyncClient",
        lambda **kw: _FakeClient({"Time Series (Daily)": {}}),
    )
    await md.fetch_daily_prices("AAPL")
    assert fresh_quota.used == 1
