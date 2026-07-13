# Finding 002 — Real labeled set built (1,074 events); item codes predict magnitude, not direction

**Date:** 2026-07-13 · **Experiment:** `experiments/exp002_build_real_labeled_set.py` · **Cost:** $0

## What was built

`data/real_labeled_8k_set.json` — **1,074 real 8-K filings** (46 large-caps,
~July 2024 → July 2026) each labeled with real market outcomes:

- Sources: SEC EDGAR submissions API (filing dates, acceptance timestamps, item
  codes — no document fetches needed) + Yahoo daily closes, SPY-adjusted.
- Honest event-day logic: filings accepted after 16:00 ET map to the **next**
  session (EDGAR's acceptanceDateTime is Eastern wall time despite the "Z").
- Labels: `ret_1d`, `ret_5d`, market-adjusted `abn_1d`/`abn_5d`, and a
  3-class `direction` (±1% neutral band on `abn_1d`).
- Fully regenerable by script; every input cached under `data/`. This is what
  Finding 001 demanded: a dataset with a generation script and a citable source.

It is 10× the size of the fabricated set it replaces, and the same method
scales to *every* 8-K filer since ~2024 (thousands more events) for free —
price history depth (Yahoo 2y window used here) is the binding constraint, not
filings.

## Headline result: 8-K item codes stratify impact ~4× — but carry no direction

Per-item base rates over the 1,074 events (items co-occur; n ≥ 15 shown):

| Item | Meaning | n | mean \|abn_1d\| | P(\|abn_1d\| ≥ 2%) | P(positive) |
|---|---|---|---|---|---|
| 2.02 | Earnings results | 370 | **5.25%** | **70.5%** | 44% |
| 7.01 | Reg FD disclosure | 192 | 2.90% | 42.2% | 45% |
| 8.01 | Other events | 256 | 2.24% | 28.1% | 50% |
| 1.01 | Material agreement | 56 | 2.09% | 30.4% | 50% |
| 5.02 | Officer/director change | 234 | 1.73% | 27.4% | 42% |
| 2.03 | Financial obligation | 28 | 1.35% | 21.4% | 43% |
| 5.03 | Bylaws/fiscal year | 44 | 1.32% | 25.0% | 57% |
| 5.07 | Shareholder vote | 85 | **1.30%** | **22.4%** | 52% |

(9.01 is exhibits-attached, present on 77% of filings — not informative alone.)

Two conclusions:

1. **Magnitude is predictable from metadata alone.** An item-2.02 filing is
   ~3× more likely to produce a ≥2% abnormal move than a 5.07. A signal system
   that only knew item codes would already beat an uninformed prior at
   answering "is this filing worth watching?" — that's the mandatory baseline
   any ML in this product must now beat.
2. **Direction is NOT in the metadata.** P(positive) hovers at 42–57% across
   every item type. Direction, if recoverable at all, lives in the filing
   *content* (NLP), not the filing *type*. Untested so far — that is Bet B.

## Product implications

- The defensible near-term claim is **"this filing matters"** (magnitude /
  WATCH-style alerts), not "buy/sell". Confidence for magnitude claims can be
  anchored to these measured base rates *today*, replacing part of the
  hand-set formula with observed frequencies.
- The change gate / risk gate should treat item codes as first-class evidence:
  a 5.07-only 8-K is ~78% likely to be noise; a 2.02 is 70% likely to matter.
- The parser already extracts 8-K item codes (post-`51a2081`) — wiring base
  rates into `impact_hypothesis` is cheap.

## Decisions

1. **SCALE** the real-label builder: it becomes the evaluation backbone and
   the seed of the historical evidence corpus (charter question 2).
2. **ADOPT** item-code base rates as the zero-ML baseline and as an evidence
   enrichment source in the pipeline (implementation task, not research).
3. **OPEN Bet B**: does filing *text* (FinBERT / L-M sentiment on the real
   documents) predict the *sign* of `abn_1d` better than the ~46% base rate?
   EDGAR document fetches are free; FinBERT runs locally — still $0.
