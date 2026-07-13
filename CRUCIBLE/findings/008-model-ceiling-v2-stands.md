# Finding 008 — Bet F: v2 stands; sector missed the ship bar by 0.0005 AUC

**Date:** 2026-07-13 · **Experiment:** `experiments/exp008_model_ceiling.py` · **Cost:** $0

## Question

Do sector (2-digit SIC), size/liquidity (log 20-day dollar volume), filing
novelty (days since last 8-K), item count, and a 2.02×vol interaction beat the
shipped v2 magnitude model? Pre-registered ship bar: **≥ +0.010 AUC AND better
Brier** on the identical time split (test n=3,616, 2026).

## Primary result (target |abn_1d| ≥ 2%) — cumulative ablation

| Feature set | Brier | AUC | ECE |
|---|---|---|---|
| v2 reproduction (items + vol) | 0.2178 | 0.7152 | 0.081 |
| + n_items, 2.02×vol | 0.2172 | 0.717 | 0.081 |
| + novelty | 0.2171 | 0.717 | 0.082 |
| + size (dollar volume) | 0.2167 | 0.716 | 0.078 |
| **+ sector (top-10 SIC)** | **0.2149** | **0.7247** | 0.085 |

Sector is the only feature that moves the needle. At full precision the gain
is **+0.00955 AUC** — under the +0.010 bar. Brier improves but the criterion
was conjunctive. **Not shipped.** (Rounded to 3 decimals it looked like
exactly +0.010 — adjudicating at full precision matters; a marginal "ship"
would have added a production SIC-lookup dependency for a sub-threshold gain.)

Interactions, novelty, and size are ~flat: the market doesn't care how often
a company files or how big it is, once you know the item codes and its
volatility. Useful negative — those features never need building.

## Secondary results (report-only, each is a candidate future bet)

1. **Big moves are much more predictable.** Target |abn_1d| ≥ 5%: AUC
   **0.801** with v2 features, **0.826** with sector, ECE ~0.02. A
   high-conviction "major impact" tier (rarer, sharper) is sitting in the
   data — stronger than the shipped ≥2% product surface (0.715). Candidate
   Bet G: two-tier signals — P(≥2%) and P(≥5%) with its own pre-registered
   bar and its own risk-gate threshold.
2. **The signal is a next-session phenomenon.** Target |abn_5d| ≥ 2%: AUC
   drops to ~0.62 for every feature set. Predictability decays fast past the
   first session — 8-K impact windows should stay short, and any future
   "1-week outlook" claim currently has no evidential basis.
3. ≥1% threshold is mushy (AUC 0.65) — 1% is inside normal daily noise;
   2% was the right product line.

## Decisions

1. **Bet F closed, killed at the bar.** v2 remains the production model.
   Sector goes on the shelf as "real but sub-threshold" — worth retrying only
   combined with something else (e.g., in a Bet G two-tier model, where its
   ≥5% gain was 2.5× larger).
2. Candidate Bet G (two-tier ≥5% alert, AUC ~0.80+) added to the register.
3. Impact-window guidance for the product: keep 8-K windows at 4h/24h;
   do not extend to 1w without new evidence.
