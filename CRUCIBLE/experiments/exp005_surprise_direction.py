"""exp005 — Bet D first test: does EPS surprise predict direction?

Finding 003 killed tone features but hypothesized the market prices results
vs. CONSENSUS EXPECTATIONS. Yahoo's earningsHistory module (free, cookie+crumb
auth) provides actual EPS vs analyst consensus for the last 4 reported
quarters per ticker — exactly the surprise feature, and legitimate for live
use: the estimate exists before the filing and the actual is IN the filing,
so surprise is computable the moment an earnings 8-K drops (no lookahead).

Method:
  - Fetch earningsHistory for the 46 tickers of the real labeled set.
  - Join each surprise record to the item-2.02 filing whose filing date falls
    within (quarter_end, quarter_end + 100d], nearest first — earnings 8-Ks
    follow the quarter they report by 2-8 weeks.
  - Test sign(surprise) vs sign(abn_1d): accuracy vs majority baseline, AUC
    with surprisePercent as the ranking score. Also |surprise| vs |abn_1d|.

Caveat logged up front: only ~4 quarters of history exist per ticker, so
n≈150 and the window (~2025-07 → 2026-05) overlaps the exp004 train period.
This is a viability probe for Bet D, not a full validation — if the signal
is real here, the follow-up is a proper time-split study with a deeper
surprise history source.

Cost ceiling: $0. Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import statistics
import time
import urllib.request
from datetime import date, timedelta
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "CRUCIBLE" / "data"
CACHE = DATA / "yahoo_earnings"
OUT = DATA / "exp005_results.json"

UA = {"User-Agent": "Mozilla/5.0"}
JOIN_WINDOW_DAYS = 100


def _yahoo_opener() -> tuple[urllib.request.OpenerDirector, str]:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    opener.addheaders = list(UA.items())
    try:
        opener.open("https://fc.yahoo.com", timeout=15)
    except Exception:
        pass  # 404 is expected; we only need the cookie
    crumb = opener.open(
        "https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=15
    ).read().decode()
    return opener, crumb


def fetch_earnings_history(tickers: list[str]) -> dict[str, list[dict]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    opener = crumb = None
    out: dict[str, list[dict]] = {}
    for t in tickers:
        path = CACHE / f"{t.lower()}.json"
        if not path.exists():
            if opener is None:
                opener, crumb = _yahoo_opener()
            url = (
                f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{t}"
                f"?modules=earningsHistory&crumb={crumb}"
            )
            try:
                path.write_bytes(opener.open(url, timeout=30).read())
            except Exception as exc:  # noqa: BLE001
                path.write_text(json.dumps({"error": str(exc)}))
            time.sleep(0.3)
        payload = json.loads(path.read_text())
        try:
            hist = payload["quoteSummary"]["result"][0]["earningsHistory"]["history"]
        except (KeyError, TypeError, IndexError):
            continue
        rows = []
        for h in hist:
            try:
                rows.append(
                    {
                        "quarter_end": h["quarter"]["fmt"],
                        "eps_actual": h["epsActual"]["raw"],
                        "eps_estimate": h["epsEstimate"]["raw"],
                        "surprise_pct": h["surprisePercent"]["raw"] * 100.0,
                    }
                )
            except (KeyError, TypeError):
                continue
        out[t] = rows
    return out


def join_to_filings(surprises: dict[str, list[dict]]) -> list[dict]:
    events = json.loads((DATA / "real_labeled_8k_set.json").read_text())["events"]
    by_ticker: dict[str, list[dict]] = {}
    for e in events:
        if "2.02" in e["items"] and e["abn_1d"] is not None:
            by_ticker.setdefault(e["ticker"], []).append(e)
    joined = []
    for ticker, rows in surprises.items():
        for s in rows:
            q_end = date.fromisoformat(s["quarter_end"])
            candidates = [
                e
                for e in by_ticker.get(ticker, [])
                if q_end < date.fromisoformat(e["filed"]) <= q_end + timedelta(days=JOIN_WINDOW_DAYS)
            ]
            if not candidates:
                continue
            filing = min(candidates, key=lambda e: e["filed"])
            joined.append({**s, "ticker": ticker, "filed": filing["filed"],
                           "abn_1d": filing["abn_1d"], "accession": filing["accession"]})
    return joined


def auc(scores: list[float], labels: list[bool]) -> float:
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def main() -> None:
    events = json.loads((DATA / "real_labeled_8k_set.json").read_text())["events"]
    tickers = sorted({e["ticker"] for e in events})
    surprises = fetch_earnings_history(tickers)
    joined = join_to_filings(surprises)

    y = [j["abn_1d"] > 0 for j in joined]
    beat = [j["surprise_pct"] > 0 for j in joined]
    acc = sum(b == t for b, t in zip(beat, y)) / len(y)
    majority = max(sum(y), len(y) - sum(y)) / len(y)
    summary = {
        "n_joined": len(joined),
        "beat_rate": round(sum(beat) / len(beat), 3),
        "positive_abn_rate": round(sum(y) / len(y), 3),
        "sign_accuracy_beat_vs_abn": round(acc, 3),
        "majority_baseline": round(majority, 3),
        "auc_surprise_pct": round(auc([j["surprise_pct"] for j in joined], y), 3),
        "corr_surprise_vs_abn": round(
            statistics.correlation(
                [j["surprise_pct"] for j in joined], [j["abn_1d"] for j in joined]
            ),
            3,
        ),
        "mean_abn_on_beat": round(
            statistics.mean(j["abn_1d"] for j in joined if j["surprise_pct"] > 0), 2
        ),
        "mean_abn_on_miss": round(
            statistics.mean(j["abn_1d"] for j in joined if j["surprise_pct"] <= 0), 2
        ),
    }
    OUT.write_text(json.dumps({"summary": summary, "per_event": joined}, indent=1))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
