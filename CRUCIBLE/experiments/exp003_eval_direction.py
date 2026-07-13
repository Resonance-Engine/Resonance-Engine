"""exp003b — Bet B: does filing text predict the SIGN of the abnormal return?

Joins the real labeled set (exp002) with real earnings-8-K texts (exp003a) and
tests whether the repo's own sentiment machinery — Loughran-McDonald net
sentiment and FinBERT — predicts sign(abn_1d) better than the base rate.

Protocol (fixed before looking at results):
  - Universe: item-2.02 events with abn_1d labels and usable text.
  - Time split: train = event day ≤ 2025-12-31, test = 2026 (no look-ahead).
  - Score → decision threshold chosen on train only (accuracy-maximizing grid);
    reported on test. AUC reported threshold-free (Mann-Whitney).
  - Baselines: majority class on test; coin flip = 0.5 AUC.
  - Variant: "decisive moves" subset (|abn_1d| ≥ 1%).

Kill criterion (from BETS.md): <55% held-out sign accuracy → directional
claims are dead at this evidence level.

Cost ceiling: $0 (all local; FinBERT ~440MB one-time HF download).
Capture date: 2026-07-13.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from src.nlp.loughran_mcdonald import score_text  # noqa: E402

DATA = ROOT / "CRUCIBLE" / "data"
TEXTS = DATA / "filing_texts"
OUT = DATA / "exp003_results.json"

SPLIT_DATE = date(2025, 12, 31)
CHUNK_WORDS = 380
MAX_CHUNKS = 5


def load_joined() -> list[dict]:
    events = json.loads((DATA / "real_labeled_8k_set.json").read_text())["events"]
    joined = []
    for e in events:
        if "2.02" not in e["items"] or e["abn_1d"] is None:
            continue
        path = TEXTS / f"{e['accession']}.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text())
        parts = doc.get("parts") or {}
        # Prefer press-release exhibits (the substance); fall back to 8-K body.
        text = " ".join(v for k, v in sorted(parts.items()) if k.startswith("EX-99"))
        if len(text) < 300:
            text = parts.get("8-K", "")
        if len(text) < 300:
            continue
        joined.append({**e, "text": text})
    return joined


def lm_score(text: str) -> float:
    return score_text(text)["net_sentiment"]


def finbert_scores(rows: list[dict]) -> list[float]:
    from src.nlp.finbert import classify_batch

    all_chunks: list[str] = []
    spans: list[tuple[int, int]] = []
    for r in rows:
        words = r["text"].split()
        chunks = [
            " ".join(words[i : i + CHUNK_WORDS])
            for i in range(0, min(len(words), CHUNK_WORDS * MAX_CHUNKS), CHUNK_WORDS)
        ]
        spans.append((len(all_chunks), len(all_chunks) + len(chunks)))
        all_chunks.extend(chunks)
    results = classify_batch(all_chunks)
    scores = []
    for start, end in spans:
        rs = results[start:end]
        scores.append(sum(x.positive - x.negative for x in rs) / len(rs) if rs else 0.0)
    return scores


def auc(scores: list[float], labels: list[bool]) -> float:
    """Mann-Whitney AUC of score for label=True."""
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def best_train_threshold(scores: list[float], labels: list[bool]) -> float:
    cands = sorted(set(scores))
    best_t, best_acc = cands[0], -1.0
    for t in cands:
        acc = sum((s > t) == y for s, y in zip(scores, labels)) / len(labels)
        if acc > best_acc:
            best_t, best_acc = t, acc
    return best_t


def evaluate(name: str, rows: list[dict], scores: list[float]) -> dict:
    out = {}
    for variant, keep in [
        ("all", lambda r: True),
        ("decisive_|abn|>=1%", lambda r: abs(r["abn_1d"]) >= 1.0),
    ]:
        idx = [i for i, r in enumerate(rows) if keep(r)]
        tr = [i for i in idx if date.fromisoformat(rows[i]["event_trading_day"]) <= SPLIT_DATE]
        te = [i for i in idx if date.fromisoformat(rows[i]["event_trading_day"]) > SPLIT_DATE]
        y_tr = [rows[i]["abn_1d"] > 0 for i in tr]
        y_te = [rows[i]["abn_1d"] > 0 for i in te]
        s_tr = [scores[i] for i in tr]
        s_te = [scores[i] for i in te]
        if not te or not tr:
            continue
        t = best_train_threshold(s_tr, y_tr)
        acc = sum((s > t) == y for s, y in zip(s_te, y_te)) / len(y_te)
        majority = max(sum(y_te), len(y_te) - sum(y_te)) / len(y_te)
        out[variant] = {
            "n_train": len(tr),
            "n_test": len(te),
            "test_pos_rate": round(sum(y_te) / len(y_te), 3),
            "test_majority_baseline": round(majority, 3),
            "threshold_from_train": round(t, 4),
            "test_sign_accuracy": round(acc, 3),
            "test_auc": round(auc(s_te, y_te), 3),
            "full_sample_auc": round(auc([scores[i] for i in idx], [rows[i]["abn_1d"] > 0 for i in idx]), 3),
        }
    return {name: out}


def main() -> None:
    rows = load_joined()
    print(f"joined events with text: {len(rows)}")
    results = {}

    lm = [lm_score(r["text"]) for r in rows]
    results.update(evaluate("loughran_mcdonald_net", rows, lm))
    print(json.dumps(results, indent=2))

    print("running FinBERT (local, may take minutes)...")
    fb = finbert_scores(rows)
    results.update(evaluate("finbert_pos_minus_neg", rows, fb))

    OUT.write_text(
        json.dumps(
            {
                "results": results,
                "per_event": [
                    {
                        "accession": r["accession"],
                        "ticker": r["ticker"],
                        "event_trading_day": r["event_trading_day"],
                        "abn_1d": r["abn_1d"],
                        "lm": round(l, 4),
                        "finbert": round(f, 4),
                    }
                    for r, l, f in zip(rows, lm, fb)
                ],
            },
            indent=1,
        )
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
