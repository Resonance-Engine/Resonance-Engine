"""exp008 — Bet F: model ceiling — sector / size / novelty features vs shipped v2.

Pre-registered (BETS.md, before running): the best feature set must beat the
shipped v2 model by >= +0.010 AUC on the identical time split AND improve
Brier, else v2 stands and no complexity ships.

Feature sets, cumulative ablation on the S&P 500 labeled set
(train <= 2025-12-31, test = 2026, target |abn_1d| >= 2%):

  v2_repro      items(7) + trailing vol z          (sanity: must match F007)
  +interact     + n_items, 2.02 x vol_z
  +novelty      + log1p(days since ticker's last 8-K)
  +size         + log10(20-day avg dollar volume)  (from cached Yahoo bars)
  +sector       + top-10 two-digit SIC one-hots    (from cached EDGAR submissions)

Secondary (report-only, no ship decision): best model at |abn|>=1% and >=5%
thresholds, and the 5-day-horizon target |abn_5d| >= 2%.

Cost ceiling: $0 (all inputs cached). Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "CRUCIBLE" / "experiments"))

from exp002_build_real_labeled_set import window_return  # noqa: E402
from exp004_calibrated_magnitude import (  # noqa: E402
    ITEM_FEATURES,
    fit_logistic,
    metrics,
    trailing_vol,
)

DATA = ROOT / "CRUCIBLE" / "data"
OUT = DATA / "exp008_results.json"
SPLIT = date(2025, 12, 31)
YAHOO = DATA / "yahoo"
SUBMISSIONS = DATA / "edgar_submissions"
N_SIC_GROUPS = 10


def load_price_data(ticker: str) -> tuple[dict[date, float], dict[date, float]]:
    """(closes, dollar_volume) from the cached Yahoo chart payload."""
    path = YAHOO / f"{ticker.lower()}.json"
    closes: dict[date, float] = {}
    dollar: dict[date, float] = {}
    if not path.exists():
        return closes, dollar
    try:
        result = json.loads(path.read_text())["chart"]["result"][0]
        stamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
    except (KeyError, TypeError, IndexError):
        return closes, dollar
    for ts, close, vol in zip(stamps, quote["close"], quote["volume"]):
        if close is None:
            continue
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        closes[d] = float(close)
        if vol:
            dollar[d] = float(close) * float(vol)
    return closes, dollar


def sic_two_digit(cik: int) -> str:
    path = SUBMISSIONS / f"{cik}.json"
    if not path.exists():
        return "??"
    try:
        sic = str(json.loads(path.read_text()).get("sic", "") or "")
    except Exception:  # noqa: BLE001
        return "??"
    return sic[:2] if len(sic) >= 2 else "??"


def avg_dollar_volume(dollar: dict[date, float], event_day: date, lookback: int = 20) -> float | None:
    days = sorted(d for d in dollar if d < event_day)[-lookback:]
    if len(days) < lookback // 2:
        return None
    return sum(dollar[d] for d in days) / len(days)


def load_rows() -> list[dict]:
    events = json.loads((DATA / "sp500_labeled_8k_set.json").read_text())["events"]
    events.sort(key=lambda e: (e["ticker"], e["filed"]))
    px: dict[str, tuple[dict, dict]] = {}
    spy_closes, _ = load_price_data("spy")
    last_filed: dict[str, date] = {}
    rows = []
    for e in events:
        ticker = e["ticker"]
        if ticker not in px:
            px[ticker] = load_price_data(ticker)
        closes, dollar = px[ticker]
        ev_day = date.fromisoformat(e["event_trading_day"])
        filed = date.fromisoformat(e["filed"])
        vol = trailing_vol(closes, ev_day)
        adv = avg_dollar_volume(dollar, ev_day)
        prev = last_filed.get(ticker)
        last_filed[ticker] = filed
        if vol is None or adv is None:
            continue
        ret_5d = window_return(closes, ev_day, 5)
        spy_5d = window_return(spy_closes, ev_day, 5)
        rows.append(
            {
                "event_day": ev_day,
                "items": e["items"],
                "vol": vol,
                "abn_1d": e["abn_1d"],
                "abn_5d": (ret_5d - spy_5d) if ret_5d is not None and spy_5d is not None else None,
                "n_items": len(e["items"]),
                "days_since_last": (filed - prev).days if prev else 365,
                "log_adv": math.log10(adv),
                "sic2": sic_two_digit(e["cik"]),
            }
        )
    return rows


def build_features(rows, train_idx, spec: str, sic_groups: list[str]):
    """Design matrix per feature spec; continuous cols z-scored on train."""
    cols: list[list[float]] = []
    for r in rows:
        f = [1.0] + [1.0 if it in r["items"] else 0.0 for it in ITEM_FEATURES] + [r["vol"]]
        if spec >= "b_interact":
            f += [float(r["n_items"]), ("2.02" in r["items"]) * r["vol"]]
        if spec >= "c_novelty":
            f += [math.log1p(min(r["days_since_last"], 365))]
        if spec >= "d_size":
            f += [r["log_adv"]]
        if spec >= "e_sector":
            f += [1.0 if r["sic2"] == g else 0.0 for g in sic_groups]
        cols.append(f)
    x = np.array(cols)
    # z-score every non-binary column using train stats
    for j in range(1, x.shape[1]):
        col = x[train_idx, j]
        if set(np.unique(col)) <= {0.0, 1.0}:
            continue
        mu, sd = col.mean(), col.std()
        if sd > 0:
            x[:, j] = (x[:, j] - mu) / sd
    return x


def run_target(rows: list[dict], label: str, y_fn) -> dict:
    idx = [i for i, r in enumerate(rows) if y_fn(r) is not None]
    y = np.array([1.0 if y_fn(rows[i]) else 0.0 for i in idx])
    sub = [rows[i] for i in idx]
    tr = [i for i, r in enumerate(sub) if r["event_day"] <= SPLIT]
    te = [i for i, r in enumerate(sub) if r["event_day"] > SPLIT]
    sic_counts = Counter(sub[i]["sic2"] for i in tr)
    sic_groups = [s for s, _ in sic_counts.most_common(N_SIC_GROUPS)]
    out = {"n_train": len(tr), "n_test": len(te)}
    for spec in ["a_v2_repro", "b_interact", "c_novelty", "d_size", "e_sector"]:
        x = build_features(sub, tr, spec, sic_groups)
        w = fit_logistic(x[tr], y[tr])
        p = (1.0 / (1.0 + np.exp(-x[te] @ w))).tolist()
        out[spec] = metrics([bool(v) for v in y[te]], p)
    return {label: out}


def main() -> None:
    rows = load_rows()
    print(f"rows with full features: {len(rows)}", flush=True)
    results = {}
    results.update(run_target(rows, "primary_abn1d_ge2", lambda r: abs(r["abn_1d"]) >= 2))
    results.update(run_target(rows, "secondary_abn1d_ge1", lambda r: abs(r["abn_1d"]) >= 1))
    results.update(run_target(rows, "secondary_abn1d_ge5", lambda r: abs(r["abn_1d"]) >= 5))
    results.update(run_target(
        rows, "secondary_abn5d_ge2",
        lambda r: None if r["abn_5d"] is None else abs(r["abn_5d"]) >= 2,
    ))
    OUT.write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
