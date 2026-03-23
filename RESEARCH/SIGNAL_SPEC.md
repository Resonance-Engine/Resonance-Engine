# Signal Specification & Design
## How Signals Work in Resonance Engine

**Last Updated:** March 2026
**Owner and Co-Owner:** Reiyyan (Product & Architecture) and Fairoz (AI/ML & Data Platform)
**Reviewers:** Reiyyan - Product & Architecture Lead
**Revision:** v0.2 — Added evidence[] array to signal schema (informed by AgentPredict architecture review)

---

## What is a Signal?

A **signal** is a testable, actionable statement derived from an event that:
1. **Predicts** a market outcome (price move, volatility spike, volume surge)
2. **Quantifies uncertainty** (confidence score, not a guarantee)
3. **Explains itself** (rationale, citations, historical precedents)
4. **Acknowledges what it doesn't know** (uncertainty statement)

**Signals are NOT:**
- Investment advice (legally, we can't recommend specific trades)
- Guarantees (markets are unpredictable)
- Black boxes (every signal must be explainable)

---

## Signal Schema (JSON)
```json
{
  "signal_id": "sig_20260309_001",
  "event_id": "evt_20260309_001",
  "timestamp": "2026-03-09T14:35:00Z",
  "ticker": "AAPL",
  "signal_type": "volatility_spike",
  "signal_text": "High probability of short-term volatility increase for AAPL in next 4 hours",
  "confidence": 0.78,
  "rationale": "Historical precedent: guidance cuts typically trigger 2-5% intraday moves. Apple's Q2 guidance cut by 5% is material. Across 23 similar guidance revisions (retrieved via semantic search), median intraday move was 3.1%.",
  "uncertainty": "Direction uncertain (could move up or down). Supply chain issues are complex and market reaction depends on broader tech sector sentiment.",
  "impact_window": "4h",
  "predicted_move": null,
  "actual_move": null,
  "evidence": [
    {
      "event_id": "evt_20250815_042",
      "event_summary": "AAPL Q3 2025 guidance cut by 3%, supply chain concerns cited",
      "ticker": "AAPL",
      "outcome": "+2.8% intraday move (direction: down then recovery)",
      "similarity_score": 0.94,
      "time_delta": "7 months ago"
    },
    {
      "event_id": "evt_20241120_019",
      "event_summary": "MSFT Q4 2024 guidance revision downward by 4%, cloud growth slowing",
      "ticker": "MSFT",
      "outcome": "-3.2% intraday move, recovered over 48h",
      "similarity_score": 0.87,
      "time_delta": "16 months ago"
    },
    {
      "event_id": "evt_20250203_008",
      "event_summary": "GOOGL Q1 2025 guidance cut by 6%, ad revenue headwinds",
      "ticker": "GOOGL",
      "outcome": "-4.1% intraday move",
      "similarity_score": 0.82,
      "time_delta": "13 months ago"
    }
  ],
  "citations": [
    {"type": "event", "id": "evt_20260309_001", "url": "https://sec.gov/..."},
    {"type": "historical_data", "description": "AAPL guidance revisions 2020-2025 (n=12)"},
    {"type": "vector_retrieval", "description": "Top-3 similar guidance revision events (cosine similarity >0.80)"}
  ],
  "metadata": {
    "model_version": "v0.1.2",
    "generated_at": "2026-03-09T14:35:12Z",
    "agent_chain": ["ingestion", "entity_resolution", "event_extraction", "impact_hypothesis", "risk_gate"],
    "evidence_count": 3,
    "avg_similarity": 0.88
  },
  "created_at": "2026-03-09T14:35:12Z"
}
```

---

## Signal Types (Taxonomy)

| Signal Type | Description | Example |
|-------------|-------------|---------|
| **volatility_spike** | Short-term volatility increase (direction uncertain) | "High probability of 2-5% intraday move in next 4 hours" |
| **positive_drift** | Directional move upward (low-medium confidence) | "Medium confidence of +3% move in next 24 hours based on FDA approval precedent" |
| **negative_drift** | Directional move downward (low-medium confidence) | "Medium confidence of -4% move in next 24 hours based on earnings miss precedent" |
| **volume_surge** | Unusual trading volume expected | "High probability of 2x average volume in next 2 hours" |
| **low_confidence** | Event detected but no clear pattern | "Event is material but historical outcomes are mixed; no actionable signal" |
| **watch** | Monitor for follow-up events | "Lawsuit filed; watch for settlement news in next 30 days" |

**Note:** We start with conservative signal types (volatility, drift) and add more as models improve.

---

## Confidence Scoring

### What Confidence Means:
- **Confidence = 0.78** means "in our training data, when we said 78% confidence, we were right 78% of the time"
- **NOT** a prediction of exact probability (markets are non-stationary)
- **NOT** a recommendation (we don't say "buy" or "sell")

### Confidence Calibration:
- **Phase 1 target:** Calibration error <15% (acceptable for MVP)
- **Phase 3 target:** Calibration error <10% (production-grade)
- **Method:** Platt scaling or isotonic regression on validation set

### Confidence Bins:
| Bin | Range | Interpretation | Action |
|-----|-------|----------------|--------|
| **Very Low** | 0.0 - 0.4 | No clear pattern | Don't generate signal (filtered out) |
| **Low** | 0.4 - 0.6 | Weak evidence | Generate "watch" signal, low priority |
| **Medium** | 0.6 - 0.75 | Moderate evidence | Generate signal, normal priority |
| **High** | 0.75 - 0.9 | Strong evidence | Generate signal, high priority |
| **Very High** | 0.9 - 1.0 | Extremely strong | Rare; flag for human review (possible overfitting) |

**Guardrail:** If confidence >0.9, Risk Gate flags for review (might be overconfident).

---

## Rationale Field (Explainability)

Every signal must include a **rationale** that explains:
1. **What pattern triggered this signal?** (e.g., "FDA approvals historically bullish")
2. **What's the evidence?** (e.g., "12 similar events in 2020-2025, avg +8% return in 24h")
3. **Why this confidence score?** (e.g., "High variance in outcomes → medium confidence")

### Good Rationale Examples:
- ✅ "Historical precedent: FDA approvals for biotech stocks (n=47, 2020-2025) led to avg +12% return in 24h, but with high variance (σ=8%). Confidence score reflects this uncertainty."
- ✅ "Earnings guidance cuts for AAPL (n=5, 2020-2025) triggered avg 3% intraday move. Direction was mixed (3 down, 2 up), hence 'volatility spike' vs directional signal."

### Bad Rationale Examples:
- ❌ "This stock will go up." (No explanation, overconfident)
- ❌ "My model says so." (Black box, not helpful)
- ❌ "FDA approval is good news." (Too generic, no evidence)

---

## Uncertainty Statement (What We Don't Know)

Every signal must include an **uncertainty** field that acknowledges:
1. **Known unknowns** (e.g., "Direction uncertain; could move either way")
2. **Data limitations** (e.g., "Small sample size (n=5); low statistical power")
3. **Regime dependence** (e.g., "Pattern holds in bull markets but fails in recessions")

### Good Uncertainty Examples:
- ✅ "Direction uncertain (could move up or down). Supply chain issues are complex and market reaction depends on broader tech sector sentiment."
- ✅ "Small sample size (n=7 similar events). Pattern may not generalize to current market regime."
- ✅ "Historical data is 2020-2025; COVID-era volatility may not apply to current market conditions."

### Bad Uncertainty Examples:
- ❌ "" (Empty field — every signal MUST have uncertainty statement)
- ❌ "None" (Overconfident; there's always uncertainty)
- ❌ "Anything can happen" (Too vague; not helpful)

---

## Impact Window (Time Horizon)

Signals must specify a **time window** for predicted impact:
- **1h** — Very short-term (intraday traders)
- **4h** — Short-term (day traders)
- **24h** — Medium-term (swing traders)
- **1w** — Long-term (position traders)

**Phase 1 focus:** 4h and 24h windows (easier to validate, less noisy than 1h).

---

## Citations (Provenance Chain)

Every signal must cite its sources:
1. **Source event** (the news/filing that triggered this signal)
2. **Historical data** (what past events does this resemble?)
3. **Model version** (which model generated this signal?)

### Citation Schema:
```json
{
  "type": "event",
  "id": "evt_20260309_001",
  "url": "https://sec.gov/...",
  "description": "Apple Q2 guidance revision (8-K filing)"
}
```
```json
{
  "type": "historical_data",
  "description": "AAPL guidance revisions 2020-2025 (n=12)",
  "query": "SELECT * FROM events WHERE ticker='AAPL' AND event_type='guidance_revision' AND date > '2020-01-01'"
}
```

**Guardrail:** Risk Gate rejects signals with no citations.

---

## Evidence Array (RAG-Powered)

Every signal must include an **evidence** array — retrieved similar historical events that ground the hypothesis. This is what makes confidence scores *trustworthy*: "0.78 confidence" means nothing without showing what it's based on.

### Evidence Item Schema:
```json
{
  "event_id": "evt_20250815_042",
  "event_summary": "AAPL Q3 2025 guidance cut by 3%, supply chain concerns cited",
  "ticker": "AAPL",
  "outcome": "+2.8% intraday move (direction: down then recovery)",
  "similarity_score": 0.94,
  "time_delta": "7 months ago"
}
```

### Evidence Fields:
| Field | Type | Description |
|-------|------|-------------|
| **event_id** | string | ID of the historical event in our database |
| **event_summary** | string | What happened (human-readable) |
| **ticker** | string \| null | Which company (null for sector-wide events) |
| **outcome** | string | What was the market reaction |
| **similarity_score** | float (0.0-1.0) | Cosine similarity to the triggering event |
| **time_delta** | string | How long ago this happened (human-readable) |

### Evidence Quality Rules:
- **Minimum evidence:** Every signal should have at least 1 evidence item (Risk Gate warns if 0)
- **Ideal evidence:** 3-5 items with similarity_score >0.70
- **Cross-sector bonus:** Evidence from different tickers/sectors strengthens the signal (pattern is generalizable, not ticker-specific)
- **Recency weighting:** More recent evidence is more relevant (market regimes change)
- **Staleness warning:** If all evidence is >3 years old, add uncertainty note about regime change

### How Evidence is Retrieved:
1. Event summary is embedded using text-embedding-3-small (or equivalent)
2. Vector store (Pinecone/Qdrant) returns top-K similar historical events (K=10)
3. Filter to similarity_score >0.70
4. Enrich with actual market outcomes from PostgreSQL
5. Rank by similarity_score, take top 3-5

---

## Signal Generation Pipeline
```
Event (with entities + event_type)
    → Impact Hypothesis Agent (RAG-powered)
        → Embed event summary (text-embedding-3-small)
        → Retrieve top-K similar events from vector store (Pinecone/Qdrant)
        → Query historical data (Alpha Vantage, Finnhub) for structured lookups
        → Combine: semantic retrieval (cross-sector analogues) + SQL (exact matches)
        → Compute avg return, volatility, volume in impact window (1h, 4h, 24h)
        → Fit statistical model (e.g., "FDA approvals → +8% avg, σ=5%")
        → Generate confidence score (based on sample size, variance, evidence quality)
        → Attach evidence[] array (top 3-5 similar events with outcomes)
    → Risk/Policy Gate Agent
        → Validate citations (event exists? historical data query valid?)
        → Validate evidence (similarity scores reasonable? outcomes present?)
        → Check confidence bounds (reject if >0.9 without human review)
        → Enforce disclaimers ("not investment advice")
        → Append uncertainty statement (if missing)
    → Signal Store (PostgreSQL)
    → Upsert event embedding to vector store (grows knowledge base)
    → API/UI (serve to users)
```

---

## Evaluation Metrics

### Offline Metrics (Pre-Launch):
- **Confidence calibration:** Plot predicted confidence vs. actual accuracy
  - Target: Points fall on diagonal line (perfect calibration)
  - Metric: Brier score, log loss
- **Signal precision:** % of signals that were "correct" (outcome matched prediction)
  - Target: >55% (better than random 50%)
- **Signal recall:** % of material events that generated signals (did we miss any?)
  - Target: >70% (catch most important events)

### Online Metrics (Post-Launch):
- **Accuracy vs. baseline:** Compare signal outcomes to random baseline
  - Target: +10-15% improvement over random
- **User engagement:** % of signals that users click (to see rationale/citations)
  - Target: >30% click-through rate
- **User feedback:** Thumbs up/down on signals
  - Target: >60% thumbs up

---

## Signal Quality Guardrails

### Pre-Launch Guardrails (Phase 1):
- [ ] Every signal has a confidence score (0.0 - 1.0)
- [ ] Every signal has a rationale (non-empty, >50 chars)
- [ ] Every signal has an uncertainty statement (non-empty, >20 chars)
- [ ] Every signal has at least one citation (event or historical data)
- [ ] Every signal has an evidence[] array (warn if empty, ideal: 3-5 items)
- [ ] Evidence items have similarity_score >0.70
- [ ] Confidence calibration error <15% on validation set
- [ ] Signal accuracy >55% on backtest set

### Post-Launch Guardrails (Phase 2+):
- [ ] Monitor live signal accuracy (compare predictions to outcomes)
- [ ] Alert if accuracy drops below 50% (worse than random)
- [ ] A/B test new models (don't deploy if worse than baseline)
- [ ] Monthly drift checks (are models degrading over time?)

---

## Risk Gate Rules (Compliance)

The **Risk/Policy Gate Agent** enforces these rules:

### Rule 1: No Investment Advice Language
**Block signals containing:**
- "Buy", "Sell", "Hold"
- "Guaranteed", "Sure thing", "Can't lose"
- "You should", "You must", "Recommended action"

**Allowed:**
- "High probability", "Medium confidence", "Historically"
- "Based on precedent", "Similar events"

### Rule 2: Disclaimer Enforcement
**Every signal must include (appended by Risk Gate):**
> "This is not investment advice. Signals are educational and based on historical patterns which may not repeat. Past performance does not guarantee future results. You are solely responsible for your trading decisions."

### Rule 3: Citation Validation
**Reject signals if:**
- No citations provided
- Event ID doesn't exist in database
- Historical data query is invalid

### Rule 4: Confidence Bounds
**Reject signals if:**
- Confidence <0.4 (too uncertain; don't generate signal)
- Confidence >0.9 without human review (possible overfitting)

### Rule 5: Uncertainty Requirement
**Reject signals if:**
- Uncertainty field is empty
- Uncertainty is generic ("Anything can happen")

---

## Example Signals (Good vs. Bad)

### ✅ Good Signal Example 1:
```json
{
  "signal_text": "High probability of short-term volatility increase for NVDA in next 4 hours",
  "confidence": 0.76,
  "rationale": "Earnings beat by 15% vs expectations. Historical data (n=18, 2020-2025) shows NVDA earnings beats led to avg 4.2% intraday move (σ=2.8%). High volatility expected regardless of direction.",
  "uncertainty": "Direction uncertain (50/50 up vs down in historical data). Broader semiconductor sector sentiment will influence direction."
}
```

### ✅ Good Signal Example 2:
```json
{
  "signal_text": "Medium confidence of positive price drift for MRNA in next 24 hours",
  "confidence": 0.64,
  "rationale": "FDA approval for biotech stocks (n=47, 2020-2025) led to avg +12% return in 24h. MRNA has lower beta than avg biotech, so expecting +6-8% move.",
  "uncertainty": "Small sample size for MRNA-specific approvals (n=3). Market conditions in 2026 may differ from 2020-2025 data. Regulatory changes could affect sentiment."
}
```

### ❌ Bad Signal Example 1 (Overconfident):
```json
{
  "signal_text": "AAPL will go up 10% tomorrow",
  "confidence": 0.95,
  "rationale": "My model says so.",
  "uncertainty": ""
}
```
**Why it's bad:**
- Overconfident (0.95 is too high, likely overfitting)
- No historical evidence cited
- No uncertainty statement
- Language is too definitive ("will go up")

### ❌ Bad Signal Example 2 (No Explainability):
```json
{
  "signal_text": "Watch TSLA",
  "confidence": 0.5,
  "rationale": "Elon tweeted something.",
  "uncertainty": "Anything can happen."
}
```
**Why it's bad:**
- Vague signal ("watch" without specifics)
- No historical data cited
- Uncertainty is generic (not helpful)
- Low confidence (should be filtered out)

---

## Future Enhancements (Post-MVP)

### Phase 3+:
- **Multi-signal aggregation:** Combine multiple weak signals into stronger composite signal
- **Sector-level signals:** "Biotech sector likely to see volatility spike due to FDA news"
- **Custom signal builder:** Users define their own event types + impact models
- **Backtesting UI:** Users can test signals on historical data

### Phase 4+:
- **Portfolio-aware signals:** Personalized signals based on user's holdings
- **Execution integration:** Link signals to brokerage APIs (trade directly from signal)
- **Social signals:** Aggregate user feedback to improve model ("wisdom of the crowd")

---

## Appendix: Related Documents

- `RESEARCH/PRD.md` — Product vision, signal requirements
- `RESEARCH/ARCHITECTURE.md` — Impact Hypothesis Agent design
- `RESEARCH/EVALUATION.md` — Signal accuracy metrics, backtesting
- `RESEARCH/RISKS_GUARDRAILS.md` — Compliance, Risk Gate rules
- `ROLES.md` — Fairoz owns signal generation pipeline

---

**Document Status:** Draft v0.2
**Last Updated:** March 2026
**Next Review:** After Phase 1 signal generation prototype
**Changelog:** v0.2 — Added evidence[] array to signal schema, Evidence section with quality rules and retrieval flow, updated signal generation pipeline to include vector store retrieval + upsert. Informed by AgentPredict architecture review.
