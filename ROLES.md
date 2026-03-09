# Resonance Engine — Roles & Responsibilities

**Purpose:** Define ownership areas so we move fast without stepping on each other.

**Last Updated:** March 2026

---

## Team Structure

### Reiyyan Zafar- Founder — Product & Architecture Lead
**Primary ownership:**
- Product direction (what we build first, for whom, and why)
- UX requirements for Event Cards and Signals (user-facing outputs)
- System architecture decisions (services, storage, deployment approach)
- Release planning and prioritization (roadmap + milestones)
- External relationships:
  - Data vendor evaluation (which APIs to use, pricing negotiations)
  - Partnerships (potential integrations with brokerages, analytics platforms)
  - Go-to-market exploration (pricing model, user acquisition strategy)
  - Investor/fundraising communications

**Secondary:**
- Reviews PRDs, research notes, and evaluation plans (quality check, strategic alignment)
- Reviews model behavior from a **user-trust perspective** (does this output inspire confidence? is it misleading?)
- Frontend development contributions (UI/UX implementation, dashboard polish)

---

### Fairoz Khan — AI/ML Engineer + Data Scientist + Data Engineer
**Role summary:** Owns the **"Signal Intelligence & Data Platform"** — the entire pipeline from raw news ingestion to validated, explainable signals.

**Primary ownership:**

#### 1. Data Engineering
- **Ingestion prototypes**: News + EDGAR data pipelines (pull, parse, normalize, dedupe)
- **Schema design**: Event card schema, signal schema, intermediate data models
- **Storage strategy**: Time-series databases, event logs, caching layers
- **Data quality**: Deduplication logic, timestamp integrity, data validation rules
- **Observability**: Structured logging, tracing IDs for events, metrics dashboards (ingestion latency, error rates)

#### 2. Entity Resolution & NLP Pipelines
- **Ticker/CIK mapping**: Build canonical entity resolver (handle "Apple" vs "Apple Hospitality REIT" ambiguity)
- **Symbol normalization**: Map mentions to tickers, CIKs, ISIN codes
- **Dataset creation**: Hand-label test sets for entity resolution (precision/recall eval)
- **NLP baselines**: Implement FinBERT, Loughran-McDonald lexicons, keyword-based event extractors

#### 3. Agentic AI Workflows
- **Agent design**: Define tool-using pipelines with typed outputs (Ingestion → Entity Resolution → Event Extraction → Impact Hypotheses → Signal Generation)
- **Orchestration**: Implement multi-agent workflows (LangGraph or equivalent framework)
- **Tool integration**: Connect agents to retrievers, parsers, calendars, symbol mappers, market data APIs
- **State management**: Maintain context across agent steps, log intermediate artifacts

#### 4. Model Development & Fine-Tuning
- **Baseline models**: Train/fine-tune FinBERT-style sentiment classifiers
- **Custom event extractors**: Build models for event taxonomy (FDA approval, earnings guidance, lawsuit, etc.)
- **Impact prediction**: Develop models that map events → market reaction hypotheses (volatility, returns, volume)
- **Confidence calibration**: Ensure model probabilities match real-world outcomes (70% confidence → 70% accuracy)

#### 5. Evaluation & Backtesting
- **Offline NLP metrics**: Precision/recall for entity resolution, event extraction F1 scores, confidence calibration plots
- **Market reaction labeling**: Pull post-event returns/volatility/volume data, label signals, measure accuracy vs. random baseline
- **Backtesting safety checks**:
  - **Look-ahead bias**: Enforce point-in-time data discipline (no peeking at future filings/prices)
  - **Survivorship bias**: Include delisted stocks in historical tests
  - **Overfitting detection**: Implement Bailey et al. "Probability of Backtest Overfitting" methodology
- **Drift monitoring**: Monthly checks for model degradation, data distribution shifts

#### 6. MLOps Foundations
- **Experiment tracking**: Use MLflow, Weights & Biases, or equivalent (track hyperparameters, metrics, model versions)
- **Dataset versioning**: DVC or similar (reproducible data snapshots for evals)
- **Model documentation**: Write Model Cards for each production model (intended use, performance, limitations, training data)
- **Pipeline automation**: CI/CD for model retraining, evaluation reports, deployment

#### 7. Documentation
- **RESEARCH/ authoring**:
  - `PRD.md` contributions (technical feasibility, data constraints)
  - `DATA_NOTES.md` (data sources, APIs, schema docs)
  - `ARCHITECTURE.md` (system design diagrams, agent workflows)
  - `SIGNAL_SPEC.md` (signal schema, confidence methodology)
  - `EVALUATION.md` (metrics definitions, backtesting procedures)
  - `REFERENCES.md` (links to papers, APIs, tools)
- **Code documentation**: Docstrings, README updates, architecture decision records (ADRs)

**Secondary:**
- Backend API development (if needed for signal serving, event card retrieval)
- Frontend integration support (help connect UI to backend APIs, debug data issues)

---

## Collaboration Principles

### 1. Every deliverable has an owner
- **Owner** = person responsible for delivery, quality, and maintenance
- **Contributor** = provides input/review but not final decision
- Example: PRD is owned by Founder, but Fairoz contributes technical feasibility notes

### 2. PRD changes require written diffs
- Any change to product scope, target user, or core features must be documented:
  - **What changed** (one-sentence summary)
  - **Why** (rationale, new data, user feedback)
  - **Impact** (does this affect timelines? data needs? evaluation plans?)
- Format: Add a "Changelog" section at bottom of PRD.md

