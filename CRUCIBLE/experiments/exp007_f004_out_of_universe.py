"""exp007 — Bet E: is the SHIPPED magnitude model calibrated out-of-universe?

The F004 model wired into production (src/agents/magnitude.py) was fit on 46
mega-caps. Finding 006 proved mega-cap samples can flatter effect sizes.
This experiment scores the shipped weights on the 13,022-event S&P 500 set
(exp006) — 456 of 502 tickers were never seen in training.

Pre-registered kill criterion (BETS.md): if the shipped weights score a WORSE
Brier than the item-code base-rate table on the out-of-universe sample, the
confidence we currently emit is miscalibrated for non-mega-caps → production
incident, refit required before live signals at scale.

Also runs the refit: same features re-fit on the S&P 500 set (train ≤ 2025-12-31,
test 2026) to measure what a bigger universe buys.

Cost ceiling: $0 (all inputs cached on disk). Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import statistics
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "CRUCIBLE" / "experiments"))

from exp001_verify_labels import fetch_history  # noqa: E402
from exp004_calibrated_magnitude import (  # noqa: E402
    ITEM_FEATURES,
    fit_logistic,
    item_bucket,
    metrics,
    trailing_vol,
)
from src.agents.magnitude import magnitude_probability  # noqa: E402

DATA = ROOT / "CRUCIBLE" / "data"
OUT = DATA / "exp007_results.json"
SPLIT = date(2025, 12, 31)
TARGET_ABS = 2.0

# F004's train-derived base-rate table (the fallback bar)
BASE_TABLE = {"2.02": 0.675, "7.01": 0.318, "8.01/1.01": 0.168, "other": 0.195}

ORIGINAL_46 = {
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "UNH", "HD", "MA", "DIS", "BAC", "XOM", "PFE", "KO",
    "CSCO", "INTC", "AMD", "CRM", "NFLX", "ADBE", "QCOM", "TXN", "ORCL", "IBM",
    "GE", "BA", "CAT", "MMM", "GS", "MS", "C", "WFC", "T", "VZ",
    "UBER", "SNAP", "SBUX", "NKE", "MRNA", "ABBV", "AVGO",
}


def load_rows() -> list[dict]:
    events = json.loads((DATA / "sp500_labeled_8k_set.json").read_text())["events"]
    vol_cache: dict[str, dict] = {}
    rows = []
    for e in events:
        closes = vol_cache.setdefault(e["ticker"], fetch_history(e["ticker"]))
        vol = trailing_vol(closes, date.fromisoformat(e["event_trading_day"]))
        if vol is None:
            continue
        rows.append(
            {
                "ticker": e["ticker"],
                "event_day": date.fromisoformat(e["event_trading_day"]),
                "items": e["items"],
                "vol": vol,
                "y": abs(e["abn_1d"]) >= TARGET_ABS,
            }
        )
    return rows


def evaluate_sample(name: str, rows: list[dict]) -> dict:
    y = [r["y"] for r in rows]
    p_shipped = [magnitude_probability(r["items"], trailing_vol=r["vol"]) for r in rows]
    p_table = [BASE_TABLE[item_bucket(set(r["items"]))] for r in rows]
    return {
        name: {
            "shipped_f004": metrics(y, p_shipped),
            "base_rate_table": metrics(y, p_table),
        }
    }


def refit_on_sp500(rows: list[dict]) -> dict:
    """Same features, re-fit on the big universe with a time split."""
    train = [r for r in rows if r["event_day"] <= SPLIT]
    test = [r for r in rows if r["event_day"] > SPLIT]

    def design(rs: list[dict]) -> np.ndarray:
        items = [[1.0 if f in r["items"] else 0.0 for f in ITEM_FEATURES] for r in rs]
        x = np.array(items)
        vol = np.array([[r["vol"]] for r in rs])
        ones = np.ones((len(rs), 1))
        return np.hstack([ones, x, vol])

    xtr, xte = design(train), design(test)
    vcol = 1 + len(ITEM_FEATURES)
    mu, sd = xtr[:, vcol].mean(), xtr[:, vcol].std()
    xtr[:, vcol] = (xtr[:, vcol] - mu) / sd
    xte[:, vcol] = (xte[:, vcol] - mu) / sd
    w = fit_logistic(xtr, np.array([1.0 if r["y"] else 0.0 for r in train]))
    p = (1.0 / (1.0 + np.exp(-xte @ w))).tolist()
    y_te = [r["y"] for r in test]
    p_shipped_te = [
        magnitude_probability(r["items"], trailing_vol=r["vol"]) for r in test
    ]
    return {
        "n_train": len(train),
        "n_test": len(test),
        "weights": {
            n: round(float(v), 4)
            for n, v in zip(["bias", *ITEM_FEATURES, "trailing_vol_z"], w)
        },
        "vol_standardization": {"train_mean": round(float(mu), 4), "train_sd": round(float(sd), 4)},
        "test_refit": metrics(y_te, p),
        "test_shipped_f004": metrics(y_te, p_shipped_te),
    }


def main() -> None:
    rows = load_rows()
    oou = [r for r in rows if r["ticker"] not in ORIGINAL_46]
    print(f"rows={len(rows)} out-of-universe={len(oou)}", flush=True)
    print(f"overall positive rate: {statistics.mean(r['y'] for r in rows):.3f}", flush=True)

    results = {}
    results.update(evaluate_sample("full_sp500", rows))
    results.update(evaluate_sample("out_of_universe_456_tickers", oou))
    results.update(evaluate_sample("out_of_universe_2026_only",
                                   [r for r in oou if r["event_day"] > SPLIT]))
    results["refit_sp500_time_split"] = refit_on_sp500(rows)

    OUT.write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
