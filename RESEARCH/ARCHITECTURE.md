# System Architecture & Design
## Resonance Engine Technical Blueprint

**Last Updated:** March 2026
**Owner:** Reiyyan - Product & Architecture Lead
**Contributors:** Reiyyan (Product & Architecture) and Fairoz (AI/ML & Data Platform)
**Revision:** v0.2 — Added vector store layer, RAG-powered Impact Hypothesis Agent, meaningful change gating, WebSocket gateway separation (informed by AgentPredict architecture review)

---

## Architecture Philosophy

**Design principles:**
1. **Start simple, scale intentionally** — Avoid premature optimization
2. **Reproducibility first** — Every signal must be auditable and replayable
3. **Typed contracts** — Clear interfaces between components (no "stringly typed" mess)
4. **Observability by default** — Logs, metrics, traces from day one
5. **Fail gracefully** — Degrade performance, don't crash

---

## High-Level System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SOURCES                        │
│  SEC EDGAR │ GDELT │ NewsAPI │ Alpha Vantage │ Finnhub │ ...   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       INGESTION LAYER                           │
│  • Fetch news/filings (scheduled jobs, webhooks)                │
│  • Normalize to common schema                                   │
│  • Deduplicate (hash-based, URL-based)                          │
│  • Meaningful change gating (filter boilerplate, amended dupes) │
│  • Assign stable event IDs                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTIC WORKFLOW                            │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │  Ingestion   │ → │   Entity     │ → │    Event     │       │
│  │    Agent     │   │  Resolution  │   │  Extraction  │       │
│  │              │   │    Agent     │   │    Agent     │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   Impact     │ → │  Risk/Policy │ → │    Signal    │       │
│  │  Hypothesis  │   │     Gate     │   │    Store     │       │
│  │  Agent (RAG) │   │    Agent     │   │              │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│         ↕                                                       │
│  ┌──────────────┐                                              │
│  │ Vector Store │  (Pinecone/Qdrant — similarity retrieval)    │
│  └──────────────┘                                              │
│                                                                 │
│  (Each agent has typed inputs/outputs, logs, error handling)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                              │
│  • PostgreSQL: events, signals, entities, users                │
│  • Redis: cache (entity lookups, API responses)                │
│  • Vector Store: event embeddings (similarity search)          │
│  • S3: raw data archives (90-day retention)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API & UI LAYER                             │
│  • REST API (events, signals, entities) — FastAPI              │
│  • WebSocket Gateway (real-time signal push, separate service) │
│  • React frontend (event cards, signal dashboard)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVALUATION & MONITORING                      │
│  • Offline metrics (precision, recall, F1)                     │
│  • Backtest harness (look-ahead bias checks)                   │
│  • Live monitoring (signal accuracy, latency, error rates)     │
│  • Drift detection (model degradation alerts)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Ingestion Layer

**Responsibilities:**
- Poll external APIs on schedule (cron, Celery Beat)
- Fetch new filings/news (EDGAR, GDELT, NewsAPI)
- Normalize to common schema (`Event` object)
- Deduplicate (prevent same story from appearing twice)
- Assign stable IDs (UUID or content hash)
- Write to event log (PostgreSQL or Kafka)

**Tech Stack (Phase 0-1):**
- **Language:** Python 3.11+
- **Scheduler:** Celery + Redis (async task queue)
- **HTTP client:** `requests` or `httpx`
- **Parsing:** `lxml`, `BeautifulSoup` (XML/HTML), `pydantic` (validation)

**Tech Stack (Phase 3+):**
- **Scheduler:** Airflow (better for complex DAGs, retries, monitoring)
- **Event log:** Kafka (immutable log, replay capability)
- **Stream processing:** Flink or Kafka Streams (real-time transformations)

**Data Flow:**
```
External API → Fetch → Parse → Validate → Dedupe → Assign ID → Store
```

**Deduplication Strategy:**
- Hash function: `hash(source + URL + timestamp)`
- Store hashes in Redis (expire after 7 days)
- If hash exists → skip, else → process

**Meaningful Change Gating (Phase 0):**

Before events enter the 6-agent pipeline, gate on material change to save compute on expensive downstream agents and keep signal-to-noise high:
- **Amended filings:** If an EDGAR filing is an amendment (e.g., 10-K/A), diff against the original — only re-process if substance changed
- **Boilerplate detection:** Skip 10-K annual filings with <5% text delta from prior year (risk factor copy-paste)
- **Story deduplication:** When multiple news sources cover the same event, cluster by entity + event type + timestamp window (±2h) and process only the first arrival
- **Delta threshold:** For market data feeds, only emit events on meaningful change (e.g., probability delta >0.01, price move >0.5%)

