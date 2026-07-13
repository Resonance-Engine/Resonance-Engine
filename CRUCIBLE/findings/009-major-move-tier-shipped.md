# Finding 009 — Bet G VALIDATED + SHIPPED: the major-move tier

**Date:** 2026-07-13 · **Experiment:** `experiments/exp009_major_move_tier.py` · **Cost:** $0

## Question

Can a second calibrated probability — P(|SPY-adjusted move| ≥ 5%) — support a
high-conviction "major impact" tier above the shipped ≥2% confidence?
Pre-registered ship criteria: precision ≥ 0.40 at the P ≥ 0.40 alert line with
≥ 100 test alerts; ECE ≤ 0.04; variant by test Brier with a <0.002 near-tie
rule favoring the simpler model.

## Result — all criteria pass

Chosen model: **items + trailing vol + 2-digit-SIC sector** (Brier 0.1076,
a dead tie with the full feature stack at 0.1074 → near-tie rule picks the
simpler, production-feasible variant). Held-out 2026 (n=3,616, base rate 16.2%):

| Metric | Value |
|---|---|
| AUC | 0.824 |
| Brier | 0.108 |
| ECE | 0.024 |
| Precision @ P ≥ 0.40 | **0.503** (3.1× base rate), 336 alerts |
| Precision @ P ≥ 0.50 | 0.568, 81 alerts |
| Precision @ P ≥ 0.30 | 0.457, 806 alerts, recall 0.63 |

A methodological note: exp009's first pass "chose" the full cumulative feature
stack (an exp008 design wart — its specs are cumulative, so "+sector" silently
included novelty/size features that aren't available live). The registered
comparison was items+vol vs +sector, so that exact variant was fit: it tied
the full stack (Δ Brier 0.0002), confirming novelty/size add nothing at ≥5%
either. Sector, however, genuinely earns its keep here (AUC 0.801 → 0.824) —
software (SIC 73) filings run hot, utilities (49) and banks (60) run cold.

## Shipped

- `src/agents/magnitude.py`: `major_move_probability(item_codes, trailing_vol,
  sic_code)` — second calibrated head, weights + provenance; unknown/missing
  SIC degrades gracefully to the items+vol model.
- `impact_hypothesis`: computes it for every calibrated 8-K, returns
  `major_move_probability` in state (new `PipelineState` field); rationale
  gains a "MAJOR IMPACT TIER" line when P ≥ 0.40, phrased with the measured
  precision ("proved major roughly half the time, ~3× base rate").
- Stored in signal `metadata.major_move_probability` for every signal —
  the feedback loop can score this tier's live calibration later.
- 286 tests passing (5 new), ruff clean; verified live through the pipeline
  with graceful SIC degradation.

## Product shape after today

Every 8-K signal now carries two measured probabilities:
**P(≥2% move)** = the confidence (risk-gated at 0.40), and
**P(≥5% move)** = the major tier (called out at ≥0.40, precision ~0.50).
Direction remains explicitly unvalidated context (F003/F006).

## Follow-ups

- Live trailing vol would sharpen both heads (vol currently None in
  production → z=0); a free daily-close source for the pipeline is the
  missing piece — candidate implementation task, not a research bet.
- The feedback loop should verify live precision of the ≥0.40 tier once
  signals accumulate (target: ~0.50, alert if <0.40 — that would mean
  live drift from the backtest).
