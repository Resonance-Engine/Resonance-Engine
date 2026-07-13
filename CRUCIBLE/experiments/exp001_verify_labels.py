"""exp001 — Is our ground truth real?

Verifies backend/data/labeled_test_set.json against actual market data.

Question: do the `actual_move_pct` / `direction` labels in the 100-event test
set correspond to real price moves, or were they fabricated when the file was
generated (commit a7b5252, AI-co-authored, 23/100 events dated on weekends)?

Method: for every event, fetch real daily close history from the Yahoo Finance
chart API (free, no key, cached under CRUCIBLE/data/yahoo/; Stooq was tried
first but now sits behind a JS proof-of-work wall) and compute the real
close-to-close return over the labeled window:
  - 4h / 24h -> return on the event's trading day (next trading day if the
    event date is a weekend/holiday), vs prior trading-day close
  - 1w       -> close 5 trading days after the event vs prior trading-day close
Then measure sign agreement and magnitude correlation between labels and
reality. Real labels should show high sign agreement (>=80% given intraday vs
daily noise) and strong magnitude correlation. Fabricated labels should look
like coin flips with near-zero correlation.

Cost ceiling: $0 (Stooq is free; results cached). Runtime: ~1 min cold.
Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import statistics
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "CRUCIBLE" / "data" / "yahoo"
TEST_SET = ROOT / "backend" / "data" / "labeled_test_set.json"
OUT = ROOT / "CRUCIBLE" / "data" / "exp001_results.json"

YAHOO_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval=1d"
)


def fetch_history(ticker: str) -> dict[date, float]:
    """Daily close series for a US ticker from Yahoo Finance, disk-cached."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{ticker.lower()}.json"
    if not path.exists():
        req = urllib.request.Request(
            YAHOO_URL.format(symbol=ticker.upper().replace("-", "-")),
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            path.write_bytes(resp.read())
    payload = json.loads(path.read_text())
    closes: dict[date, float] = {}
    try:
        result = payload["chart"]["result"][0]
        stamps = result["timestamp"]
        quote_closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, TypeError, IndexError):
        return closes
    for ts, close in zip(stamps, quote_closes):
        if close is None:
            continue
        closes[datetime.fromtimestamp(ts, tz=timezone.utc).date()] = float(close)
    return closes


def real_return(closes: dict[date, float], event_date: date, window: str) -> float | None:
    """Close-to-close % return over the labeled window, or None if data missing."""
    days = sorted(closes)
    if not days or event_date < days[0] or event_date > days[-1] + timedelta(days=10):
        return None
    prior = [d for d in days if d < event_date]
    onward = [d for d in days if d >= event_date]
    if not prior or not onward:
        return None
    pre = closes[prior[-1]]
    event_day_idx = days.index(onward[0])
    if window == "1w":
        post_idx = min(event_day_idx + 4, len(days) - 1)
    else:  # 4h / 24h -> the event trading day itself
        post_idx = event_day_idx
    post = closes[days[post_idx]]
    return (post - pre) / pre * 100.0


def main() -> None:
    events = json.loads(TEST_SET.read_text())["events"]
    results, missing = [], []
    for e in events:
        closes = fetch_history(e["ticker"])
        r = real_return(closes, date.fromisoformat(e["date"]), e["impact_window"])
        if r is None:
            missing.append(e["event_id"])
            continue
        results.append(
            {
                "event_id": e["event_id"],
                "ticker": e["ticker"],
                "date": e["date"],
                "window": e["impact_window"],
                "labeled_move": e["actual_move_pct"],
                "labeled_direction": e["direction"],
                "real_move": round(r, 2),
            }
        )

    n = len(results)
    sign_hits = sum(
        1
        for r in results
        if (r["labeled_direction"] == "positive") == (r["real_move"] > 0)
    )
    labeled = [r["labeled_move"] for r in results]
    real = [r["real_move"] for r in results]
    pearson = statistics.correlation(labeled, real) if n > 2 else float("nan")
    spearman = (
        statistics.correlation(
            [sorted(labeled).index(x) for x in labeled],
            [sorted(real).index(x) for x in real],
        )
        if n > 2
        else float("nan")
    )
    # among big real moves (|r|>=2%), does the label at least get the sign right?
    big = [r for r in results if abs(r["real_move"]) >= 2.0]
    big_hits = sum(
        1 for r in big if (r["labeled_direction"] == "positive") == (r["real_move"] > 0)
    )

    summary = {
        "n_scored": n,
        "n_missing_data": len(missing),
        "missing": missing,
        "sign_agreement": round(sign_hits / n, 3) if n else None,
        "sign_agreement_big_moves": round(big_hits / len(big), 3) if big else None,
        "n_big_moves": len(big),
        "pearson_magnitude_corr": round(pearson, 3),
        "spearman_magnitude_corr": round(spearman, 3),
        "mean_abs_labeled": round(statistics.mean(abs(x) for x in labeled), 2),
        "mean_abs_real": round(statistics.mean(abs(x) for x in real), 2),
    }
    OUT.write_text(json.dumps({"summary": summary, "per_event": results}, indent=2))
    print(json.dumps(summary, indent=2))
    worst = sorted(results, key=lambda r: -abs(r["labeled_move"] - r["real_move"]))[:10]
    print("\nLargest label-vs-reality gaps:")
    for r in worst:
        print(
            f"  {r['event_id']} {r['ticker']:6s} {r['date']} {r['window']:3s} "
            f"labeled {r['labeled_move']:+6.1f}% ({r['labeled_direction']})  "
            f"real {r['real_move']:+6.2f}%"
        )


if __name__ == "__main__":
    sys.exit(main())