This pattern is borrowed from AgentPredict's agent design, where the polymarket agent only emits on delta >0.01 to avoid flooding the pipeline with noise.

```python
def is_meaningful_change(event: Event, recent_events: list[Event]) -> bool:
    """Gate: only pass events that represent material new information."""
    # Check content hash against recent events (dedup)
    if event.content_hash in {e.content_hash for e in recent_events}:
        return False
    # Check entity+event_type cluster (same story, different source)
    for recent in recent_events:
        if (event.primary_ticker == recent.primary_ticker
            and event.event_type == recent.event_type
            and abs((event.timestamp - recent.timestamp).total_seconds()) < 7200):
            return False
    return True
```

**Example Code (Phase 0):**
```python
from pydantic import BaseModel
from datetime import datetime
import hashlib

class Event(BaseModel):
    event_id: str
    timestamp: datetime
    source: str
    url: str
    raw_text: str
    entities: list[dict]
    event_type: str | None
    summary: str | None

def dedupe_hash(source: str, url: str, timestamp: datetime) -> str:
    content = f"{source}|{url}|{timestamp.isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

# Usage:
event_hash = dedupe_hash("SEC_EDGAR", "https://sec.gov/...", datetime.now())
if redis.exists(event_hash):
    print("Duplicate, skip")
else:
    redis.setex(event_hash, 7 * 86400, "1")  # Expire after 7 days
    # Process event...
```

---

### 2. Agentic Workflow (Multi-Agent Pipeline)

**Why agentic?**
- **Modularity:** Each agent has one job → easier to debug, test, iterate
- **Tool use:** Agents can call external tools (entity resolver, sentiment API, market data)
- **Typed outputs:** Clear contracts between stages (no "stringly typed" chaos)
- **Auditability:** Log every intermediate artifact (provenance chain for every signal)

**Agent Breakdown:**

#### Agent 1: Ingestion Agent
- **Input:** Raw API response (JSON, XML, HTML)
- **Output:** `Event` object (standardized schema)
- **Tools:** None (pure transformation)
- **Validation:** Pydantic schema enforcement

#### Agent 2: Entity Resolution Agent
- **Input:** `Event` object (with raw text mentioning companies)
- **Output:** `Event` object (with `entities` list populated: `[{ticker, cik, name}]`)
- **Tools:**
  - SEC companyfacts.zip (ticker → CIK mapping)
  - Fuzzy string matching (handle typos, abbreviations)
  - Disambiguation rules ("Apple" → AAPL vs APLE)
- **Validation:** Precision >85% on test set

#### Agent 3: Event Extraction Agent
- **Input:** `Event` object (with entities resolved)
- **Output:** `Event` object (with `event_type`, `summary`, `confidence` populated)
- **Tools:**
  - FinBERT (sentiment classifier)
  - Loughran-McDonald lexicon (finance-specific sentiment)
  - Keyword rules (e.g., "FDA approval" → `fda_approval` event type)
- **Validation:** F1 score >0.60 on test set

#### Agent 4: Impact Hypothesis Agent (RAG-Powered)
- **Input:** `Event` object (with event type + entities)
- **Output:** `Signal` object (with `signal_text`, `confidence`, `rationale`, `uncertainty`, `evidence[]`)
- **Tools:**
  - **Vector Store (Pinecone/Qdrant)** — retrieve top-K similar historical events by semantic similarity
  - Market data API (Alpha Vantage, Finnhub) for historical returns
  - Statistical model (e.g., "FDA approvals historically lead to +8% avg return in 24h")
- **Validation:** Confidence calibration <10% error

**RAG Flow (Phase 1):**
```
Event (with entities + event_type)
    → Embed event summary (text-embedding-3-small or equivalent)
    → Query vector store: "find K most similar historical events"
    → Retrieved evidence: [{event_summary, ticker, outcome, similarity_score}, ...]
    → Combine: structured SQL lookup (same ticker/event_type) + semantic retrieval (cross-sector analogues)
    → Generate hypothesis grounded in retrieved evidence
    → Confidence score backed by N similar precedents
    → Output: Signal with evidence[] array
```

**Why RAG?** Without a vector store, the Impact Hypothesis Agent can only do exact-match SQL queries (same ticker, same event type). With semantic retrieval, it finds **analogous patterns across different companies and sectors** — e.g., "this CEO resignation resembles these 12 others across biotech." This directly strengthens Resonance's explainability differentiator.

