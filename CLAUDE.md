# Resonance Engine

Financial intelligence platform that transforms unstructured SEC filings and news into structured, actionable signals for retail traders.

## Who Is Working

- **Fairoz Khan** (`fairoz` branch) — AI/ML Engineer, Data Scientist, Data Engineer. Owns the entire backend: ingestion, NLP, RAG, agents, storage, evaluation.
- **Reiyyan Zafar** — Founder, Product & Architecture Lead. Owns frontend, product decisions, architecture sign-off.
- `main` branch requires 1 approving review before merge.

## Current Phase: Phase 0 COMPLETE → Phase 1 COMPLETE → Phase 2 (User-Facing MVP)

**Phase 0 Goal (achieved):** Prove the core pipeline works end-to-end with EDGAR filings.
**Phase 1 Goal (achieved):** Generate evidence-backed signals via LangGraph agent pipeline + RAG.

**What's implemented (working code, 195 tests passing):**
- Pydantic models: `src/models/` (event, signal, entity, evidence)
- SQLAlchemy ORM: `src/storage/models.py` (EventModel, SignalModel, EntityModel with indexes)
- Config: `src/config.py` (Pydantic Settings, all env vars)
- Ingestion utilities: `src/ingestion/normalizer.py`, `src/ingestion/deduplicator.py`, `src/ingestion/change_gate.py`
- EDGAR client: `src/ingestion/edgar/client.py` (5 async functions, rate-limited)
- EDGAR parser: `src/ingestion/edgar/parser.py` (8-K, 10-K, Form 4)
- EDGAR Celery task: `src/ingestion/edgar/tasks.py` (full pipeline with entity resolution)
- Entity resolver: `src/nlp/entity_resolver.py` (SEC data, exact + fuzzy + free-text)
- FinBERT sentiment: `src/nlp/finbert.py` (lazy-loaded, single + batch)
- Loughran-McDonald: `src/nlp/loughran_mcdonald.py` (555+ words, 5 categories)
- Event repo: `src/storage/event_repo.py` (async CRUD, idempotent insert)
- Signal repo: `src/storage/signal_repo.py` (async CRUD, update_actual_move)
- Entity repo: `src/storage/entity_repo.py` (upsert, get by ticker/CIK, list, count)
- Risk gate regex: `src/agents/risk_gate.py`
- Evaluation metrics: `src/evaluation/metrics.py` (precision@k, recall@k, f1, brier, log_loss)
- Calibration: `src/evaluation/calibration.py` (ECE, MCE, reliability diagram, Platt scaling)
- Backtester: `src/evaluation/backtester.py` (look-ahead bias, survivorship bias, PBO)
- Drift detector: `src/evaluation/drift_detector.py` (Welch's t-test, accuracy drop)
- Experiment tracker: `src/evaluation/experiment_tracker.py` (JSON-file, log/list/compare)
- Celery Beat: `src/celery_app.py` (8-K/5min, 10-K/hourly, Form4/10min, market hours)
- Alembic migrations: `src/storage/migrations/` (async env, initial 3-table migration)
- Database engine: `src/storage/database.py`

- LangGraph agent pipeline: `src/agents/pipeline.py` (6-agent chain with conditional routing)
- All 5 agents: ingestion, entity_resolution, event_extraction, impact_hypothesis, risk_gate
- RAG embedder: `src/rag/embedder.py` (OpenAI text-embedding-3-small, 1536-dim)
- RAG vector store: `src/rag/vector_store.py` (Pinecone client, namespace-partitioned)
- RAG retriever: `src/rag/retriever.py` (top-K semantic search, min_similarity filtering)
- Evidence builder: `src/rag/evidence_builder.py` (vector matches → EvidenceItem objects)
- Market data client: `src/ingestion/market_data.py` (Alpha Vantage + Finnhub)
- Docker Compose: `docker-compose.yml` (PostgreSQL 16 + Redis 7)

- FastAPI REST API: `src/api/app.py` (app factory with CORS, lifespan, 12 routes)
- API routes: signals, events, entities, auth, health, pipeline (all implemented)
- API deps: `src/api/deps.py` (DB session injection, bearer token auth)
- API middleware: `src/api/middleware.py` (CORS, request logging, error handling)
- Frontend API client: `frontend/src/api/client.js` (auth, signals, events, entities, pipeline)
- Frontend auth: `frontend/src/context/AuthContext.jsx` (token-based login/logout)
- Frontend wiring: CommandCore + SignalResolution fetch from backend API with fallback
- Vite proxy: `frontend/vite.config.js` (proxy /api → localhost:8000)

**What's skeleton/TODO (stubs only):**
- All gateway: `src/gateway/`
- News ingestion: `src/ingestion/gdelt/`, `src/ingestion/newsapi/`

## Phase 2 Priorities (in order)

1. ~~**FastAPI REST API**~~ — DONE: `src/api/` (12 routes, auth, CORS)
2. ~~**Frontend integration**~~ — DONE: API client, auth flow, dashboard wiring
3. **WebSocket gateway** — `src/gateway/` (real-time signal push)
4. **News ingestion expansion** — GDELT + NewsAPI
5. **Labeled test set** — 100 events with ground truth for evaluation
6. **Live end-to-end test** — Docker Compose up → Alembic migrate → real EDGAR filing → signal

## Core Pipeline Architecture

```
Ingestion → Normalize/Dedupe → Change Gate → Entity Resolution → Event Extraction → Impact Hypothesis (RAG) → Risk Gate → Signal Store → API/UI
```

- **Agent orchestration:** LangGraph (Phase 1)
- **State passing:** `src/agents/state.py` — `PipelineState` TypedDict
- **Vector store:** Pinecone/Qdrant for semantic similarity in Impact Hypothesis Agent (Phase 1)
- **Every signal must include:** confidence score, rationale, evidence[], uncertainty statement, disclaimer

## Tech Stack

- Python 3.11+ (strict mypy, ruff linting)
- FastAPI + uvicorn (API, Phase 2)
- SQLAlchemy 2.0 async + asyncpg (PostgreSQL)
- Celery + Redis (task queue)
- httpx (async HTTP for EDGAR/APIs)
- transformers + torch (FinBERT)
- Pinecone (vector store, Phase 1)
- LangGraph (agent orchestration, Phase 1)
- Pydantic v2 (all schemas)

## Testing

```bash
cd backend && pytest tests/ -v
```

- Working tests: `test_change_gate.py`, `test_normalizer.py`, `test_risk_gate.py`, `test_metrics.py`
- Skeleton tests: everything else in `tests/`
- Fixtures: `tests/conftest.py` (sample entity, event, signal, evidence)
- Config: `pyproject.toml` — asyncio_mode=auto, ruff line-length=100, mypy strict

## Coding Standards

- Type hints on all functions
- Google-style docstrings on public functions
- Async where I/O is involved
- Tests for all public functions (pytest + pytest-asyncio)
- Pydantic models for all data contracts
- Follow existing patterns in `src/models/` and `src/ingestion/normalizer.py`
- Line length: 100 (ruff)
- Target: Python 3.11

## Environment Setup

```bash
cp backend/.env.example backend/.env  # fill in API keys
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e "backend[dev]"
```

## Key External APIs

- **SEC EDGAR:** `https://data.sec.gov` (free, 10 req/sec, User-Agent required)
- **SEC companyfacts.zip:** `https://www.sec.gov/files/companyfacts.zip` (entity resolution)
- **GDELT:** `https://api.gdeltproject.org/api/v2` (Phase 2)
- **NewsAPI:** requires key (Phase 2)

## Documentation

- `RESEARCH/ARCHITECTURE.md` — Full system design (v0.2, informed by AgentPredict review)
- `RESEARCH/ROADMAP.md` — Phase timeline and deliverables
- `ROLES.md` — Team responsibilities
- `projectskeleton.txt` — Backend skeleton overview

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
