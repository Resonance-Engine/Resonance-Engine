# Finding 007 — Bet E resolved: shipped model survives out-of-universe; v2 refit shipped

**Date:** 2026-07-13 · **Experiment:** `experiments/exp007_f004_out_of_universe.py` · **Cost:** $0

## Question

The production magnitude model (F004) was fit on 46 mega-caps. Finding 006
proved mega-cap samples can flatter effect sizes. Is the confidence we emit
miscalibrated for the other 456 S&P 500 names? Pre-registered kill: shipped
Brier worse than the base-rate table out-of-universe → production incident.

## Result 1 — no incident: v1 generalizes

| Sample | Shipped v1 Brier | Table Brier | Shipped AUC | Table AUC |
|---|---|---|---|---|
| 456 never-seen tickers (n=11,329) | **0.1932** | 0.1946 | **0.739** | 0.719 |
| Same, 2026 only (n=3,284) | **0.2219** | 0.2280 | **0.704** | 0.669 |

The mega-cap-fit weights beat the base-rate table everywhere tested. The
item-code → magnitude structure is universe-stable (unlike the miss-alert).

## Result 2 — the 12× refit is better, so it shipped as v2

Refit on the S&P 500 set (train n=8,718 ≤ 2025-12-31; test n=3,616 in 2026):

| Model | Test Brier | Test AUC | Test ECE |
|---|---|---|---|
| Shipped v1 | 0.2208 | 0.706 | 0.088 |
| **Refit v2** | **0.2178** | **0.715** | **0.081** |

Weight shifts worth knowing: 5.07 (shareholder votes) got *more* negative
(−0.41 vs −0.11) and 5.02 (officer changes) went to ~0 — at scale, votes are
the noise and exec changes are neutral, not the other way around. After-hours
stayed useless and is now weight 0.

**Shipped**: `src/agents/magnitude.py` updated to v2 weights + new vol
standardization; tests updated to the published v2 numbers; 281 passing.

## Decisions

1. Bet E closed: **no miscalibration incident**; v2 weights in production.
2. The refit protocol worked exactly as designed on its first trigger
   (labeled set grew 12×, refit, time-split, beat the old model, shipped).
3. Remaining ceiling for a future bet: sector/market-cap features, multiple
   thresholds (1%/5%), and 5-day horizon — none tried yet; AUC 0.715 on 3,616
   test events is the number to beat.