**Vector Store Design:**
- **Provider:** Pinecone (managed, serverless) or Qdrant (self-hosted option)
- **Embedding model:** OpenAI text-embedding-3-small (Phase 1) or fine-tuned financial embedding (Phase 3)
- **Namespaces:** One per event source (sec_edgar, gdelt, newsapi) for filtered retrieval
- **Upsert policy:** Every event that passes the meaningful change gate gets embedded and upserted — the store grows over time, building a proprietary historical knowledge base
- **Retrieval:** Top-K (K=10) by cosine similarity, filtered by event_type or sector when relevant
- **Supplementary, not primary:** PostgreSQL remains the source of truth. Vector store is a similarity index only.

```python
class EvidenceItem(BaseModel):
    """A single piece of retrieved evidence backing a signal."""
    event_id: str                    # ID of the historical event
    event_summary: str               # What happened
    ticker: str | None               # Which company (if applicable)
    outcome: str                     # What was the market reaction
    similarity_score: float          # Cosine similarity (0.0-1.0)
    time_delta: str                  # How long ago this happened

class Signal(BaseModel):
    # ... existing fields ...
    evidence: list[EvidenceItem]     # Retrieved similar historical events
```

#### Agent 5: Risk/Policy Gate Agent
- **Input:** `Signal` object (draft)
- **Output:** `Signal` object (approved) OR rejection (with reason)
- **Tools:**
  - Regex filters (block "guaranteed," "sure thing," etc.)
  - Citation validator (every signal must link to source event)
  - Disclaimer injector (append "This is not investment advice")
- **Validation:** 100% block rate for non-compliant outputs on test set

**Orchestration (Phase 1):**
- **Framework:** LangGraph (typed workflows, state management)
- **Alternative:** Custom pipeline using Python async/await
- **State:** Pass `Event` and `Signal` objects through agents, log each step

**Example LangGraph Workflow:**
```python
from langgraph.graph import StateGraph, END

class PipelineState:
    event: Event
    signal: Signal | None
    
workflow = StateGraph(PipelineState)

workflow.add_node("ingest", ingestion_agent)
workflow.add_node("resolve_entities", entity_resolution_agent)
workflow.add_node("extract_event", event_extraction_agent)
workflow.add_node("gen_hypothesis", impact_hypothesis_agent)
workflow.add_node("risk_gate", risk_policy_gate_agent)

workflow.add_edge("ingest", "resolve_entities")
workflow.add_edge("resolve_entities", "extract_event")
workflow.add_edge("extract_event", "gen_hypothesis")
workflow.add_edge("gen_hypothesis", "risk_gate")
workflow.add_edge("risk_gate", END)

workflow.set_entry_point("ingest")

# Run pipeline:
result = workflow.run({"event": raw_event})
```

---

### 3. Storage Layer

**Database: PostgreSQL**
- **Why:** ACID guarantees, JSONB support (flexible schema), mature ecosystem
- **Tables:** `events`, `signals`, `entities`, `users`
- **Indexes:** Timestamp (DESC), ticker, event_type, GIN on JSONB fields
- **Partitioning (Phase 3+):** Partition `events` and `signals` by month (faster queries)

**Cache: Redis**
- **Why:** Fast lookups (entity resolution, API response caching)
- **Use cases:**
  - Entity cache: `ticker:AAPL` → `{cik, name, sic}`
  - API response cache: `newsapi:fda-approval:2026-03-09` → `[article1, article2, ...]`
  - Deduplication hashes (expire after 7 days)
- **Eviction policy:** LRU (least recently used)

**Vector Store: Pinecone/Qdrant (Phase 1+)**
- **Why:** Semantic similarity search for historical event retrieval — enables cross-sector pattern matching that SQL can't do
- **Use cases:**
  - Impact Hypothesis Agent retrieves top-K similar historical events
  - Evidence grounding for signal rationale
  - Builds proprietary knowledge base over time (every processed event gets embedded)
- **Namespaces:** One per source (sec_edgar, gdelt, newsapi)
- **Embedding model:** text-embedding-3-small (Phase 1), fine-tuned financial embedding (Phase 3)
- **Role:** Supplementary index for similarity search — PostgreSQL remains source of truth

**Archive: AWS S3**
- **Why:** Cheap long-term storage for raw data
- **Use cases:**
  - Raw API responses (JSON dumps, 90-day retention)
  - Model checkpoints (for reproducibility)
  - Evaluation reports (monthly snapshots)
