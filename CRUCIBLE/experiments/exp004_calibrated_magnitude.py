"""exp004 — Bet C: calibrated magnitude confidence from measured features.

Target: P(|abn_1d| >= 2%) for a real 8-K — the "this filing matters" claim
that Finding 002 showed is actually predictable (unlike direction, Finding 003).

Models (train <= 2025-12-31, test = 2026):
  1. base_rate      — train frequency bucketed by most-impactful item present
                      (2.02 > 7.01 > {8.01,1.01} > rest). The bar to beat.
  2. logistic       — logistic regression (pure-numpy gradient descent) over
                      item indicators + trailing 20-session realized vol +
                      after-hours flag.
Metrics on the held-out 2026 test set: Brier, log loss, AUC, ECE — computed
with the repo's own src/evaluation code (first use in anger, on real data).

Kill criterion (BETS.md): logistic must beat the base-rate table on test
Brier, else ship the plain table.

Cost ceiling: $0 (all inputs already cached on disk).
Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "CRUCIBLE" / "experiments"))

from exp001_verify_labels import fetch_history  # noqa: E402
from src.evaluation.calibration import calibration_error  # noqa: E402
from src.evaluation.metrics import brier_score, log_loss  # noqa: E402

DATA = ROOT / "CRUCIBLE" / "data"
OUT = DATA / "exp004_results.json"

SPLIT = date(2025, 12, 31)
TARGET_ABS = 2.0
VOL_LOOKBACK = 20
ITEM_FEATURES = ["2.02", "7.01", "8.01", "1.01", "5.02", "5.07", "9.01"]


def trailing_vol(closes: dict[date, float], event_day: date) -> float | None:
    days = sorted(d for d in closes if d < event_day)
    if len(days) < VOL_LOOKBACK + 1:
        return None
    window = days[-(VOL_LOOKBACK + 1):]
    rets = [
        (closes[b] - closes[a]) / closes[a] * 100.0
        for a, b in zip(window, window[1:])
    ]
    return statistics.stdev(rets)


def load_features() -> list[dict]:
    events = json.loads((DATA / "real_labeled_8k_set.json").read_text())["events"]
    vols: dict[str, dict[date, float]] = {}
    rows = []
    for e in events:
        if e["abn_1d"] is None:
            continue
        closes = vols.setdefault(e["ticker"], fetch_history(e["ticker"]))
        ev_day = date.fromisoformat(e["event_trading_day"])
        vol = trailing_vol(closes, ev_day)
        if vol is None:
            continue
        accepted = datetime.fromisoformat(e["accepted"].replace("Z", ""))
        rows.append(
            {
                "event_day": ev_day,
                "y": abs(e["abn_1d"]) >= TARGET_ABS,
                "vol": vol,
                "after_hours": accepted.hour >= 16,
                "items": set(e["items"]),
            }
        )
    return rows


def item_bucket(items: set[str]) -> str:
    if "2.02" in items:
        return "2.02"
    if "7.01" in items:
        return "7.01"
    if items & {"8.01", "1.01"}:
        return "8.01/1.01"
    return "other"


def design_matrix(rows: list[dict]) -> np.ndarray:
    cols = [[1.0 if f in r["items"] else 0.0 for f in ITEM_FEATURES] for r in rows]
    x = np.array(cols)
    vol = np.array([[r["vol"]] for r in rows])
    ah = np.array([[1.0 if r["after_hours"] else 0.0] for r in rows])
    ones = np.ones((len(rows), 1))
    return np.hstack([ones, x, vol, ah])


def fit_logistic(x: np.ndarray, y: np.ndarray, lr: float = 0.05, epochs: int = 5000,
                 l2: float = 1e-3) -> np.ndarray:
    # standardize non-binary columns (vol) using train stats baked into x upstream
    w = np.zeros(x.shape[1])
    for _ in range(epochs):
        p = 1.0 / (1.0 + np.exp(-x @ w))
        grad = x.T @ (p - y) / len(y) + l2 * w
        w -= lr * grad
    return w


def metrics(y: list[bool], p: list[float]) -> dict:
    yi = [1 if v else 0 for v in y]
    pos = [q for q, v in zip(p, y) if v]
    neg = [q for q, v in zip(p, y) if not v]
    auc = (
        sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / (len(pos) * len(neg))
        if pos and neg
        else float("nan")
    )
    return {
        "brier": round(brier_score(p, y), 4),
        "log_loss": round(log_loss(p, y), 4),
        "ece_10bin": round(calibration_error(p, y, n_bins=10), 4),
        "auc": round(auc, 3),
        "base_positive_rate": round(sum(yi) / len(yi), 3),
        "n": len(yi),
    }


def main() -> None:
    rows = load_features()
    train = [r for r in rows if r["event_day"] <= SPLIT]
    test = [r for r in rows if r["event_day"] > SPLIT]
    print(f"n={len(rows)} train={len(train)} test={len(test)}")

    # Model 1: train-frequency base-rate table by item bucket
    buckets: dict[str, list[bool]] = {}
    for r in train:
        buckets.setdefault(item_bucket(r["items"]), []).append(r["y"])
    table = {k: sum(v) / len(v) for k, v in buckets.items()}
    p_base = [table[item_bucket(r["items"])] for r in test]

    # Model 2: logistic regression, vol standardized with train stats
    xtr, xte = design_matrix(train), design_matrix(test)
    vol_col = 1 + len(ITEM_FEATURES)
    mu, sd = xtr[:, vol_col].mean(), xtr[:, vol_col].std()
    xtr[:, vol_col] = (xtr[:, vol_col] - mu) / sd
    xte[:, vol_col] = (xte[:, vol_col] - mu) / sd
    ytr = np.array([1.0 if r["y"] else 0.0 for r in train])
    w = fit_logistic(xtr, ytr)
    p_lr = (1.0 / (1.0 + np.exp(-xte @ w))).tolist()

    y_te = [r["y"] for r in test]
    results = {
        "target": f"|abn_1d| >= {TARGET_ABS}%",
        "train_base_rate_table": {k: round(v, 3) for k, v in sorted(table.items())},
        "logistic_weights": {
            name: round(float(v), 4)
            for name, v in zip(
                ["bias", *ITEM_FEATURES, "trailing_vol_z", "after_hours"], w
            )
        },
        "test_base_rate_table": metrics(y_te, p_base),
        "test_logistic": metrics(y_te, p_lr),
    }
    OUT.write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
