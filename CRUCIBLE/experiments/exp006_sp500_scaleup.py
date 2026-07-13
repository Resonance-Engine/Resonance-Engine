"""exp006 — Bet D validation: EPS-miss asymmetry at S&P 500 scale.

Finding 005 found P(negative | EPS miss) = 78.6% on n=28 misses. This is the
pre-registered validation: rebuild the real-label machinery (exp002) for the
full S&P 500, join Yahoo earningsHistory surprises (exp005), and re-measure
the bucket structure on ~10x the sample.

Pre-registered kill criterion (BETS.md, set before running):
  P(negative | miss) < 65% on the scaled sample, or the monotone bucket
  structure disappears → Bet D dies and the miss-alert is NOT shipped.

Sources (all free): Wikipedia S&P 500 constituents; SEC EDGAR submissions
API (8-K dates, item codes, acceptance times); Yahoo daily closes (SPY-
adjusted labels, after-hours-aware); Yahoo earningsHistory (cookie+crumb).

Cost ceiling: $0. ~1,500 rate-limited requests, cold runtime ~15-25 min.
Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CRUCIBLE" / "experiments"))

from exp001_verify_labels import fetch_history  # noqa: E402
from exp002_build_real_labeled_set import (  # noqa: E402
    eightk_filings,
    event_trading_day,
    load_ticker_cik_map,
    window_return,
)
from exp005_surprise_direction import fetch_earnings_history  # noqa: E402

DATA = ROOT / "CRUCIBLE" / "data"
OUT_SET = DATA / "sp500_labeled_8k_set.json"
OUT_RESULTS = DATA / "exp006_results.json"
WIKI_CACHE = DATA / "sp500_constituents.html"
JOIN_WINDOW_DAYS = 100


def sp500_tickers() -> list[str]:
    """S&P 500 tickers from Wikipedia's constituents table (cached)."""
    if not WIKI_CACHE.exists():
        req = urllib.request.Request(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            WIKI_CACHE.write_bytes(resp.read())
    html = WIKI_CACHE.read_text(errors="ignore")
    table = html.split('id="constituents"', 1)[-1]
    # Ticker cells link to exchange quote pages; symbol is the link text.
    tickers = re.findall(
        r'<a[^>]+href="https?://www\.nyse\.com/quote/[^"]+"[^>]*>([A-Z.\-]{1,6})</a>'
        r"|<a[^>]+nasdaq\.com/market-activity/stocks/[^\"]+\"[^>]*>([A-Z.\-]{1,6})</a>",
        table,
    )
    out: list[str] = []
    for a, b in tickers:
        sym = (a or b).strip()
        if sym and sym not in out:
            out.append(sym)
    return out


def build_labeled_set(tickers: list[str]) -> list[dict]:
    """exp002's labeling loop, parameterized by ticker list."""
    cik_map = load_ticker_cik_map()
    spy = fetch_history("SPY")
    events: list[dict] = []
    n_no_cik = n_no_px = 0
    for i, wiki_ticker in enumerate(tickers):
        yahoo_t = wiki_ticker.replace(".", "-")  # BRK.B → BRK-B
        sec_t = wiki_ticker.replace(".", "-")  # SEC file uses BRK-B form
        cik = cik_map.get(sec_t) or cik_map.get(wiki_ticker.replace(".", ""))
        if cik is None:
            n_no_cik += 1
            continue
        try:
            closes = fetch_history(yahoo_t)
            time.sleep(0.15)
        except Exception:
            closes = {}
        if not closes:
            n_no_px += 1
            continue
        try:
            filings = eightk_filings(cik)
        except Exception:
            continue
        for f in filings:
            ev_day = event_trading_day(closes, f)
            if ev_day is None:
                continue
            ret_1d = window_return(closes, ev_day, 1)
            spy_1d = window_return(spy, ev_day, 1)
            if ret_1d is None or spy_1d is None:
                continue
            events.append(
                {
                    "ticker": yahoo_t,
                    "cik": cik,
                    "accession": f["accession"],
                    "filed": f["filed"],
                    "items": f["items"],
                    "event_trading_day": ev_day.isoformat(),
                    "abn_1d": round(ret_1d - spy_1d, 3),
                }
            )
        if (i + 1) % 50 == 0:
            print(f"  labeled {i + 1}/{len(tickers)} tickers ({len(events)} events)", flush=True)
    print(f"  skipped: {n_no_cik} no CIK, {n_no_px} no price data", flush=True)
    return events


def join_surprises(events: list[dict], surprises: dict[str, list[dict]]) -> list[dict]:
    by_ticker: dict[str, list[dict]] = {}
    for e in events:
        if "2.02" in e["items"]:
            by_ticker.setdefault(e["ticker"], []).append(e)
    joined = []
    for ticker, rows in surprises.items():
        for s in rows:
            q_end = date.fromisoformat(s["quarter_end"])
            cands = [
                e
                for e in by_ticker.get(ticker, [])
                if q_end < date.fromisoformat(e["filed"]) <= q_end + timedelta(days=JOIN_WINDOW_DAYS)
            ]
            if not cands:
                continue
            filing = min(cands, key=lambda e: e["filed"])
            joined.append({**s, "ticker": ticker, "filed": filing["filed"],
                           "abn_1d": filing["abn_1d"], "accession": filing["accession"]})
    return joined


def bucket_stats(rows: list[dict]) -> dict:
    if not rows:
        return {}
    neg = sum(r["abn_1d"] < 0 for r in rows)
    big_neg = sum(r["abn_1d"] <= -2 for r in rows)
    return {
        "n": len(rows),
        "p_negative": round(neg / len(rows), 3),
        "p_abn_le_-2": round(big_neg / len(rows), 3),
        "mean_abn": round(statistics.mean(r["abn_1d"] for r in rows), 2),
        "median_abn": round(statistics.median(r["abn_1d"] for r in rows), 2),
    }


def main() -> None:
    tickers = sp500_tickers()
    print(f"S&P 500 tickers parsed: {len(tickers)}", flush=True)

    print("building labeled set (EDGAR + Yahoo)...", flush=True)
    events = build_labeled_set(tickers)
    OUT_SET.write_text(json.dumps({"_meta": {
        "created": date.today().isoformat(),
        "generator": "CRUCIBLE/experiments/exp006_sp500_scaleup.py",
        "label_semantics": "same as real_labeled_8k_set.json (exp002)",
        "n_events": len(events),
    }, "events": events}, indent=1))
    print(f"labeled events: {len(events)}", flush=True)

    print("fetching earnings surprises...", flush=True)
    surprises = fetch_earnings_history(sorted({e["ticker"] for e in events}))
    joined = join_surprises(events, surprises)
    print(f"joined surprise-filing pairs: {len(joined)}", flush=True)

    buckets = {
        "MISS (<=0%)": [r for r in joined if r["surprise_pct"] <= 0],
        "small beat (0-3%)": [r for r in joined if 0 < r["surprise_pct"] <= 3],
        "mid beat (3-10%)": [r for r in joined if 3 < r["surprise_pct"] <= 10],
        "big beat (>10%)": [r for r in joined if r["surprise_pct"] > 10],
    }
    summary = {name: bucket_stats(rows) for name, rows in buckets.items()}

    miss = summary["MISS (<=0%)"]
    p_neg_by_bucket = [v["p_negative"] for v in summary.values() if v]
    verdict = (
        "VALIDATED"
        if miss and miss["p_negative"] >= 0.65
        and p_neg_by_bucket == sorted(p_neg_by_bucket, reverse=True)
        else "KILLED (per pre-registered criterion)"
    )

    OUT_RESULTS.write_text(json.dumps(
        {"verdict": verdict, "buckets": summary, "n_joined": len(joined),
         "per_event": joined}, indent=1))
    print(json.dumps({"verdict": verdict, "buckets": summary}, indent=2))


if __name__ == "__main__":
    main()