- **Lifecycle policy:** Move to Glacier after 90 days, delete after 1 year

---

### 4. API & UI Layer

**Backend API (Phase 2):**
- **Framework:** FastAPI (Python) — fast, typed, auto-docs via OpenAPI
- **Endpoints:**
  - `GET /events` — List recent events (paginated, filterable by ticker/date)
  - `GET /events/{event_id}` — Get single event (with full details)
  - `GET /signals` — List recent signals (paginated, filterable by confidence/ticker)
  - `GET /signals/{signal_id}` — Get single signal (with rationale/citations/evidence)
  - `GET /entities/{ticker}` — Get company info (CIK, name, recent events)
  - `POST /watchlist` — Add ticker to user's watchlist
  - `GET /watchlist` — Get user's watchlist
  - `GET /health` — Health check endpoint
- **Authentication:** JWT tokens (simple, stateless)
- **Rate limiting:** 100 requests/minute per user (prevent abuse)

**WebSocket Gateway (Phase 2, separate service):**

The WebSocket real-time push is a **separate thin service** from the REST API. This pattern is borrowed from AgentPredict's gateway design:

- **Why separate?** The REST API handles request/response (stateless, scales horizontally). WebSocket connections are long-lived and stateful (connection lifecycle, reconnection, fan-out). Mixing them creates operational complexity as you scale.
- **Gateway responsibilities:**
  - `/ws/signals` — Subscribe to real-time signal push
  - `/health` — Health check
  - Subscribe to new signals from PostgreSQL (LISTEN/NOTIFY or poll)
  - Fan-out to all connected browser clients
  - Buffer last N signals for late-joining clients (cursor-based catch-up)
  - Silent removal of disconnected clients
- **Message envelope:** `{"type": "signal"|"event", "data": {...}}`
- **Phase 0-1:** WebSocket handling lives inside FastAPI (simple, no separation needed yet)
- **Phase 2+:** Split into dedicated gateway service when real users connect

**Frontend (Phase 2):**
- **Framework:** React + TypeScript
- **UI Components:**
  - Event card (source, timestamp, entities, summary, confidence)
  - Signal dashboard (sortable table, filters, click to expand)
  - Watchlist (user-selected tickers, notification preferences)
- **State management:** Zustand or React Query (simpler than Redux)
- **Styling:** Tailwind CSS (rapid prototyping)

**Deployment (Phase 2-3):**
- **Phase 2:** AWS EC2 (t3.small, simple deployment)
- **Phase 3:** Docker + ECS or Kubernetes (auto-scaling, zero-downtime deploys)
- **CDN:** CloudFront (static assets, reduce latency)
- **SSL:** Let's Encrypt (free HTTPS)

---

### 5. Evaluation & Monitoring

**Offline Metrics (Phase 1):**
- **Entity resolution:** Precision, recall, F1 (hand-labeled test set)
- **Event extraction:** F1 score, confusion matrix (per event type)
- **Confidence calibration:** Plot predicted probabilities vs. actual outcomes

**Backtesting Harness (Phase 1):**
- **Look-ahead bias check:** Ensure all data is point-in-time (no future peeking)
- **Survivorship bias check:** Include delisted stocks in historical tests
- **Overfitting detection:** Bailey et al. "Probability of Backtest Overfitting" methodology
- **Monthly drift monitoring:** Compare current model performance to baseline

**Live Monitoring (Phase 2+):**
- **Signal accuracy:** Track post-event outcomes (did signal pan out?)
- **Latency:** Time from event ingestion → signal generation
- **Error rates:** % of events that fail entity resolution, event extraction, etc.
- **User engagement:** Click-through rate on signals, time spent on platform

**Observability Stack (Phase 3+):**
- **Metrics:** Prometheus (collect metrics from all services)
- **Dashboards:** Grafana (visualize metrics, set alerts)
- **Logs:** Structured logging (JSON format), centralized via Loki or CloudWatch
- **Traces:** OpenTelemetry (correlate logs/metrics across services)

---

## Tech Stack Summary

