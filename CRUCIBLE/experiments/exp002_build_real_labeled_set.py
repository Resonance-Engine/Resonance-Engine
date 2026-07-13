"""exp002 — Build a REAL labeled 8-K event set (replaces the fabricated one).

Finding 001 killed backend/data/labeled_test_set.json (labels were invented).
This script builds the honest replacement from two free sources:

  1. SEC EDGAR submissions API (data.sec.gov/submissions/CIK##########.json)
     — every 8-K a company filed: filing date, acceptance timestamp, item codes.
     One request per company; no document fetches needed for labeling.
  2. Yahoo Finance daily closes (cached in CRUCIBLE/data/yahoo/ by exp001)
     — real market outcomes, including SPY for market-adjusted (abnormal) returns.

Event-day logic: EDGAR acceptanceDateTime is US-Eastern wall time (the trailing
"Z" in the API is a known quirk — values like T16:05 cluster around the 4pm
close, impossible in UTC). Filings accepted after 16:00 ET can only be traded
on the NEXT session, so their event day is the next trading day.

Labels per event (close-to-close, %):
  ret_1d  — event trading day close vs prior close
  ret_5d  — +5 trading days close vs prior close
  abn_1d / abn_5d — same minus SPY over the identical window
  direction — positive / negative / neutral on abn_1d with a ±1.0% band

Output: CRUCIBLE/data/real_labeled_8k_set.json
Cost ceiling: $0 (EDGAR free at ≤10 req/s; Yahoo free, cached).
Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CRUCIBLE" / "experiments"))
from exp001_verify_labels import fetch_history  # reuse the cached Yahoo loader

DATA = ROOT / "CRUCIBLE" / "data"
OUT = DATA / "real_labeled_8k_set.json"
SUBMISSIONS_CACHE = DATA / "edgar_submissions"

UA = {"User-Agent": "Resonance Engine research saify2001@icloud.com"}
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"

NEUTRAL_BAND = 1.0  # |abn_1d| below this → neutral
AFTER_HOURS_CUTOFF = 16  # ET hour; acceptance >= 16:00 trades next session

# The 47 tickers from the (dead) synthetic set, kept for continuity — all
# large-cap and liquid, so daily closes are clean.
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "UNH", "HD", "MA", "DIS", "BAC", "XOM", "PFE", "KO",
    "CSCO", "INTC", "AMD", "CRM", "NFLX", "ADBE", "QCOM", "TXN", "ORCL", "IBM",
    "GE", "BA", "CAT", "MMM", "GS", "MS", "C", "WFC", "T", "VZ",
    "UBER", "SNAP", "SBUX", "NKE", "MRNA", "ABBV", "AVGO", "BRK-B",
]


def _get_json(url: str, cache_path: Path) -> dict:
    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as resp:
            cache_path.write_bytes(resp.read())
        time.sleep(0.15)  # stay far under EDGAR's 10 req/s
    return json.loads(cache_path.read_text())


def load_ticker_cik_map() -> dict[str, int]:
    raw = _get_json(TICKERS_URL, SUBMISSIONS_CACHE / "company_tickers.json")
    return {row["ticker"].upper(): row["cik_str"] for row in raw.values()}


def eightk_filings(cik: int) -> list[dict]:
    """All 8-K filings (excluding amendments) from a company's recent history."""
    sub = _get_json(SUBMISSIONS_URL.format(cik=cik), SUBMISSIONS_CACHE / f"{cik}.json")
    recent = sub["filings"]["recent"]
    out = []
    for form, filed, accepted, accession, items in zip(
        recent["form"],
        recent["filingDate"],
        recent["acceptanceDateTime"],
        recent["accessionNumber"],
        recent["items"],
    ):
        if form != "8-K":
            continue
        out.append(
            {
                "filed": filed,
                "accepted": accepted,
                "accession": accession,
                "items": [i.strip() for i in items.split(",") if i.strip()],
            }
        )
    return out


def event_trading_day(closes: dict[date, float], filing: dict) -> date | None:
    """First session on which the filing was tradeable."""
    accepted = datetime.fromisoformat(filing["accepted"].replace("Z", ""))
    d = accepted.date()
    if accepted.hour >= AFTER_HOURS_CUTOFF:
        d += timedelta(days=1)
    onward = [day for day in sorted(closes) if day >= d]
    return onward[0] if onward else None


def window_return(closes: dict[date, float], event_day: date, horizon: int) -> float | None:
    """% return from the close before event_day to `horizon` sessions after it."""
    days = sorted(closes)
    if event_day not in closes:
        return None
    idx = days.index(event_day)
    if idx == 0 or idx + horizon - 1 >= len(days):
        return None
    pre = closes[days[idx - 1]]
    post = closes[days[idx + horizon - 1]]
    return (post - pre) / pre * 100.0


def main() -> None:
    cik_map = load_ticker_cik_map()
    spy = fetch_history("SPY")
    events, skipped = [], 0

    for ticker in TICKERS:
        cik = cik_map.get(ticker.replace("-", ""))
        if cik is None:
            print(f"  !! no CIK for {ticker}", file=sys.stderr)
            continue
        closes = fetch_history(ticker)
        if not closes:
            print(f"  !! no price data for {ticker}", file=sys.stderr)
            continue
        for f in eightk_filings(cik):
            ev_day = event_trading_day(closes, f)
            if ev_day is None:
                skipped += 1
                continue
            ret_1d = window_return(closes, ev_day, 1)
            ret_5d = window_return(closes, ev_day, 5)
            if ret_1d is None:
                skipped += 1
                continue
            spy_day = ev_day if ev_day in spy else None
            abn_1d = ret_1d - window_return(spy, ev_day, 1) if spy_day else None
            abn_5d = (
                ret_5d - window_return(spy, ev_day, 5)
                if spy_day and ret_5d is not None and window_return(spy, ev_day, 5) is not None
                else None
            )
            basis = abn_1d if abn_1d is not None else ret_1d
            direction = (
                "neutral"
                if abs(basis) < NEUTRAL_BAND
                else "positive" if basis > 0 else "negative"
            )
            events.append(
                {
                    "ticker": ticker,
                    "cik": cik,
                    "accession": f["accession"],
                    "filed": f["filed"],
                    "accepted": f["accepted"],
                    "items": f["items"],
                    "event_trading_day": ev_day.isoformat(),
                    "ret_1d": round(ret_1d, 3),
                    "ret_5d": round(ret_5d, 3) if ret_5d is not None else None,
                    "abn_1d": round(abn_1d, 3) if abn_1d is not None else None,
                    "abn_5d": round(abn_5d, 3) if abn_5d is not None else None,
                    "direction": direction,
                }
            )

    meta = {
        "version": "1.0",
        "created": date.today().isoformat(),
        "generator": "CRUCIBLE/experiments/exp002_build_real_labeled_set.py",
        "sources": {
            "filings": "SEC EDGAR submissions API (item codes + acceptance timestamps)",
            "prices": "Yahoo Finance daily closes; SPY used for abnormal returns",
        },
        "label_semantics": {
            "ret_1d": "close-to-close % return over the first tradeable session",
            "abn_1d": "ret_1d minus SPY same-window return",
            "direction": f"sign of abn_1d with ±{NEUTRAL_BAND}% neutral band",
            "after_hours_rule": f"acceptance >= {AFTER_HOURS_CUTOFF}:00 ET → next session",
        },
        "n_events": len(events),
        "n_skipped_no_price_window": skipped,
    }
    OUT.write_text(json.dumps({"_meta": meta, "events": events}, indent=1))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
