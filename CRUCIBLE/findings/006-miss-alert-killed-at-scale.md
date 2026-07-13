# Finding 006 — Bet D KILLED at scale: the miss-alert doesn't clear the shipping bar

**Date:** 2026-07-13 · **Experiment:** `experiments/exp006_sp500_scaleup.py` · **Cost:** $0

## What ran

The pre-registered validation of Finding 005: rebuilt the real-label machinery
for the full S&P 500 (**13,022 labeled 8-K events**, 502 tickers), joined
1,976 EPS-surprise records, re-measured the bucket structure on 350 misses
(12.5× the probe's n=28).

## Result — the effect is real but shrank below the pre-registered bar

| Surprise bucket | n | P(negative) | P(≤−2%) | mean abn | median |
|---|---|---|---|---|---|
| MISS (≤0%) | 350 | **60.9%** | 47.1% | −2.70% | −1.57% |
| small beat (0–3%) | 405 | 51.9% | 38.0% | −0.49% | −0.22% |
| mid beat (3–10%) | 658 | 47.9% | 30.9% | +0.56% | +0.15% |
| big beat (>10%) | 563 | 41.6% | 26.6% | +2.05% | +1.40% |

Kill criterion was **P(negative | miss) ≥ 65%**; observed 60.9%. Killed.
The probe's 78.6% was small-sample optimism (n=28, mega-caps only, one year).

## What survives the kill — worth being precise

- **The monotone structure held perfectly** (60.9 → 51.9 → 47.9 → 41.6), and
  mean moves are strongly ordered (−2.7% → +2.05%). Surprise direction is
  *real* — 60.9% vs 50% on n=350 is far beyond chance — it's just not a
  high-conviction retail alert. A "79% conviction" product claim would have
  been a lie at scale; that's exactly what pre-registration is for.
- At S&P 500 scale, **big beats now lean positive** (58.4% positive,
  mean +2.05%) — symmetric weak signal at both tails that the mega-cap
  probe couldn't see.
- Surprise remains a legitimate *feature* for future models (it moves the
  needle ~10-19pp off coin-flip at the tails) — it's just not a standalone
  signal at product conviction levels.

## Candidate follow-ups (would need fresh pre-registration — NOT post-hoc rescues)

- Deep-miss subgroup (surprise < −5%), revenue miss + EPS miss combined,
  guidance-cut detection in the filing text, market-cap interaction
  (the probe hints large caps punish misses harder).
- Any of these must state its kill bar BEFORE looking at the sliced data.

## By-product: the dataset just got 12× bigger

`data/sp500_labeled_8k_set.json` — 13,022 real labeled events across 502
tickers is now the largest asset in the company. Immediate uses:
1. **Refit the F004 magnitude model** on 13k events (vs 1,022) with sector /
   market-cap features — more power, and validates F004 out-of-universe.
2. Bet A's evidence corpus: these are exactly the events to embed once
   Pinecone unblocks.

## Decisions

1. **Bet D KILLED as a standalone directional product claim.** Nothing gets
   wired into the pipeline. The product remains magnitude-first (F004).
2. Surprise-as-feature and the follow-up slices go to the candidate list,
   each requiring pre-registered criteria.
3. Next lap by leverage: **refit F004 on the 13k-event set** (out-of-universe
   validation + sector features) — it strengthens the claim we already ship.
