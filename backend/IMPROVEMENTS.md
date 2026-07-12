# Backend Improvement Pass — 2026-07-12 (branch `fairoz`)

Expert-level survey + fixes across the entire backend. Four parallel review
agents swept ingestion/scheduler, NLP/agents, RAG/storage, and
API/gateway/evaluation; findings were ranked by leverage and the top items
implemented. Baseline: 209 tests passing, 13 ruff errors, 228 mypy errors.
**Result: 262 tests passing, ruff clean, all critical correctness bugs fixed.**

## Wave 1 — Silent correctness bugs corrupting every signal

### 1. Cross-namespace evidence merge was broken (CRITICAL)
- **Where:** `src/agents/impact_hypothesis.py` (old lines 88/96) → now `src/rag/retriever.py::retrieve_similar_events_multi`
- **Bug:** merge deduped on `r.get("event_id")` and sorted on `similarity_score` — keys that don't exist in retrieval results (`{"id", "score", "metadata"}`). Every result got `eid=""`, so all but the FIRST result were dropped as "duplicates" and the sort was a no-op. At most 1 evidence item ever survived; the 3+-evidence confidence bracket (0.45+0.35·sim, cap 85%) almost never fired. Commit 43e9458 claimed to fix cross-namespace retrieval but left this.
- **Fix:** new `retrieve_similar_events_multi()` in the retriever — embeds the query ONCE (was 3× per event, one per namespace = 3× OpenAI cost), queries each namespace with the precomputed vector, merges on `id`, sorts on `score`. Agent now calls it.
- **Tests:** `tests/unit/test_retriever.py` (13 tests, was an empty stub) — merge survival, dedupe, sort order, single-embed, namespace failure tolerance.

### 2. Predictions stored as ground truth — RAG self-contamination (CRITICAL)
- **Where:** `src/agents/pipeline.py::_store_signal_node`
- **Bug:** wrote `"actual_move": state.get("predicted_move")` into Pinecone metadata. `evidence_builder._get_outcome` reads `actual_move` as the OBSERVED historical outcome and formats it as "+2.0% move" evidence for future predictions → the model cites its own guesses as ground truth (self-reinforcing confidence inflation).
- **Fix:** metadata key renamed to `predicted_move` (ignored by evidence builder). Real outcomes flow via the existing signal-repo fallback in `_get_outcome`, populated by the feedback loop. Pinecone is at 0 vectors, so no legacy contamination exists.
- **Tests:** `tests/unit/test_pipeline_store.py` (4 tests, new file).

### 3. Feedback-loop labels were corrupt (3 bugs) (CRITICAL for evaluation)
- **Where:** `src/ingestion/market_data.py::compute_post_event_returns`
- **Bugs:** (a) 1h/4h windows computed from DAILY bars — silently measured ~next-day moves; (b) post-price selection loop actually returned the bar BEFORE the window end, not at/after; (c) pre-price used the event day's own daily bar, whose close happens AFTER the event — lookahead bias.
- **Fix:** rewritten as `_select_pre_price` (daily series: last bar from a PRIOR date; intraday: last bar ≤ event) + `_select_post_price` (first bar ≥ window end) + `_compute_window_returns`. Short windows (1h/4h) now use 60-min intraday bars; if intraday is unavailable they're SKIPPED (retried later), never mislabeled from daily bars.
- **Tests:** `tests/unit/test_market_data.py` (19 tests, new file).

### 4. Alpha Vantage quota never enforced + throttle response undetected
- **Where:** `src/ingestion/market_data.py`
- **Bug:** QuotaTracker existed but nothing called `.allow()` — the feedback loop could fire 50 AV calls/run every 30 min against a 25/day free tier. Worse, AV signals throttling with HTTP 200 + `{"Note": ...}` body, which parsed as "no data" → labeling silently died.
- **Fix:** new `_alpha_vantage_get()` helper: quota-gated (`alpha_vantage_quota.allow()`), detects `Note`/`Information`/`Error Message` bodies and logs loudly. Finnhub quota also now enforced in `fetch_quote_finnhub`. `label_expired_signals` default batch 50→10; scheduler `FEEDBACK_BATCH` 50→10.

