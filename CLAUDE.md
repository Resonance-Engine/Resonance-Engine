# Resonance Engine

Financial intelligence platform that transforms unstructured SEC filings and news into structured, actionable signals for retail traders.

## Who Is Working

- **Fairoz Khan** (`fairoz` branch) — AI/ML Engineer, Data Scientist, Data Engineer. Owns the entire backend: ingestion, NLP, RAG, agents, storage, evaluation.
- **Reiyyan Zafar** — Founder, Product & Architecture Lead. Owns frontend, product decisions, architecture sign-off.
- `main` branch requires 1 approving review before merge.

## Current Phase: Phase 0 (Foundation)

**Goal:** Prove the core pipeline works end-to-end with EDGAR filings.

**What's implemented (working code):**
- Pydantic models: `src/models/` (event, signal, entity, evidence)
- SQLAlchemy ORM: `src/storage/models.py` (EventModel, SignalModel, EntityModel with indexes)
- Config: `src/config.py` (Pydantic Settings, all env vars)
- Ingestion utilities: `src/ingestion/normalizer.py`, `src/ingestion/deduplicator.py`, `src/ingestion/change_gate.py`
- Risk gate regex: `src/agents/risk_gate.py` (`contains_blocked_language()` only)
- Metrics: `src/evaluation/metrics.py` (`f1_score()` only)
- Celery app factory: `src/celery_app.py`
- Database engine: `src/storage/database.py`

**What's skeleton/TODO (stubs only):**
- EDGAR client + parser: `src/ingestion/edgar/`
- All NLP: `src/nlp/entity_resolver.py`, `src/nlp/finbert.py`, `src/nlp/loughran_mcdonald.py`
- All agents: `src/agents/pipeline.py`, `src/agents/*.py` (except risk_gate regex)
- All RAG: `src/rag/`
- All storage repos: `src/storage/event_repo.py`, `src/storage/signal_repo.py`, `src/storage/entity_repo.py`
- All API routes: `src/api/`
- All gateway: `src/gateway/`
- Evaluation: most of `src/evaluation/`

## Phase 0 Priorities (in order)

1. **EDGAR client** — `src/ingestion/edgar/client.py` (httpx async, SEC API at data.sec.gov, 10 req/sec rate limit, User-Agent required)
2. **EDGAR parser** — `src/ingestion/edgar/parser.py` (parse 8-K/10-K XML/SGML, extract text, item codes)
3. **Entity resolution** — `src/nlp/entity_resolver.py` (load SEC companyfacts.zip, fuzzy ticker/CIK matching)
4. **FinBERT sentiment** — `src/nlp/finbert.py` (HuggingFace transformers, financial sentiment)
5. **Loughran-McDonald** — `src/nlp/loughran_mcdonald.py` (word list lexicon scoring)
6. **Storage repos** — `src/storage/event_repo.py` (async SQLAlchemy CRUD)
7. **Celery tasks** — `src/ingestion/edgar/tasks.py` (scheduled polling)
8. **Evaluation harness** — `src/evaluation/` (precision@k, recall@k, brier score, calibration error)

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
