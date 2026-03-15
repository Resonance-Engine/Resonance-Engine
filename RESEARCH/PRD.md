# Product Requirements Document (PRD)
## Resonance Engine — Real-Time News Intelligence for Retail Traders

**Version:** 0.1 (Early Stage)  
**Last Updated:** March 2026  
**Owner and Co-Owner:** Reiyyan (Product & Architecture) and Fairoz (AI/ML & Data Platform)  
**Reviewers:** Reiyyan - Product & Architecture Lead



---

## Executive Summary

**Resonance Engine** is a financial computing and market intelligence platform that transforms unstructured news and public disclosures into structured, actionable insights for retail traders.

**Core value proposition:**  
Reduce the **latency of understanding** — not just "fast data," but fast, credible interpretation of breaking information and its likely market impact.

**Wedge strategy:**  
Start with **real-time event intelligence** (news → structured events → impact hypotheses → signals), then expand into analytics, optimization, and algorithmic execution.

**Target user (MVP):**  
Retail traders (individual investors, part-time traders, small prop traders) who need to act on breaking news but lack institutional-grade tools or teams.

---

## Problem Statement

### Current pain points for retail traders:

1. **Information overload**: Breaking news floods in from dozens of sources (Twitter/X, Reddit, news APIs, SEC filings), but most traders can't process it fast enough.

2. **Lack of context**: A headline says "FDA approval" or "earnings beat" — but what does that *actually* mean for price/volatility? What happened historically in similar situations?

3. **No structured workflow**: Traders manually check multiple tabs (news, filings, charts, forums), losing time and missing connections.

4. **Generic sentiment tools**: Existing tools (TradingView news, basic sentiment APIs) provide shallow "positive/negative" scores without nuance, confidence, or rationale.

5. **Institutional tools are inaccessible**: Bloomberg Terminal costs $24k/year. Reuters, RavenPack, and Benzinga News Analytics are priced for institutions, not individuals.

### What retail traders *actually* need:

- **Event cards** that explain *what happened*, *who's affected*, and *why it matters*
- **Impact hypotheses** that say "here's what tends to happen next, with uncertainty bounds"
- **Signals** that are testable, explainable, and come with confidence scores
- **Transparency**: Show me *why* the system thinks this matters (citations, historical precedents, entity links)

---

## Solution Overview

### What we're building (MVP scope):

A **real-time news → events → signals pipeline** with:

1. **Ingestion layer**: Pull from SEC EDGAR (filings), GDELT (global news), NewsAPI (breaking news), and optionally Reddit/X (community signals)

2. **Entity resolution**: Map messy company mentions to canonical tickers/CIKs (e.g., "Apple" → AAPL, CIK 0000320193)

3. **Event extraction**: Convert unstructured text into structured events (e.g., "FDA approval," "earnings guidance revision," "lawsuit filed")

4. **Impact hypothesis generation**: Produce scenario-based predictions ("historically, similar FDA approvals led to +8% avg return in 24h, but volatility also spiked")

5. **Signal generation**: Output actionable, testable statements with confidence scores ("High likelihood of short-term volatility increase; direction uncertain")

6. **User-facing outputs**: Event cards (web UI), signal alerts (push notifications), explainability (citation trails)

### What makes this different:

| Feature | Existing Tools | Resonance Engine |
|---------|---------------|------------------|
| **Output type** | Sentiment score (0.0–1.0) | Structured event + impact hypothesis + confidence |
| **Explainability** | Black box | Every signal has citations, entity links, historical precedents |
| **Uncertainty** | Overconfident ("BUY NOW!") | Explicit confidence bounds, "what we don't know" |
| **Target user** | Institutional quants | Retail traders (accessible pricing, clear UX) |
| **Compliance** | Often vague disclaimers | "Not investment advice" enforced by Risk/Policy Gate Agent |

---

## User Personas

### Primary: Alex, the Part-Time Retail Trader
- **Background**: Works full-time in tech, trades 5–10 hours/week
- **Pain**: Misses breaking news during work hours, relies on Reddit/Twitter for alerts (often too late or unreliable)
- **Need**: Real-time event alerts with context ("FDA approved XYZ drug → historically bullish for biotech → watch for volatility spike")
- **Success metric**: Catches 80% of major market-moving events within 10 minutes of public disclosure

### Secondary: Jamie, the Small Prop Trader
- **Background**: Trades full-time from home, manages 6-figure portfolio
- **Pain**: Spends 2+ hours/day manually checking news feeds, SEC filings, earnings calendars
- **Need**: Automated event ingestion + structured output so she can focus on execution, not data wrangling
- **Success metric**: Reduces daily news-checking time by 50%, increases trade opportunities identified by 30%

