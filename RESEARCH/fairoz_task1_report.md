# Fairoz — Task 1 Report
## Architecture Review & Backend Skeleton Implementation

**Date:** March 22, 2026
**Branch:** `fairoz`
**Author:** Fairoz Khan (AI/ML Engineer + Data Platform)

---

## Objective

Review the AgentPredict project architecture (a separate prediction platform built by a 4-person team), identify transferable patterns, and apply them to Resonance Engine's architecture. Then lay down the full backend skeleton so Phase 0 implementation can begin immediately.

---

## What Was Reviewed

**AgentPredict** is a real-time prediction platform that combines Polymarket (prediction market) and MMA (fight statistics) data, runs them through a C++ high-performance engine and a RAG orchestrator (Pinecone + Gemini Flash), and serves evidence-backed predictions to a React dashboard via WebSocket.

Key architectural elements studied:
- C++ engine with ring buffer EventStore, cursor-based subscribers, gRPC communication
- Python agents (Polymarket + MMA) ingesting data via async HTTP and emitting to engine via gRPC
- RAG orchestrator: context builder → Pinecone retriever → Gemini Flash inference → confidence verifier
- FastAPI WebSocket gateway bridging gRPC streams to the browser
- Two-column dashboard: factual event stream (left) + AI predictions with evidence (right)
- Docker Compose service separation (engine, agents, RAG, gateway, dashboard)

---

## Decisions Made

### 4 Patterns Adopted

1. **RAG-Powered Impact Hypothesis Agent (Phase 1)**
   - **What:** Embed every processed event into a vector store (Pinecone/Qdrant). When the Impact Hypothesis Agent generates a signal, it retrieves the top-K most similar historical events and their actual market outcomes to ground the prediction with evidence.
   - **Why:** Without this, the agent can only do exact-match SQL queries (same ticker + same event type). With semantic retrieval, it finds analogous patterns across different companies and sectors — e.g., "this CEO resignation resembles these 12 others across biotech." This directly strengthens Resonance's core differentiator: explainable, evidence-backed signals.

2. **`evidence[]` Array on Every Signal (Phase 1)**
   - **What:** Added an `evidence` field to the Signal schema — a list of `EvidenceItem` objects, each containing the historical event ID, summary, ticker, market outcome, cosine similarity score, and time delta.
   - **Why:** "0.78 confidence" is meaningless without showing what it's based on. The evidence array makes confidence scores trustworthy and gives users the ability to evaluate the signal's reasoning for themselves. This also addresses the PRD's explainability requirement more concretely than the original architecture.

3. **Meaningful Change Gating at Ingestion (Phase 0)**
   - **What:** A gate function that filters events before they enter the 6-agent pipeline. Checks: content hash deduplication, story clustering (same entity + event type within ±2h window), and amended filing detection.
   - **Why:** The agent pipeline is expensive (NLP inference, vector retrieval, market data lookups). Running it on duplicate stories, boilerplate 10-K copy-paste, or three rewrites of the same Reuters article wastes compute and pollutes the signal store. Borrowed from AgentPredict's approach where the Polymarket agent only emits on delta >0.01.

4. **WebSocket Gateway Separation (Phase 2)**
   - **What:** When real-time signal push is built in Phase 2, the WebSocket handling will be a separate thin service from the REST API, with its own fan-out broadcaster and cursor-based catch-up buffer for late-joining clients.
   - **Why:** REST APIs are stateless and scale horizontally. WebSocket connections are long-lived and stateful. Mixing them in one service creates operational complexity. AgentPredict's gateway pattern handles this cleanly.

### Patterns NOT Adopted

- **C++ engine** — Resonance processes news/filings at minutes-scale latency, not live market ticks. Python is the right choice.
- **gRPC** — 2-person team doesn't benefit from the codegen overhead. Internal function calls and Celery tasks are sufficient.
- **Ring buffers** — PostgreSQL handles 1k–10k events/day without breaking a sweat.
- **Service-per-agent Docker topology** — LangGraph in-process orchestration is simpler and sufficient for the current pipeline complexity.

---

## Documentation Changes

### ARCHITECTURE.md (v0.1 → v0.2)
- Updated system diagram: added vector store connected to Impact Hypothesis Agent, added "meaningful change gating" to ingestion layer, changed "WebSocket" to "WebSocket Gateway (separate service)" in API layer, added vector store to storage layer
- Added detailed section on RAG-powered Impact Hypothesis Agent: flow, vector store design (provider, embedding model, namespaces, upsert policy, retrieval parameters), `EvidenceItem` schema
- Added meaningful change gating section with code example under Ingestion Layer
- Added WebSocket Gateway section under API & UI Layer with responsibilities, message envelope format, and phasing notes
- Added Pinecone/Qdrant to storage layer and tech stack table
- Updated tech stack table: API row now shows "FastAPI + WS Gateway + Load Balancer" for Phase 3+

### SIGNAL_SPEC.md (v0.1 → v0.2)
- Updated signal JSON schema: added `evidence[]` array with 3 concrete examples, added `vector_retrieval` citation type, added `evidence_count` and `avg_similarity` to metadata
- Added new "Evidence Array (RAG-Powered)" section: EvidenceItem schema table, evidence quality rules (minimum count, similarity threshold, cross-sector bonus, recency weighting, staleness warning), 5-step retrieval flow
- Updated Signal Generation Pipeline: added embedding step, vector retrieval, evidence attachment, and post-pipeline upsert to vector store
- Added evidence guardrails to Pre-Launch checklist

