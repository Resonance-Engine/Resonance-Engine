# Finding 004 — Bet C VALIDATED: calibrated magnitude confidence from measured features

**Date:** 2026-07-13 · **Experiment:** `exp004_calibrated_magnitude.py` · **Cost:** $0

## Question

Can we produce a *calibrated* probability for the claim that actually matters
(Finding 002/003): **"this 8-K will move the stock ≥2% (SPY-adjusted) in its
first session"** — beating a plain base-rate lookup, with honest metrics?

## Method

1,022 events from the real labeled set with ≥20 prior sessions of price data.
Time split: train ≤ 2025-12-31 (n=684), test 2026 (n=338, positive rate 44.1%).
Two models, evaluated with the repo's own `src/evaluation` code (its first use
on real data ever):

- **Base-rate table** (the bar): train-frequency by most-impactful item
  present — 2.02: 67.5%, 7.01: 31.8%, 8.01/1.01: 16.8%, other: 19.5%.
- **Logistic regression** (pure numpy): item indicators + trailing 20-session
  realized volatility (z-scored on train) + after-hours flag.

## Result — logistic beats the table on every metric (held-out 2026)

| Model | Brier ↓ | Log loss ↓ | ECE ↓ | AUC ↑ |
|---|---|---|---|---|
| Uninformed constant (0.441) | 0.2465 | — | — | 0.500 |
| Base-rate table | 0.2161 | 0.630 | 0.093 | 0.692 |
| **Logistic (items + vol)** | **0.2095** | **0.614** | **0.085** | **0.727** |

Weights make economic sense: item 2.02 dominates (+1.80), trailing volatility
adds real lift (+0.40 per σ — volatile names move more on news), routine items
(8.01, 5.02) push probability down. After-hours timing adds nothing (0.02).

## What this means

- **The product's core number can now be real.** Replace the hand-set
  `0.45 + 0.35·sim` confidence with a measured P(≥2% move): a 10-line
  scoring function (weights above) plus the base-rate table as fallback.
  ECE ≈ 8.5% means "our 70% is roughly a 70%" — already defensible, and
  Platt/isotonic on accumulating live labels will tighten it.
- **The moat compounds for free**: every additional labeled event (exp002
  scales to all 8-K filers) re-fits and tightens this model at $0.
- Ceiling not reached: sector, market-cap, earnings-calendar features, and
  filing-length/novelty are all untried. AUC 0.727 is a floor, not a limit.

## Decisions

1. **VALIDATED → implementation task**: wire magnitude confidence into
   `impact_hypothesis` (weights + table are in `data/exp004_results.json`).
   Signal semantics change: confidence = P(material move), direction shown
   only as unvalidated context until Bet D lands.
2. Refit protocol: retrain on all data whenever the labeled set grows ~20%,
   always time-split, always report Brier/ECE vs the table.
3. Session arc complete: Finding 002 (magnitude is predictable) →
   Finding 003 (direction is not, with current features) → Finding 004
   (magnitude probability, calibrated). This IS the evidence-backed product.
