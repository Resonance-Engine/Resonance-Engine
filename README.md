# Resonance Engine

Financial computing and market intelligence software focused on real-time **news → understanding → signals** for retail traders.

## Mission

Help traders interpret breaking information quickly, transparently, and responsibly by turning unstructured news and disclosures into structured events and testable market-impact hypotheses.

## What this repo is (right now)

Early-stage scaffolding for:
- **Ingestion** of news + public disclosures (SEC filings, news APIs)
- **Entity resolution** (ticker/company mapping, CIK normalization)
- **Event extraction** (what happened? who is affected? event taxonomy)
- **Impact hypotheses** (what tends to happen next, with uncertainty quantification)
- **Signal surfacing** (alerts + explainability + guardrails)

**Not yet:**
- A live trading system
- Investment advice
- A backtest-validated alpha product

## Core Concepts

### Event Card (planned output)
Each breaking news item becomes a structured event:
- **Source** + timestamp + link (citation trail)
- **Entities affected** (tickers, CIKs, company names)
- **Event type** taxonomy (earnings, guidance, offering, litigation, FDA approval, macro data, etc.)
- **Novelty/relevance/confidence** scores
- **Impact hypotheses** with uncertainty bounds
- **Suggested follow-up checks** (related filings, historical precedents)

### Signal (planned output)
A normalized, testable statement derived from an Event Card:
- "Unusually high likelihood of short-term volatility increase"
- "Historically positive drift after similar events (low confidence)"
- "FDA approval language suggests probable stock movement >5% in next 2 hours (medium confidence)"

**Every signal includes:**
- Confidence score (calibrated probability)
- Supporting rationale (which features/patterns triggered it)
- Uncertainty acknowledgment (what we don't know)

## Data Sources (MVP-friendly)

**Planned starting points:**
- **SEC EDGAR APIs** + bulk downloads (8-Ks, 10-Ks, companyfacts.zip, submissions.zip)
- **GDELT Project** for broad event/news exploration at scale
- **NewsAPI** for prototyping ingestion workflows (developer-tier)
- **Optional:** Social sources (Reddit/X) only if compliant with platform terms

**Market data for labeling/evaluation (starter options):**
- Alpha Vantage (free tier with rate limits)
- Finnhub (rate-limit aware batching)
- Polygon.io (news + market data joins)

**What we're NOT relying on:**
- IEX Cloud (discontinued as of late 2024)
- Premium Bloomberg/Reuters feeds (institutional pricing, MVP blocker)

## Architecture Direction (high level)
```
Ingestion → Normalize/Dedupe → Entity Resolution → Event Extraction 
    → Impact Hypotheses → Signal Store → API/UI
```

**System traits we care about early:**
- **Reproducibility** (event replay from immutable logs)
- **Timestamp integrity** (no look-ahead bias in backtests)
- **Auditable artifacts** (every signal has a provenance chain)
- **Clear evaluation harness** (offline metrics + market reaction labels)

**Tech primitives under consideration:**
- Event streaming (Kafka/Redis Streams for replay)
- Stream processing (Flink/lightweight alternatives for stateful computations)
- Observability (OpenTelemetry for correlated traces/logs/metrics)

## Agentic AI Workflow (planned)

We define **"agentic"** as:
1. Decomposing tasks into steps (ingestion → entity resolution → event extraction → impact analysis)
2. Interacting with tools (retrievers, parsers, calendars, symbol mappers)
3. Maintaining state across steps (typed intermediate outputs)
4. Producing auditable artifacts (explainable signal generation)

**Planned agent breakdown:**
- **Ingestion Agent:** Standardizes incoming documents (source, timestamp, URL, raw text), deduplicates, assigns stable IDs
- **Entity Resolution Agent:** Maps mentions to canonical entities (tickers, CIKs), handles ambiguous names
- **Event Extraction Agent:** Converts text into event schema (FDA approval, earnings guidance, lawsuit), with polarity and confidence
- **Impact Hypothesis Agent:** Produces scenario-based hypotheses ("probable short-term volatility spike; direction uncertain")
- **Risk/Policy Gate Agent:** Enforces "not investment advice" wording, blocks overconfident language, validates citations, logs uncertainty

## Local Development (placeholder)

**TODO:** Add setup instructions for backend/frontend once scaffolding is committed.

For now:
```bash
# Clone the repo
git clone https://github.com/reiyyanz/Resonance-Engine.git
cd Resonance-Engine

# Create your branch
git checkout -b yourname

# Install dependencies (TBD)
# Run services (TBD)
```

## Repo Structure (current)
```
backend/          # Planned services + data pipelines
frontend/         # Planned UI (event cards, signal dashboard)
RESEARCH/         # PRD, data notes, evaluation plan, model strategy, roadmap
UI Design/        # Brand assets + mockups (logo, color palette)
ROLES.md          # Team roles + responsibilities
README.md         # This file
```

## Documentation Philosophy

We treat documentation as **execution scaffolding**, not afterthought.

Key docs (in `RESEARCH/`):
- **PRD.md** — What we're building, for whom, and why
- **DATA_NOTES.md** — Data sources, licensing, pipeline design
- **ARCHITECTURE.md** — System design (agents, streaming, services)
- **SIGNAL_SPEC.md** — Signal schema, confidence calibration, output format
- **EVALUATION.md** — How we test/validate (metrics, backtesting, bias checks)
- **RISKS_GUARDRAILS.md** — Compliance, failure modes, "not investment advice" stance
- **ROADMAP.md** — Time horizons (short/mid/long-term milestones)
- **REFERENCES.md** — Links to APIs, papers, tools, datasets

## Compliance & Risk Awareness

**This system is not investment advice.**

We are building:
- Educational tools for understanding market information
- Transparent signal generation with uncertainty quantification
- Explainable event interpretation workflows

We are NOT:
- Recommending specific trades
- Guaranteeing outcomes
- Acting as a registered investment adviser

**Documented safety measures:**
- All signals include confidence scores and uncertainty bounds
- Risk/Policy Gate Agent enforces guardrails on output language
- Evaluation harness includes backtest overfitting checks (Bailey et al. methodology)
- Point-in-time data discipline to avoid look-ahead bias
- Clear disclaimers on every user-facing output

## Research Foundations

We build on:
- **FinBERT** (finance-domain sentiment baseline)
- **Loughran-McDonald** sentiment dictionaries (with commercial licensing awareness)
- **GDELT** event data for broad-scale pattern exploration
- **ReAct** paradigm (reasoning + acting with LLMs)
- **ML Test Score** rubric (production ML readiness)
- **Datasheets for Datasets** + **Model Cards** (standardized model/data documentation)
- **NIST AI RMF** (risk-oriented AI governance)
- Academic evidence on textual media content predicting market activity

See `RESEARCH/REFERENCES.md` for full citations.

## Contributing

**Branching conventions:**
- Feature branches: `feature/<short-name>` or `<yourname>/<short-name>`
- Documentation branches are fine; prefer small PRs

**Every PR includes:**
- What changed (one-sentence summary)
- How to test (even if "run this script")
- Screenshots for UI changes
- For model changes: small evaluation report + examples of good/bad outputs

## License

TBD (will add once we formalize)

## Contact

Questions? Open an issue or reach out to the team.

---

**Seek your Alpha.**