---

## Core Features (MVP)

### 1. Event Cards
**What it is:** A structured representation of a breaking news item.

**Schema (draft):**
```json
{
  "event_id": "evt_20260309_001",
  "timestamp": "2026-03-09T14:32:00Z",
  "source": "SEC EDGAR 8-K",
  "url": "https://sec.gov/...",
  "entities": [
    {"ticker": "AAPL", "cik": "0000320193", "name": "Apple Inc."}
  ],
  "event_type": "earnings_guidance_revision",
  "summary": "Apple revised Q2 revenue guidance downward by 5% citing supply chain delays",
  "novelty_score": 0.92,
  "confidence": 0.87,
  "impact_hypotheses": [
    {
      "scenario": "short_term_volatility_spike",
      "probability": 0.78,
      "rationale": "Historical precedent: guidance cuts typically trigger 2–5% intraday moves"
    }
  ],
  "citations": ["SEC 8-K filing", "Historical earnings data 2020–2025"],
  "suggested_followups": ["Check supplier filings (TSMC, Foxconn)", "Review analyst revisions"]
}
```

**UI mockup (planned):**
- Card-based layout (like Twitter/Reddit posts)
- Color-coded by event type (green = positive, red = negative, yellow = neutral/mixed)
- Click to expand: full text, citations, entity links, historical chart overlays

### 2. Signals
**What it is:** A testable, actionable statement with confidence bounds.

**Examples:**
- "High probability (78%) of short-term volatility increase for AAPL in next 4 hours"
- "Medium confidence (62%) of positive price drift for biotech sector after FDA approval news"
- "Low confidence (42%) on directional move; historically mixed outcomes for this event type"

**Requirements:**
- Every signal must include:
  - Confidence score (calibrated probability)
  - Rationale (which features/patterns triggered it)
  - Uncertainty statement ("what we don't know")
  - Citation trail (links to source events, historical data)

**Output channels (MVP):**
- Web dashboard (sortable, filterable list)
- Push notifications (user-configurable thresholds)
- API endpoint (for programmatic access)

### 3. Agentic Workflow (under the hood)

**Agent pipeline:**
1. **Ingestion Agent**: Standardizes incoming documents (source, timestamp, URL, raw text), deduplicates, assigns stable IDs
2. **Entity Resolution Agent**: Maps mentions to canonical tickers/CIKs, handles ambiguous names ("Apple" vs "Apple Hospitality REIT")
3. **Event Extraction Agent**: Converts text into event schema (FDA approval, earnings beat, lawsuit), with polarity and confidence
4. **Impact Hypothesis Agent**: Produces scenario-based hypotheses using historical market reaction data
5. **Risk/Policy Gate Agent**: Enforces "not investment advice" wording, blocks overconfident language, validates citations

**Why agentic?**
- Decomposed tasks → easier to debug, evaluate, and iterate
- Tool use (retrievers, parsers, symbol maps) → more accurate than end-to-end LLM
- Typed outputs → clear contracts between stages, no "hallucination drift"
- Auditable → every signal has a provenance chain

### 4. Evaluation & Backtesting Harness

**Offline metrics (NLP quality):**
- Entity resolution precision/recall (ticker mapping accuracy)
- Event extraction F1 score (compared to hand-labeled test set)
- Confidence calibration (are 70% confidence predictions actually right 70% of the time?)

