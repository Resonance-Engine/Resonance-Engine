# Finding 005 — Bet D activated: direction lives in EPS surprise, asymmetrically (misses)

**Date:** 2026-07-13 · **Experiment:** `experiments/exp005_surprise_direction.py` · **Cost:** $0

## Question

Finding 003 killed tone features and hypothesized the market prices results
**vs. consensus expectations**. Yahoo's `earningsHistory` module (free,
cookie+crumb) provides actual vs. consensus EPS for the last 4 reported
quarters per ticker. Does EPS surprise predict the sign of the real
next-session abnormal return? (Live-legit: the estimate exists before the
filing; the actual is in the filing — surprise is computable the moment an
earnings 8-K drops.)

## Method

185 joins of surprise records to item-2.02 filings from the real labeled set
(join: filing date within 100 days after quarter end, nearest first).

## Results

**Naive beat/miss sign is useless — because beating is the norm.** 84.9% of
events are "beats" (estimates are managed down), so sign(surprise) scores
49.7% vs a 58.9% majority baseline. Beats are priced in.

**But outcomes are monotone in surprise size, with a hard asymmetry:**

| Surprise bucket | n | P(abn < 0) | P(abn ≤ −2%) | median abn |
|---|---|---|---|---|
| **MISS (≤ 0%)** | 28 | **78.6%** | **60.7%** | **−4.10%** |
| small beat (0–3%) | 38 | 63.2% | 39.5% | −1.17% |
| mid beat (3–10%) | 62 | 53.2% | 29.0% | −0.41% |
| big beat (>10%) | 57 | 52.6% | 29.8% | −0.23% |

Surprise% AUC for positive-vs-negative: 0.605. Misses get punished hard and
reliably; disappointing beats (<3%) also lean negative; big beats are a coin
flip. This is the classic earnings-surprise asymmetry, reproduced on our own
labeled data.

## The product claim this unlocks (first validated DIRECTIONAL claim)

> "Company missed consensus EPS → elevated probability of a negative
> market-adjusted move (observed: ~79% negative, ~61% chance of ≤−2%,
> median −4.1%)."

A rare-event, high-conviction negative alert — fires on ~15% of earnings
events. Sub-3% beats can carry a weaker "underwhelming beat" flag (63%
negative). No claim on big beats — direction there is unresolved.

## Honest caveats (why Bet D is ACTIVE, not VALIDATED)

- **n = 28 misses.** Wilson 95% CI on 78.6% is roughly 60–90%. Real but wide.
- **No time split possible** — Yahoo only serves 4 quarters back, and the
  window (~2025-07 → 2026-05) overlaps the exp004 train period.
- Consensus history depth is the binding constraint. Scale-up path, still $0:
  fetch `earningsHistory` for the full S&P 500 (~500 tickers × 4 quarters →
  ~2,000 joins, ~300 misses) and rebuild the labeled set for those tickers
  with the exp002 machinery. That gives a proper cross-sectional validation.

## Decisions

1. **Bet D ACTIVE** with the scale-up above as its validation protocol.
   Kill criterion: on the S&P 500 sample, P(negative | miss) < 65% or the
   monotone bucket structure disappears.
2. **Do not wire into the pipeline yet** — n=28 is a finding, not a product.
   Wire only after the scale-up holds, as a MISS-conditioned negative signal
   with measured probabilities (same discipline as Finding 004).
3. Live implementation sketch when validated: fetch consensus estimate for
   the ticker pre-filing (Yahoo, free), parse actual EPS from the 8-K text,
   compute surprise at signal time.
