"""exp009 — Bet G: the high-conviction P(|abn_1d| >= 5%) "major impact" tier.

Pre-registered ship criteria (BETS.md, written before this ran):
  1. precision >= 0.40 at alert line P >= 0.40, with >= 100 test alerts
     (test = held-out 2026, n=3,616, base rate 16.2%);
  2. ECE <= 0.04 overall for the chosen model;
  3. variant by better test Brier; ties/near-ties (<0.002) -> simpler
     (v2 features), since sector needs production plumbing.

Outputs production-ready weights (JSON) for the chosen variant.

Cost ceiling: $0 (all inputs cached). Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "CRUCIBLE" / "experiments"))

from exp004_calibrated_magnitude import ITEM_FEATURES, fit_logistic, metrics  # noqa: E402
from exp008_model_ceiling import N_SIC_GROUPS, build_features, load_rows  # noqa: E402

DATA = ROOT / "CRUCIBLE" / "data"
OUT = DATA / "exp009_results.json"
SPLIT = date(2025, 12, 31)
TARGET_ABS = 5.0
ALERT_LINE = 0.40


def alert_stats(p: list[float], y: list[bool], line: float) -> dict:
    alerts = [(pi, yi) for pi, yi in zip(p, y) if pi >= line]
    if not alerts:
        return {"line": line, "n_alerts": 0}
    hits = sum(yi for _, yi in alerts)
    return {
        "line": line,
        "n_alerts": len(alerts),
        "precision": round(hits / len(alerts), 3),
        "recall": round(hits / sum(y), 3),
    }


def main() -> None:
    rows = load_rows()
    y_all = np.array([1.0 if abs(r["abn_1d"]) >= TARGET_ABS else 0.0 for r in rows])
    tr = [i for i, r in enumerate(rows) if r["event_day"] <= SPLIT]
    te = [i for i, r in enumerate(rows) if r["event_day"] > SPLIT]
    sic_groups = [s for s, _ in Counter(rows[i]["sic2"] for i in tr).most_common(N_SIC_GROUPS)]
    y_te = [bool(v) for v in y_all[te]]

    results: dict = {"target": f"|abn_1d| >= {TARGET_ABS}%", "n_train": len(tr), "n_test": len(te)}
    fitted = {}
    for spec, label in [("a_v2_repro", "v2_features"), ("e_sector", "plus_sector")]:
        x = build_features(rows, tr, spec, sic_groups)
        w = fit_logistic(x[tr], y_all[tr])
        p = (1.0 / (1.0 + np.exp(-x[te] @ w))).tolist()
        fitted[label] = (x, w, p)
        results[label] = {
            "metrics": metrics(y_te, p),
            "alerts": [alert_stats(p, y_te, line) for line in (0.30, 0.40, 0.50)],
        }

    # Pre-registered variant choice: better Brier; near-tie (<0.002) -> simpler
    b_simple = results["v2_features"]["metrics"]["brier"]
    b_sector = results["plus_sector"]["metrics"]["brier"]
    chosen = "v2_features" if b_simple - b_sector < 0.002 else "plus_sector"
    m = results[chosen]["metrics"]
    a40 = next(a for a in results[chosen]["alerts"] if a["line"] == ALERT_LINE)
    ship = (
        a40.get("n_alerts", 0) >= 100
        and a40.get("precision", 0) >= 0.40
        and m["ece_10bin"] <= 0.04
    )
    results["chosen_variant"] = chosen
    results["ship_check"] = {
        "precision_at_0.40": a40.get("precision"),
        "n_alerts": a40.get("n_alerts"),
        "ece": m["ece_10bin"],
        "verdict": "SHIP" if ship else "DO NOT SHIP (pre-registered criteria not met)",
    }

    # Export production weights for the chosen variant (fit on train only —
    # the same fit that was evaluated; do NOT refit on all data, so the
    # shipped weights are exactly the validated ones)
    _, w, _ = fitted[chosen]
    names = ["bias", *ITEM_FEATURES, "trailing_vol"]
    if chosen == "plus_sector":
        # build_features specs are cumulative: e_sector includes the
        # intermediate features as well
        names += ["n_items", "item202_x_vol", "log1p_days_since_last", "log10_adv"]
        names += [f"sic_{g}" for g in sic_groups]
    # recover vol standardization used by build_features (train stats)
    vols = np.array([rows[i]["vol"] for i in tr])
    results["production_weights"] = {
        "weights": {n: round(float(v), 4) for n, v in zip(names, w)},
        "vol_standardization": {
            "train_mean": round(float(vols.mean()), 4),
            "train_sd": round(float(vols.std()), 4),
        },
    }

    OUT.write_text(json.dumps(results, indent=1))
    print(json.dumps({k: v for k, v in results.items() if k != "production_weights"}, indent=2))
    print(json.dumps(results["production_weights"], indent=2))


if __name__ == "__main__":
    main()