**Market reaction metrics (signal quality):**
- Label signals with post-event returns/volatility windows (1h, 4h, 24h)
- Measure signal accuracy vs. random baseline
- Track false positive rate (signals that didn't pan out)

**Backtesting safety checks:**
- **Look-ahead bias**: Ensure all data is point-in-time (no peeking at future filings/prices)
- **Survivorship bias**: Include delisted stocks in historical tests
- **Overfitting**: Use Bailey et al. "Probability of Backtest Overfitting" methodology

**Guardrails:**
- If backtest shows <55% accuracy → do NOT ship signal type
- If confidence calibration is off by >10% → retrain/recalibrate
- Monthly drift checks (are models degrading over time?)

---

## Non-Goals (what we're NOT building, at least not yet)

1. **Automated trade execution** (not in MVP; legal/regulatory complexity)
2. **Portfolio management** (no "recommended allocation" — that's investment advice territory)
3. **Social trading platform** (no copy-trading, no leaderboards — liability risk)
4. **Proprietary data collection** (no web scraping, no insider info — legal minefield)
5. **High-frequency trading** (latency requirements are different; we focus on minutes-to-hours, not microseconds)

---

## Success Metrics (MVP phase)

### User engagement:
- **Daily active users (DAU)**: Target 100+ within 3 months of launch
- **Event cards viewed per user**: Avg 10+ per session
- **Signal click-through rate**: 30%+ (users click to see rationale/citations)

### Signal quality:
- **Accuracy vs. random baseline**: +15% improvement
- **Confidence calibration error**: <10% (e.g., 70% confidence signals are right 65–75% of the time)
- **False positive rate**: <20% (signals that didn't lead to any meaningful market move)

### System reliability:
- **Ingestion latency**: 95% of events processed within 2 minutes of publication
- **Uptime**: 99%+ (event streaming should be always-on)
- **Data freshness**: No stale signals (timestamp integrity enforced)

---

## Technical Constraints & Dependencies

### Data sources (MVP tier):
- **SEC EDGAR**: Free, reliable, but limited to U.S. public companies
- **GDELT**: Free, global coverage, but noisy (requires heavy filtering)
- **NewsAPI**: Developer tier (100 requests/day free) — need caching/batching
- **Alpha Vantage / Finnhub**: Free tiers with rate limits (5 calls/min, 500/day) — need careful quota management

### Compute constraints:
- **LLM costs**: Running GPT-4/Claude on every news article = $$$. Need:
  - Batch processing (not real-time LLM calls for everything)
  - Smaller models for filtering/triage (FinBERT, lexicon-based pre-filters)
  - Caching of entity resolutions and event templates

### Latency targets:
- **Event ingestion → Event card creation**: <2 minutes (95th percentile)
- **Event card → Signal generation**: <5 minutes (including market data lookups)
- **Total end-to-end**: <10 minutes from news publication to user notification

### Compliance:
- **Not investment advice**: Every output must include disclaimer
- **No guarantees**: Confidence scores ≠ promises
- **Transparent limitations**: "What we don't know" must be surfaced
- **User agreement**: Terms of service must clarify educational use only

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data vendor rate limits** | Service degradation, missed events | Implement caching, batch API calls, prioritize high-value sources |
| **LLM hallucinations** | Incorrect event extraction, false signals | Multi-agent validation, typed outputs, human-in-the-loop for edge cases |
| **Market regime shifts** | Historical patterns stop working | Monthly model retraining, drift detection, confidence decay for old patterns |
| **Legal liability** | User loses money, blames us | Strong disclaimers, "not investment advice" enforced by policy gate, terms of service |
| **Competitors (Bloomberg, RavenPack)** | They copy our approach | Focus on retail UX (simplicity, explainability), not just features |

---

## Open Questions (to resolve before MVP launch)

1. **Pricing model**: Free tier with ads? Freemium ($9.99/month for premium signals)? B2B licensing to small funds?
2. **User onboarding**: Do we require brokerage account linking (to personalize signals to user's portfolio)? Or keep it generic?
3. **Mobile app**: Web-first or mobile-first? Push notifications are critical → may need iOS/Android apps early.
4. **Community features**: Do we allow users to share event cards / signal screenshots? (Viral growth vs. moderation burden)
5. **International markets**: Start U.S.-only (EDGAR, NYSE/NASDAQ) or support global equities (requires more data vendors)?

---

## Next Steps (Immediate Actions)

1. **Finalize data source contracts**: Confirm free-tier limits for NewsAPI, Alpha Vantage, Finnhub
2. **Build ingestion prototype**: EDGAR + GDELT → normalized event schema (first 100 events hand-labeled for eval)
3. **Entity resolution MVP**: Ticker/CIK mapper using SEC companyfacts.zip + fuzzy matching
4. **Event extraction baseline**: FinBERT sentiment + Loughran-McDonald lexicon + keyword rules
5. **Evaluation harness v0.1**: Offline metrics (precision/recall) + backtest safety checks
6. **UI mockups**: Event card design (Figma/Sketch) + signal dashboard wireframes

---

## Appendix: Related Documents

- `RESEARCH/DATA_NOTES.md` — Data sources, APIs, licensing details
- `RESEARCH/ARCHITECTURE.md` — System design (agents, streaming, services)
- `RESEARCH/SIGNAL_SPEC.md` — Signal schema, confidence calibration
- `RESEARCH/EVALUATION.md` — Metrics, backtesting methodology
- `RESEARCH/RISKS_GUARDRAILS.md` — Compliance, failure modes
- `RESEARCH/ROADMAP.md` — Time horizons, milestones
- `ROLES.md` — Team ownership areas

---

**Document Status:** Draft v0.1 — Open for feedback  
**Last Updated:** March 2026  
**Next Review:** After ingestion prototype (Week 2)