### ROADMAP.md (v0.1 → v0.2)
- Phase 0: Added "Meaningful change gating" deliverable + success criterion (">30% duplicate/boilerplate filtered")
- Phase 1: Added "Vector store setup" deliverable (provision, embedding pipeline, upsert Phase 0 events, retriever implementation). Updated Impact Hypothesis Agent to be RAG-powered. Added success criteria for vector store (500+ embedded events, 3+ evidence items per retrieval)
- Phase 2: Replaced single "WebSocket" bullet with dedicated "WebSocket gateway" deliverable (separate service, cursor catch-up, fan-out)
- Updated milestone summary table to reflect changes

### New Files
- **RESEARCH/projectskeleton.txt** — Complete directory structure, Pydantic schema definitions, ownership map (who owns what, which phase), build order dependencies, verification commands, environment variable template, and notes on what was/wasn't adopted from AgentPredict
- **RESEARCH/fairoz_task1_report.md** — This file

---

## Backend Skeleton (93 Files Created)

The `backend/` directory went from empty to a fully structured skeleton with typed interfaces, clear ownership, and TODO markers on every unimplemented function.

### Fully Implemented (working code, not stubs)

| File | What it does |
|------|-------------|
| `src/models/event.py` | `Event` Pydantic model with all fields, `EventSource` enum |
| `src/models/signal.py` | `Signal` Pydantic model with `evidence[]`, `Citation` model, `SignalType` enum |
| `src/models/entity.py` | `Entity` Pydantic model (ticker, CIK, name, SIC) |
| `src/models/evidence.py` | `EvidenceItem` Pydantic model with validation (similarity 0-1) |
| `src/config.py` | `Settings` class via pydantic-settings, all env vars typed |
| `src/celery_app.py` | Celery factory with broker/backend config, autodiscovery |
| `src/ingestion/normalizer.py` | `normalize_event()` — assigns UUID, computes content hash, returns Event |
| `src/ingestion/deduplicator.py` | `is_duplicate()` — Redis hash check with 7-day TTL |
| `src/ingestion/change_gate.py` | `is_meaningful_change()` — content hash + story clustering filter |
| `src/agents/state.py` | `PipelineState` dataclass (shared typed state for LangGraph) |
| `src/agents/risk_gate.py` | `contains_blocked_language()` — regex filter for investment advice terms |
| `src/storage/database.py` | SQLAlchemy async engine + session factory |
| `src/storage/models.py` | ORM models: `EventModel`, `SignalModel`, `EntityModel` with indexes |
| `src/evaluation/metrics.py` | `f1_score()` implemented; precision/recall/Brier stubbed |

### Stubbed with Clear TODOs (NotImplementedError + phase label)

| Module | Files | Phase |
|--------|-------|-------|
| `src/ingestion/edgar/` | client.py, parser.py, tasks.py | Phase 0 |
| `src/ingestion/gdelt/` | client.py, tasks.py | Phase 2 |
| `src/ingestion/newsapi/` | client.py, tasks.py | Phase 2 |
| `src/agents/` | pipeline.py, ingestion_agent.py, entity_resolution.py, event_extraction.py, impact_hypothesis.py | Phase 0-1 |
| `src/rag/` | embedder.py, vector_store.py, retriever.py, evidence_builder.py | Phase 1 |
| `src/nlp/` | finbert.py, loughran_mcdonald.py, entity_resolver.py | Phase 0 |
| `src/storage/` | event_repo.py, signal_repo.py, entity_repo.py | Phase 0-1 |
| `src/evaluation/` | calibration.py, backtester.py, drift_detector.py, experiment_tracker.py | Phase 0-1 |
| `src/api/` | app.py, routes/*, deps.py, middleware.py | Phase 2 |
| `src/gateway/` | server.py, signal_subscriber.py, broadcaster.py, buffer.py | Phase 2 |

### Tests Written

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_normalizer.py` | 4 tests (hash determinism, UUID assignment, hash computation) | Implemented |
| `test_change_gate.py` | 5 tests (hash dedup, story clustering, different types, empty recent) | Implemented |
| `test_risk_gate.py` | 6 tests (blocks buy/sell/guaranteed/you-should, allows historical/probability) | Implemented |
| `test_metrics.py` | 5 tests (f1 perfect, zero, balanced) | Implemented |
| 7 other unit test files | TODO stubs with test case descriptions | Stubbed |
| 3 integration test files | TODO stubs | Stubbed |
| 3 API test files | pytest.skip with phase labels | Stubbed |

### Configuration Files

- `pyproject.toml` — PEP 621 metadata, pytest config (markers for API tests), ruff + mypy config
- `requirements.txt` — 20 pinned production dependencies
- `requirements-dev.txt` — Dev/test extras (pytest, ruff, mypy)
- `.env.example` — All environment variables with defaults/placeholders

---

## What's Next (Phase 0 Immediate Priorities)

1. **EDGAR ingestion** — Implement `client.py` and `parser.py` to pull and parse 8-K filings
2. **Entity resolution MVP** — Implement `entity_resolver.py` using SEC companyfacts.zip
3. **Event extraction baseline** — Implement `finbert.py` and `loughran_mcdonald.py`
4. **Evaluation harness** — Implement metrics, create labeled test set, set up experiment tracking
5. **Set up local dev environment** — `pip install -r requirements-dev.txt`, PostgreSQL + Redis via Docker Compose

---

## Memory Saved

A persistent memory record was saved summarizing the AgentPredict learnings and the 4 adopted patterns, so future conversations can reference this context without re-reading all the docs.
