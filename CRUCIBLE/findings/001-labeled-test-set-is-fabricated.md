# Finding 001 — The 100-event labeled test set is fabricated

**Date:** 2026-07-13 · **Experiment:** `experiments/exp001_verify_labels.py` · **Cost:** $0

## Question

`backend/data/labeled_test_set.json` is described in CLAUDE.md and the roadmap
as "100 events with ground truth" — the anchor asset for Phase 2 evaluation and
calibration. Are its `actual_move_pct` / `direction` labels real market
outcomes?

## Red flags that triggered the audit

- Provenance: the entire file appeared in one commit (`a7b5252`, 2026-04-10,
  AI-co-authored) alongside a confidence-formula tune. No generation script, no
  data source cited.
- Internal impossibilities: lt_001 has Apple reporting **Q3 FY2026** results on
  **2026-01-30** — a quarter that hadn't happened yet. **23 of 100 events are
  dated on weekends**, 11 of them with intraday (4h) impact windows on days the
  market was closed.

## Method

For all 100 events, fetched real daily close history (Yahoo Finance chart API,
free, cached in `data/yahoo/`) and computed the real close-to-close return over
each event's labeled window (event trading day for 4h/24h; +5 trading days for
1w). Compared labels vs reality.

## Result — labels are statistically indistinguishable from noise

| Metric | Value | Real labels would show |
|---|---|---|
| Sign agreement (all 100) | **51%** | ≥ ~80% |
| Sign agreement, real \|move\| ≥ 2% (n=45) | **58%** | ≥ ~90% |
| Pearson corr, labeled vs real magnitude | **0.058** | ≥ ~0.8 |
| Spearman corr | **0.055** | ≥ ~0.8 |

Spot checks are damning: lt_020 labels AMD 2026-02-04 as −1.5% when the real
day was **−17.3%**; lt_046 labels MSFT 2026-01-29 as +2.8% when the real day
was **−10.0%**; lt_044 labels INTC −8.2% for a week that was really **+11.4%**.

Full per-event table: `data/exp001_results.json`.

## Why this matters

- Any precision/Brier/ECE numbers ever computed against this set are
  meaningless. Nothing may be tuned or claimed on the basis of this file.
- This is the third instance of the same failure class in this codebase
  (invented EFTS mock shapes; predictions stored as ground truth): **synthetic
  data presented as observed data**. The test-mock-hygiene rule extends to
  datasets: a labeled set must carry a generation script and a verifiable
  source, or it doesn't exist.
- The event *texts* are still usable as NLP pipeline smoke inputs — but their
  labels must never be treated as market outcomes.

## Decision

1. **KILL** `labeled_test_set.json` as a ground-truth asset. Do not delete the
   file (its texts have smoke-test value; deletion is the founder's call), but
   CLAUDE.md/roadmap references to "ground truth" must be corrected.
2. **REPLACE**: build a real labeled set from real EDGAR 8-K filings + real
   Yahoo daily closes — both free, so this scales to thousands of events.
   → picked up as exp002 / Bet A in `BETS.md`.
3. Rule going forward: every dataset in `backend/data/` must have a
   generation script and cite its source, or it is treated as fiction.
