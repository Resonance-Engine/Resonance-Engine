# Finding 003 — Bet B KILLED: current sentiment machinery carries no directional signal

**Date:** 2026-07-13 · **Experiments:** `exp003_fetch_texts.py` + `exp003_eval_direction.py` · **Cost:** $0

## Question (Bet B)

Does the text of a real earnings 8-K (press-release exhibits), scored by the
pipeline's own NLP — Loughran-McDonald net sentiment and FinBERT — predict the
**sign** of the next-session SPY-adjusted return better than base rate?

## Method

- 370 real item-2.02 filings fetched from EDGAR (full submissions; EX-99
  press-release exhibits extracted, 8-K body fallback), joined to the real
  labels from Finding 002.
- Protocol fixed in advance: time split (train ≤ 2025-12-31: n=268; test 2026:
  n=102), threshold chosen on train only, threshold-free AUC, majority-class
  baseline, plus a "decisive moves" subset (|abn_1d| ≥ 1%).
- FinBERT run locally in 380-word chunks (≤5/doc), score = mean(pos − neg).
  L-M net sentiment on full text.

## Result — nothing beats the majority class

Test period 2026 (positive rate 41%, majority baseline **58.8%**):

| Scorer | Variant | Test sign accuracy | Test AUC | Full-sample AUC |
|---|---|---|---|---|
| Loughran-McDonald | all | 55.9% | 0.521 | 0.491 |
| Loughran-McDonald | \|abn\| ≥ 1% | 52.2% | 0.505 | 0.494 |
| FinBERT | all | 46.1% | 0.449 | 0.543 |
| FinBERT | \|abn\| ≥ 1% | 45.7% | 0.476 | 0.563 |

Every configuration is at or below the do-nothing baseline; every AUC is
within noise of 0.5. The kill criterion (<55% held-out accuracy — and more
damningly, zero lift over majority) is met.

## Interpretation — why this is expected, and what it does NOT say

Earnings press releases are near-uniformly upbeat corporate prose; dictionary
counts and tone classifiers measure *how the company talks*, not *how results
compare to expectations*. The market prices **surprise vs. consensus**, which
is absent from both the filing and our features. This kill does **not** say
direction is unpredictable — it says *tone-of-filing* features are dead. The
plausible next-tier features are fundamentally different: reported figures vs.
analyst consensus, guidance changes vs. prior guidance, and the market's own
early reaction. Each needs a data source we don't currently have for free at
scale (consensus estimates), so pursuing them is a *new* bet with a real
sourcing question — not a tweak to this one.

## Consequences

1. **Product claim, effective immediately:** BUY/SELL direction on earnings
   events is unsupported by any evidence we possess. The honest, *measured*
   claim is magnitude: "item-2.02 filing → 70% probability of a ≥2% move"
   (Finding 002). Ship WATCH/volatility-style signals; do not ship direction.
2. **Pipeline implication:** `impact_hypothesis` currently derives signal
   direction from FinBERT/L-M sentiment. Per this finding, that direction is
   noise dressed in a confidence score — a retail user acting on it gets a
   coin flip. This should be surfaced to Reiyyan before any user-facing launch.
3. **Bet C proceeds** (calibrated magnitude confidence) — it never depended on
   direction, and Finding 002 shows magnitude is where the real signal lives.

## Side observation logged during the session

The self-labeling flywheel has never turned: **0 of 132 signals in Postgres
have `actual_move` labels** (feedback loop only runs while the server runs;
the server almost never runs; AV quota was historically mis-enforced). The
"proprietary resolved-predictions dataset" is currently a hypothesis, not an
asset. Mitigation for 24h/1w windows: label from free daily closes (the
exp002 method) instead of burning Alpha Vantage quota — implementation task.