### 3. Model changes require evaluation reports
- Any model that changes output behavior (event extraction, signal generation, confidence scoring) needs:
  - **Small evaluation report** (metrics before/after, examples of improved/degraded outputs)
  - **Good/bad output examples** (at least 5 each, with explanations)
  - **Rollback plan** ("if accuracy drops below X%, revert to previous version")
- Even in early stage (no users yet), this builds good habits and catches bugs early.

### 4. Code review standards
- **No PRs merged without review** (even in early stage, at least one other person reviews)
- **Every PR includes**:
  - What changed (one-sentence summary in PR description)
  - How to test (commands to run, expected output)
  - Screenshots for UI changes
  - Link to related issue/task (if applicable)

### 5. Communication defaults
- **Async-first**: Use GitHub issues/PRs for design discussions (creates written record)
- **Sync when needed**: Voice/video calls for big architecture decisions, brainstorming, debugging sessions
- **Weekly check-ins**: 30-min standup (progress, blockers, next priorities)

---

## Branching & Contribution Conventions

### Branch naming:
- `feature/<short-name>` for new features (e.g., `feature/edgar-ingestion`)
- `fix/<short-name>` for bug fixes (e.g., `fix/ticker-mapping-error`)
- `docs/<short-name>` for documentation updates (e.g., `docs/prd-v0.2`)
- `<yourname>/<short-name>` for personal experimentation (e.g., `fairoz/llm-fine-tuning-test`)

### Commit messages:
- Start with verb (Add, Fix, Update, Remove, Refactor)
- Keep first line <50 chars (summary)
- Add details in body if needed
- Example:
```
  Add EDGAR ingestion pipeline
  
  - Pull 8-K filings from SEC bulk API
  - Parse XML to extract company name, CIK, filing date
  - Store in PostgreSQL events table
```

### Pull requests:
- **Small PRs preferred** (<300 lines of code when possible)
- Every PR includes:
  - **Title**: One-sentence summary of change
  - **Description**: What changed, why, how to test
  - **Related docs**: Links to PRD, ARCHITECTURE.md, or GitHub issue
  - **Testing**: "Ran `pytest tests/ingestion/` — all pass" or "Manual test: triggered ingestion for AAPL, verified event card created"
- **Review SLA**: Both team members commit to reviewing PRs within 24 hours (or communicate blockers)

---

## Decision-Making Framework

### Who decides what:

| Decision Type | Owner | Requires Input From | Example |
|---------------|-------|---------------------|---------|
| **Product scope** | Founder | Fairoz (feasibility check) | "Should we support crypto markets in MVP?" |
| **Data source selection** | Founder | Fairoz (technical eval) | "Use NewsAPI vs GDELT for MVP?" |
| **System architecture** | Founder | Fairoz (implementation reality check) | "Use Kafka vs Redis Streams?" |
| **NLP model choice** | Fairoz | Founder (UX impact review) | "FinBERT vs custom LSTM for sentiment?" |
| **Evaluation metrics** | Fairoz | Founder (business metric alignment) | "Track precision/recall vs just accuracy?" |
| **UI/UX design** | Founder | Fairoz (data constraints) | "Event card layout, signal dashboard wireframes" |
| **Pricing model** | Founder | Fairoz (compute cost estimates) | "Free tier vs $9.99/month premium?" |

### Escalation path:
- If disagreement on technical decision → write pros/cons doc, discuss sync, Founder makes final call
- If disagreement on product direction → Fairoz raises concerns in writing, Founder decides (with rationale documented)

---

## Growth & Role Evolution

### As the team grows:
- **Fairoz's role may split into**:
  - **ML Engineer** (model development, fine-tuning, evaluation)
  - **Data Engineer** (pipelines, storage, observability)
  - **Data Scientist** (analytics, signal research, backtesting)
- For now, Fairoz owns all three, but we'll revisit as workload increases.

### Future hires (when needed):
- **Backend Engineer** (API, microservices, deployment)
- **Frontend Engineer** (React dashboard, mobile app)
- **Quantitative Researcher** (signal strategy, portfolio analytics)
- **Compliance/Legal Advisor** (investment advice boundaries, terms of service)

---

## Appendix: Fairoz's "Signal Intelligence & Data Platform" Ownership Summary

**One-paragraph role definition (for external use, e.g., LinkedIn, investor decks):**

> Fairoz owns the **Signal Intelligence & Data Platform** at Resonance Engine: ingestion pipelines that normalize news and filings into canonical event schemas; entity resolution that maps messy mentions to tickers/CIKs; NLP baselines and agentic workflows that extract structured events and generate impact hypotheses; and evaluation harnesses that are robust to trading research failure modes (overfitting, look-ahead bias, survivorship bias). This role sits at the intersection of AI/ML engineering, data science, and data engineering — responsible for turning raw information into trustworthy, explainable signals.

**Key skills demonstrated:**
- **Data engineering**: Event-driven pipelines, schema design, time-series storage, observability
- **NLP/ML**: FinBERT, custom classifiers, confidence calibration, model documentation
- **Agentic AI**: Multi-agent orchestration, tool use, typed outputs, LangGraph workflows
- **Quantitative rigor**: Backtesting safety, evaluation metrics, drift monitoring, overfitting detection
- **MLOps**: Experiment tracking, dataset versioning, CI/CD for models
- **Documentation**: PRD contributions, architecture diagrams, research notes, Model Cards

---

**Document Status:** v1.0  
**Last Updated:** March 2026  
**Next Review:** After first hire or major scope change