| Component | Phase 0-1 (MVP) | Phase 3+ (Production) |
|-----------|----------------|----------------------|
| **Language** | Python 3.11+ | Python 3.11+ |
| **Ingestion** | Celery + Redis | Airflow + Kafka |
| **Event log** | PostgreSQL | Kafka + PostgreSQL |
| **Stream processing** | None (batch jobs) | Flink or Kafka Streams |
| **Database** | PostgreSQL | PostgreSQL + TimescaleDB |
| **Vector Store** | Pinecone (serverless free tier) | Pinecone/Qdrant (dedicated) |
| **Cache** | Redis (single instance) | Redis Cluster |
| **API** | FastAPI (monolith) | FastAPI + WS Gateway + Load Balancer |
| **Frontend** | React + TypeScript | React + TypeScript |
| **Deployment** | AWS EC2 (t3.small) | Docker + ECS/K8s |
| **Monitoring** | Python logging | Prometheus + Grafana + OpenTelemetry |
| **Archive** | AWS S3 | AWS S3 + Glacier |

---

## Scalability Considerations

### Phase 0-1 (100 events/day):
- Single EC2 instance (t3.small: 2 vCPU, 2GB RAM)
- PostgreSQL (db.t3.micro: 2GB storage)
- Redis (cache.t3.micro: 512MB)
- **Total cost:** ~$50/month

### Phase 2 (1,000 events/day, 100 users):
- 2x EC2 instances (load balanced)
- PostgreSQL (db.t3.small: 20GB storage)
- Redis (cache.t3.small: 1GB)
- **Total cost:** ~$150/month

### Phase 3+ (10,000 events/day, 1,000 users):
- 5x EC2 instances (auto-scaling)
- PostgreSQL (db.m5.large: 100GB storage, read replicas)
- Redis Cluster (3 nodes, 5GB total)
- Kafka (3-node cluster for event streaming)
- **Total cost:** ~$800/month

---

## Security & Compliance

### Security Measures:
- **Encryption at rest:** PostgreSQL (AWS RDS encryption), S3 (server-side encryption)
- **Encryption in transit:** HTTPS (TLS 1.3), WebSocket over WSS
- **Authentication:** JWT tokens (short-lived, refresh tokens for long sessions)
- **Authorization:** Role-based access control (admin, premium user, free user)
- **Rate limiting:** Prevent abuse (100 req/min per user, 1000 req/min per IP)
- **Input validation:** Pydantic schemas (prevent injection attacks)

### Compliance:
- **GDPR:** Right to access, right to deletion (delete user data on request)
- **CCPA:** Similar to GDPR (California users)
- **Investment Advice:** NOT providing investment advice (strong disclaimers, Risk Gate enforcement)
- **Terms of Service:** Educational use only, no guarantees, user assumes all risk

---

## Disaster Recovery & Backups

### Backup Strategy:
- **Database:** Daily snapshots (AWS RDS automated backups, 7-day retention)
- **Event log (Kafka):** Replicated across 3 nodes, 7-day retention
- **S3 archives:** Versioning enabled, 30-day retention for raw data

### Recovery Plan:
- **Database failure:** Restore from latest snapshot (RTO: <1 hour)
- **Complete AWS outage:** Multi-region deployment (Phase 4+)
- **Data corruption:** Replay events from Kafka log (Phase 3+)

---

## Open Architecture Decisions (To Revisit)

1. **Kafka vs. Redis Streams?**
   - Kafka: More mature, better tooling, higher operational overhead
   - Redis Streams: Simpler, lower cost, less mature
   - **Decision:** Start with Redis Streams (Phase 0-2), migrate to Kafka if scale demands it (Phase 3+)

2. **Monolith vs. Microservices?**
   - Monolith: Simpler deployment, faster iteration
   - Microservices: Better scalability, more complex
   - **Decision:** Start with monolith (Phase 0-2), split into services if team grows (Phase 3+)

3. **Self-hosted vs. Managed Services?**
   - Self-hosted: Lower cost, more control, higher operational burden
   - Managed: Higher cost, less control, easier operations
   - **Decision:** Use managed services (AWS RDS, ElastiCache, ECS) to focus on product, not ops

---

## Appendix: Related Documents

- `RESEARCH/PRD.md` — Product vision, user personas, core features
- `RESEARCH/DATA_NOTES.md` — Data sources, APIs, licensing
- `RESEARCH/ROADMAP.md` — Time horizons, milestones
- `RESEARCH/EVALUATION.md` — Metrics, backtesting methodology
- `ROLES.md` — Team ownership, decision-making

---

**Document Status:** Draft v0.2
**Last Updated:** March 2026
**Next Review:** After Phase 0 prototype
**Changelog:** v0.2 — Added vector store (Pinecone/Qdrant) as supplementary storage, RAG-powered Impact Hypothesis Agent, meaningful change gating at ingestion, WebSocket gateway separation for Phase 2+, evidence[] field on signals. Informed by AgentPredict architecture review.
