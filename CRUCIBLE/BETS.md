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

### Bet D — Direction from surprise, not tone — **ACTIVE (probe positive)**
**Finding 005:** Yahoo `earningsHistory` (free) solved the sourcing question.
On 185 real joins: beats are priced in (85% of events, no signal), but
**misses are punished** — P(negative | miss) = 78.6%, P(≤−2%) = 60.7%,
median −4.1%, monotone across surprise buckets, AUC 0.605. First recoverable
directional signal, but n(miss)=28 and no time split possible yet.
**Validation protocol:** scale to the S&P 500 (~2,000 joins, ~300 misses) —
fetch earningsHistory for ~500 tickers + rebuild labels with exp002 machinery.
**Kill criterion:** P(negative | miss) < 65% on the scaled sample, or the
monotone bucket structure disappears.
**Not wired into the pipeline until validated** — same discipline as Bet C.
Live sketch when it passes: consensus fetched pre-filing, actual EPS parsed
from the 8-K, surprise computed at signal time (no lookahead).

## Killed

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