## Wave 2 — Security & robustness

### 5. WebSocket `/ws` had ZERO authentication (HIGH — data exfiltration)
- **Where:** `src/gateway/server.py`
- **Bug:** any client could connect and immediately receive the catch-up buffer (last 50 signals) + live stream — the exact data the REST API gates behind bearer tokens.
- **Fix:** handshake now requires `?token=<AUTH_TOKEN>` (browsers can't set WS headers), validated via new constant-time `validate_token()` in `src/api/deps.py` (also fixes the timing-unsafe compares in `get_current_user`/`get_optional_user`). Invalid → close 1008. Frontend `connectSignalWS` updated to append the stored token.
- **Tests:** `tests/unit/test_gateway.py` (8 tests, first gateway coverage ever).

### 6. Broadcaster head-of-line blocking
- **Where:** `src/gateway/broadcaster.py::broadcast`
- **Bug:** held the asyncio lock across every `await ws.send_text()` serially — one stalled client delayed all others AND blocked connect/disconnect.
- **Fix:** snapshot clients under the lock, send concurrently outside it (`asyncio.gather`), 5s `SEND_TIMEOUT` per send; timed-out/dead clients discarded under lock afterwards.

### 7. Entity resolution substring false positives
- **Where:** `src/nlp/entity_resolver.py`
- **Bug:** `if name.lower() in text_lower` — "metal supply"→META, "targeted cost reductions"→TGT, "intelligence"→INTC, "visation"→V. Could misattribute `primary_ticker` for the whole signal.
- **Fix:** precompiled word-boundary regexes (`\bMeta\b`), case-SENSITIVE (lowercase "target"/"visa"/"apple" are common English).
- **Tests:** 4 regression tests in `test_entity_resolver.py`.

### 8. Dedup dropped events on pipeline failure
- **Where:** `src/ingestion/deduplicator.py`, `src/scheduler.py`
- **Bug:** hash marked "seen" BEFORE processing (7-day TTL) — a pipeline crash permanently swallowed the event; also EXISTS-then-SETEX race.
- **Fix:** claim/release semantics — atomic `SET NX EX` claim before processing, `release()` on pipeline failure so later polls retry. `is_duplicate` kept as back-compat alias. Both scheduler paths (EDGAR + news) wired; dedup errors now log warnings instead of silent `pass`.
- **Tests:** `tests/unit/test_deduplicator.py` (7 tests, was an empty stub).

### 9. Risk gate's low-confidence rejection was unreachable
- **Where:** `src/agents/impact_hypothesis.py`
- **Bug:** zero-evidence confidence had a hard floor of 0.42; risk gate rejects <0.40 — the "reject low confidence" guarantee could never fire in production.
- **Fix:** zero-evidence formula now `min(0.42 + (raw_confidence − 0.5) × 0.26, 0.55)` — typical extraction (raw 0.5) still anchors at 0.42, weak extractions (raw <~0.42) fall below the gate. Deliberately NOT harsher: with Pinecone at 0 vectors every signal starts evidence-free; removing the floor entirely would have silently stopped all signal production.
- **Tests:** 3 regression tests in `test_impact_hypothesis.py`.

### 10. Tests were spending REAL API credits (discovered during Wave 2)
- **Where:** `tests/conftest.py`
- **Bug:** live keys in `.env` meant any test reaching `embed_text` made real OpenAI calls (agent + integration tests did, every run). Suite ran ~8–10s; after the fix it runs ~0.9s — that delta was network time on paid APIs.
- **Fix:** autouse fixture blanks all paid-API keys (OpenAI, Gemini, Pinecone, AV, Finnhub, NewsAPI) and resets the embedder's cached client unless the test is marked `api`.

## Wave 3 — Performance, deprecations, dead code

### 11. FinBERT: event-loop blocking + racy lazy load
- `src/nlp/finbert.py`: double-checked-locking around the ~400MB model load (two concurrent first calls both loaded it); new `classify_sentiment_async()` runs inference via `asyncio.to_thread`; `event_extraction_agent` converted to async and uses it (a sync forward pass blocked every concurrent pipeline + WS heartbeat). Also `return_all_scores=True` → `top_k=None` (deprecated flag) with shape normalization.

### 12. Change gate was completely dead
- `normalize_event` never populated `event_type`/`entities` (both computed in the EDGAR path then dropped into metadata only) → story clustering could never match. Now accepts and passes both.
- `recent_events` was rebuilt empty every 5-min poll cycle vs a 2h cluster window → clustering could never span cycles. Scheduler now keeps `_recent_events_by_form` across cycles, pruned to the cluster window.

### 13. Live scheduler decoupled from dead Celery
- `filing_to_event` moved to new Celery-free `src/ingestion/edgar/events.py`; scheduler imports from there. Previously removing Celery from requirements would have silently killed EDGAR polling (import error caught by the loop's broad except, logged as generic "loop error" every 5 min). `tasks.py` keeps a back-compat alias.

### 14. Timezone-correct timestamps
- `datetime.utcnow()` (deprecated, tz-naive, written into `timezone=True` columns) → `datetime.now(timezone.utc)` in `src/models/signal.py`, `src/storage/models.py`, `src/ingestion/normalizer.py`.

### 15. Hygiene
- All 13 baseline ruff errors fixed (unused imports/vars, ambiguous `l`); `ruff check src/` is clean.
- `/pipeline/run` 500s no longer echo raw exception strings to clients.
- CLAUDE.md corrected: gateway/news/scheduler are implemented (not "stubs"), Phase 2 items 3–5 marked done, Python 3.14 runtime noted, test-suite documentation updated.

## Known issues deliberately NOT addressed (ranked backlog)

1. **EDGAR EFTS response parsing** (`edgar/client.py::fetch_recent_filings`) — likely reads wrong `_source` fields (`entity_id`/`adsh` vs real `ciks`/`display_names`/`_id`). Needs verification against the live API before changing. The "falling back to submissions API" log message is also a lie (no fallback exists).
2. **EDGAR rate limiter** — `Semaphore(10)` + 0.12s sleep allows ~80 req/s bursts if callers ever go concurrent (currently sequential, so latent). Should be a token bucket or `Semaphore(1)`.
3. **Repo transaction boundaries** — write helpers `commit()` caller-supplied sessions; atomic multi-write transactions are impossible. Needs `flush`-when-external-session pattern.
4. **Postgres↔Pinecone orphan risk** — no reconciliation sweep; `reembed_pinecone.py` is manual.
5. **Backtester PBO** — claims CSCV, implements contiguous sliding half-splits (weak overfitting gate). Needs `itertools.combinations` partitioning. Median also takes upper element for even n.
6. **QuotaTracker** — in-memory only (per-process; multiple uvicorn workers each get the full quota), racy read-modify-write, `==` threshold warning can be skipped.
7. **mypy strict** — 228 errors outstanding; `strict` in pyproject is aspirational.
8. **Loughran-McDonald negation** — "not profitable" scores positive; hyphenated terms never match.
9. **SEC ticker cache never expires** — no TTL/refresh; ticker renames/delistings go stale.
10. **`recall_at_k`** ignores `k` (it's plain recall); Platt scaling has no convergence check; drift p-value is a rough normal approximation.
11. **Market holidays** — scheduler polls on US market holidays (weekday check only).
12. **Health endpoint** — unauthenticated, exposes DB status + quota posture.

## Test suite
- 209 → **262 passed** (5 skipped, unchanged). New/filled files: `test_retriever.py`, `test_market_data.py`, `test_pipeline_store.py`, `test_gateway.py`, `test_deduplicator.py`; extended: `test_entity_resolver.py`, `test_impact_hypothesis.py`.
- Suite runtime 8–10s → ~0.9s (no more accidental live API calls).
- `ruff check src/`: clean (was 13 errors).
