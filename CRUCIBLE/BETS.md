# Bets Register

Max three active. Each bet: falsifiable question, kill criterion, cost ceiling,
and what "materially forward" means if it wins. Update this file every session.

---

## Active

### Bet A — Historical backfill is the data moat
**Question:** Can we backfill years of real 8-K events (text + real outcomes)
into the evidence corpus so that day-one signals cite dozens of real
precedents instead of zero?
**Status:** DERISKED, ready to scale. exp002 proved the labeling half: 1,074
real labeled events from 46 tickers at $0. Remaining: (1) extend price history
beyond Yahoo's 2y chart window (or accept 2y), (2) fetch + parse filing texts
(free EDGAR), (3) embed into Pinecone — **blocked on the Pinecone key (401,
user action)** — or decide embeddings-in-Postgres instead.
**Kill criterion:** none for labeling (already works). Embedding backfill dies
if OpenAI embedding cost for the corpus exceeds ~$20 (est. is far below).
**Materially forward:** evidence[] stops being empty; the "across N similar
events, median move X%" product claim becomes real on day one.

### Bet C — Calibrated magnitude confidence — **VALIDATED 2026-07-13**
Finding 004: logistic model (item codes + trailing 20-session vol) beats the
base-rate table on held-out 2026 — Brier 0.210 vs 0.216 (uninformed 0.247),
AUC 0.727 vs 0.692, ECE 8.5%. **IMPLEMENTED 2026-07-13** (`src/agents/magnitude.py`, wired into
`impact_hypothesis` + scheduler passes `filing_metadata`; 12 new tests, 281
passing; verified live through the pipeline — earnings 8-K → 0.696 passes the
risk gate, routine 5.07 → 0.219 correctly rejected). Confidence for 8-Ks is
now the measured P(|abn_1d| ≥ 2%); uncertainty text states magnitude-not-
direction semantics per Finding 003. Refit whenever the labeled set grows
~20%, always time-split, always report Brier/ECE vs the table.
**Volume note:** routine filings (8.01/5.02/5.07-only) now honestly score
below the 0.40 risk gate and get rejected — signal volume drops, quality
rises. Threshold is Reiyyan's product knob.

---

### Bet E — F004 out-of-universe — **RESOLVED 2026-07-13, v2 SHIPPED**
Finding 007: no miscalibration incident — v1 weights beat the base-rate table
on 11,329 never-seen-ticker events (Brier 0.193 vs 0.195, AUC 0.739 vs 0.719).
The 12× refit tested better (0.2178/0.715/ECE 8.1% vs 0.2208/0.706/8.8%) and
shipped as **v2 weights in `src/agents/magnitude.py`**. Refit protocol fired
correctly on its first trigger. Next ceiling: sector/market-cap features,
1%/5% thresholds, 5-day horizon — beat AUC 0.715 (n=3,616).

## Candidate (not yet active)

### Bet G — Two-tier signals: a high-conviction P(≥5%) alert
Finding 008 secondary: |abn_1d| ≥ 5% is far more predictable than the shipped
≥2% target — AUC 0.801 (v2 features) / 0.826 (with sector), ECE ~0.02. A
rarer, sharper "major impact expected" tier could sit above the current
signal. Needs fresh pre-registration (bar, gate threshold, rationale text)
before any wiring. Sector features earn their keep here (gain 2.5× larger
than at ≥2%).

## Killed

### ~~Bet F — model ceiling (sector/size/novelty features)~~ (2026-07-13)
Finding 008: sector was the only feature with signal; at full precision it
gained +0.00955 AUC vs the pre-registered ≥ +0.010 bar → not shipped, v2
stands. Size, novelty, item-count, interactions ≈ flat (never need building).
Secondaries: ≥5% target much stronger (→ Bet G); 5-day horizon weak (AUC
0.62) — 8-K impact windows stay short; 1% threshold is noise.

### ~~Bet D — EPS-miss directional alert~~ (2026-07-13)
Finding 006: pre-registered S&P 500 validation (13,022 events, 350 misses)
came in at P(negative | miss) = 60.9% vs the 65% bar. The probe's 78.6%
(n=28) was small-sample optimism. Monotone structure held — surprise is a
real *feature* (~10-19pp off coin-flip at the tails) but not a standalone
high-conviction alert. Product stays magnitude-first. Follow-up slices
(deep miss, guidance cuts, cap interaction) require fresh pre-registration.

### ~~Bet B — direction from filing-text sentiment~~ (2026-07-13)
Finding 003: on 370 real earnings 8-Ks, time-split, neither L-M (55.9% acc,
AUC 0.52) nor FinBERT (46.1% acc, AUC 0.45) beats the 58.8% majority baseline.
Tone features are dead. **Immediate product consequence: the pipeline's
BUY/SELL direction (derived from sentiment) is a coin flip — flag to Reiyyan;
ship magnitude/WATCH claims only.**

### ~~The 100-event labeled test set as ground truth~~ (2026-07-13)
Finding 001: labels are fabricated (51% sign agreement with reality, r=0.06).
Never evaluate or tune against it. Replaced by `data/real_labeled_8k_set.json`.

---

## Blocked / user actions

- **Pinecone key 401s** — blocks the embedding half of Bet A and the live RAG
  evidence-loop proof. Alternative if renewal stays broken: store embeddings in
  Postgres (pgvector plan is shelved but scoped).
- **132 orphan signal rows** in Postgres (grew from 129) — keep/purge decision.
  Note: their labels came from the feedback loop, so any that are labeled are
  real data points; consider keeping labeled ones for Bet C.
