# System Architecture & Design
## Resonance Engine Technical Blueprint

**Last Updated:** March 2026  
**Owner:** Product & Architecture Lead  
**Contributors:** Fairoz (AI/ML + Data Platform)

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
│  │    Agent     │   │    Agent     │   │              │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                 │
│  (Each agent has typed inputs/outputs, logs, error handling)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                              │
│  • PostgreSQL: events, signals, entities, users                │
│  • Redis: cache (entity lookups, API responses)                │
│  • S3: raw data archives (90-day retention)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API & UI LAYER                             │
│  • REST API (events, signals, entities)                        │
│  • WebSocket (real-time signal push)                           │
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

#### Agent 4: Impact Hypothesis Agent
- **Input:** `Event` object (with event type + entities)
- **Output:** `Signal` object (with `signal_text`, `confidence`, `rationale`, `uncertainty`)
- **Tools:**
  - Market data API (Alpha Vantage, Finnhub) for historical returns
  - Statistical model (e.g., "FDA approvals historically lead to +8% avg return in 24h")
- **Validation:** Confidence calibration <10% error

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
  - `GET /signals/{signal_id}` — Get single signal (with rationale/citations)
  - `GET /entities/{ticker}` — Get company info (CIK, name, recent events)
  - `POST /watchlist` — Add ticker to user's watchlist
  - `GET /watchlist` — Get user's watchlist
- **Authentication:** JWT tokens (simple, stateless)
- **Rate limiting:** 100 requests/minute per user (prevent abuse)
- **WebSocket:** `/ws/signals` — Real-time push notifications for new signals

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
| **Cache** | Redis (single instance) | Redis Cluster |
| **API** | FastAPI | FastAPI + Load Balancer |
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

**Document Status:** Draft v0.1  
**Last Updated:** March 2026  
**Next Review:** After Phase 0 prototype
