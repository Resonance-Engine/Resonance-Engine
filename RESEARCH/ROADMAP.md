# Resonance Engine — Product Roadmap
## Time Horizons & Milestones

**Last Updated:** March 2026
**Owner and Co-Owner:** Reiyyan (Product & Architecture) and Fairoz (AI/ML & Data Platform)
**Reviewers:** Reiyyan - Product & Architecture Lead
**Revision:** v0.2 — Added vector store, RAG-powered impact hypothesis, meaningful change gating, and gateway separation milestones (informed by AgentPredict architecture review)

---

## Roadmap Philosophy

We prioritize **learning velocity** over feature completeness in early stages. Each phase is designed to:
- Validate core assumptions (does real-time news intelligence actually help retail traders?)
- Build technical foundations that won't need to be rewritten
- Create feedback loops (eval metrics, user testing, market validation)

**Guiding principle:** Ship small, measure rigorously, iterate fast.

---

## Phase 0: Foundation (Weeks 1-4) — **Current Phase**

**Goal:** Prove the core pipeline works end-to-end with minimal features.

### Deliverables:
- ✅ **Documentation scaffold** (README, ROLES, PRD, RESEARCH folder structure)
- 🔄 **EDGAR ingestion prototype**
  - Pull 8-K filings from SEC bulk API
  - Parse XML to extract company name, CIK, filing date, item codes
  - Store in PostgreSQL events table
  - Target: Ingest 100 filings, verify data quality
- 🔄 **Entity resolution MVP**
  - Build ticker/CIK mapper using SEC companyfacts.zip
  - Handle basic ambiguity ("Apple Inc." → AAPL vs "Apple Hospitality REIT" → APLE)
  - Test on 50 hand-labeled examples, measure precision/recall
- 🔄 **Event extraction baseline**
  - Implement FinBERT sentiment classifier
  - Add Loughran-McDonald lexicon lookups
  - Create simple keyword-based event type classifier (earnings, guidance, FDA, lawsuit)
  - Evaluate on 100 hand-labeled news articles
- 🔄 **Meaningful change gating**
  - Implement content-hash deduplication at ingestion layer
  - Add story clustering (same entity + event type + ±2h window → skip duplicates)
  - Filter boilerplate amended filings (diff against original, skip if <5% text delta)
  - Gate on material change before events enter the agent pipeline
- 🔄 **Evaluation harness v0.1**
  - Define offline metrics (entity resolution accuracy, event extraction F1)
  - Create labeled test set (100 events with ground truth)
  - Set up experiment tracking (MLflow or W&B)

### Success Criteria:
- [ ] Can ingest 100 EDGAR filings in <10 minutes
- [ ] Entity resolution achieves >85% precision on test set
- [ ] Event extraction F1 score >0.60 (baseline, will improve)
- [ ] Meaningful change gate filters >30% of duplicate/boilerplate events
- [ ] All code has basic unit tests
- [ ] Documentation is up-to-date (PRD, DATA_NOTES, ARCHITECTURE)

### Timeline: 4 weeks
**Week 1:** Documentation + EDGAR ingestion prototype  
**Week 2:** Entity resolution MVP + test set creation  
**Week 3:** Event extraction baseline + evaluation metrics  
**Week 4:** Integration testing + documentation updates

---

## Phase 1: MVP Signal Generation (Weeks 5-10)

**Goal:** Generate first testable signals with confidence scores and explainability.

### Deliverables:
- **Agentic workflow v1**
  - Implement multi-agent pipeline (Ingestion → Entity Resolution → Event Extraction → Impact Hypothesis → Risk Gate)
  - Use LangGraph or equivalent for orchestration
  - Typed outputs between agents (JSON schemas)
  - Audit trail (log every intermediate artifact)
- **Vector store setup (Pinecone/Qdrant)**
  - Provision vector store with namespaces per source (sec_edgar, gdelt, newsapi)
  - Implement embedding pipeline (text-embedding-3-small or equivalent)
  - Upsert all Phase 0 processed events to build initial knowledge base
  - Implement retriever: top-K similar events by cosine similarity, filter >0.70
- **Impact hypothesis agent (RAG-powered)**
  - Pull historical market data (Alpha Vantage / Finnhub)
  - Label events with post-event returns/volatility windows (1h, 4h, 24h)
  - Retrieve similar historical events from vector store (cross-sector analogues)
  - Combine structured SQL lookups + semantic retrieval for hypothesis grounding
  - Build simple statistical model: "events like this historically led to X% move with Y% probability"
  - Attach evidence[] array to every signal (top 3-5 similar events with outcomes)
  - Confidence calibration: ensure probabilities match outcomes
- **Signal schema v1**
  - Define JSON schema for signals (see SIGNAL_SPEC.md)
  - Implement confidence scoring (0.0–1.0, calibrated to real outcomes)
  - Add rationale field (why this signal was generated)
  - Include uncertainty statement ("what we don't know")
- **Risk/Policy Gate agent**
  - Enforce "not investment advice" language
  - Block overconfident claims ("guaranteed to go up")
  - Validate citations (every signal must link to source event)
  - Log rejected outputs (for debugging + compliance audits)
- **Backtesting harness v0.2**
  - Implement look-ahead bias checks (point-in-time data only)
  - Survivorship bias handling (include delisted stocks)
  - Overfitting detection (Bailey et al. methodology)
  - Monthly drift monitoring (are models degrading?)

### Success Criteria:
- [ ] Generate 50 signals on historical test set
- [ ] Confidence calibration error <15% (acceptable for MVP)
- [ ] Signal accuracy >55% vs. random baseline (+5% edge minimum)
- [ ] False positive rate <30% (will tighten in later phases)
- [ ] Every signal has citation trail + rationale + evidence[] array
- [ ] Vector store contains 500+ embedded historical events
- [ ] Average evidence retrieval returns 3+ items with similarity >0.70
- [ ] Risk Gate blocks 100% of non-compliant outputs in test set

### Timeline: 6 weeks
**Week 5-6:** Agentic workflow implementation + agent integration  
**Week 7-8:** Impact hypothesis agent + market data labeling  
**Week 9:** Risk Gate + backtesting harness  
**Week 10:** End-to-end testing + evaluation report

---

## Phase 2: User-Facing MVP (Weeks 11-16)

**Goal:** Ship a minimal web app that real users can test.

### Deliverables:
- **Event card UI (frontend)**
  - Card-based layout (similar to Twitter/Reddit)
  - Display: source, timestamp, entities, event type, summary, confidence
  - Click to expand: full text, citations, impact hypotheses, historical charts
  - Color-coding by event type (green/red/yellow)
- **Signal dashboard (frontend)**
  - Sortable/filterable list of signals
  - Columns: timestamp, ticker, signal text, confidence, rationale
  - Click signal → see full event card + citation trail
  - User preferences: filter by confidence threshold, event type, tickers
- **Backend API v1**
  - REST endpoints: `/events`, `/signals`, `/entities/{ticker}`
  - Rate limiting (prevent abuse)
  - API documentation (Swagger/OpenAPI)
- **WebSocket gateway (separate service)**
  - Split real-time signal push into dedicated gateway service
  - `/ws/signals` — subscribe to streaming signal updates
  - Buffer last N signals for late-joining clients (cursor-based catch-up)
  - Fan-out to all connected browser clients, silent disconnect cleanup
  - Message envelope: `{"type": "signal"|"event", "data": {...}}`
- **News ingestion expansion**
  - Add GDELT ingestion (global news at scale)
  - Add NewsAPI ingestion (breaking news, developer tier)
  - Implement deduplication (same story from multiple sources)
  - Prioritization logic (high-impact events first)
- **User onboarding flow**
  - Simple signup (email + password, no brokerage linking yet)
  - Disclaimer page ("not investment advice," educational use only)
  - Quick tutorial (how to read event cards, interpret signals)
  - Feedback mechanism (thumbs up/down on signals)

### Success Criteria:
- [ ] 10 alpha testers can sign up and view signals
- [ ] Frontend loads event cards in <2 seconds
- [ ] Real-time signal push notifications work (WebSocket stable)
- [ ] API uptime >95% during alpha test
- [ ] Collect feedback from alpha testers (survey + in-app ratings)
- [ ] Zero legal/compliance issues flagged by Risk Gate in production

### Timeline: 6 weeks
**Week 11-12:** Event card UI + signal dashboard frontend  
**Week 13-14:** Backend API + WebSocket push notifications  
**Week 15:** News ingestion expansion (GDELT + NewsAPI)  
**Week 16:** Alpha testing + user feedback collection

---

## Phase 3: Validation & Iteration (Weeks 17-24)

**Goal:** Improve signal quality based on real user feedback and backtest performance.

### Deliverables:
- **Model improvements**
  - Fine-tune FinBERT on financial news corpus
  - Add custom event extractors (train on labeled data)
  - Improve entity resolution (handle edge cases from alpha testing)
  - Recalibrate confidence scores based on production outcomes
- **Evaluation enhancements**
  - Track live signal accuracy (compare predictions to actual market moves)
  - Build feedback loop (user ratings → model retraining)
  - A/B testing framework (test new models vs. baselines)
  - Drift detection dashboard (alert when models degrade)
- **Feature additions (based on user feedback)**
  - Watchlist (users pick tickers to monitor)
  - Email/SMS alerts (configurable thresholds)
  - Historical signal archive (search past signals)
  - Export to CSV/JSON (for power users)
- **Scalability improvements**
  - Optimize ingestion pipeline (handle 1000+ events/day)
  - Add caching layer (Redis for frequently accessed entities)
  - Database indexing (faster queries on events/signals tables)
  - Monitoring/alerting (Prometheus + Grafana for system health)
- **Expand data sources (if budget allows)**
  - Consider paid tier of NewsAPI (more requests/day)
  - Add earnings call transcripts (free sources like Seeking Alpha API)
  - Integrate social signals (Reddit sentiment, if compliant with ToS)

### Success Criteria:
- [ ] Signal accuracy improves to >60% (+10% edge over random)
- [ ] Confidence calibration error <10% (production-grade)
- [ ] False positive rate <20% (tighter than MVP)
- [ ] User retention: 50%+ of alpha testers still active after 4 weeks
- [ ] System handles 1000+ events/day with <5 min latency
- [ ] Net Promoter Score (NPS) >30 from alpha users

### Timeline: 8 weeks
**Week 17-18:** Model fine-tuning + evaluation enhancements  
**Week 19-20:** Feature additions (watchlist, alerts, export)  
**Week 21-22:** Scalability improvements (caching, indexing, monitoring)  
**Week 23-24:** Beta launch + user acquisition experiments

---

## Phase 4: Public Beta & Go-To-Market (Weeks 25-36)

**Goal:** Launch to broader audience, validate product-market fit, explore monetization.

### Deliverables:
- **Public beta launch**
  - Open signups (no invite required)
  - Marketing site (landing page with demo video, testimonials)
  - SEO/content marketing (blog posts, tutorials, case studies)
  - Social media presence (Twitter/X, Reddit r/algotrading)
- **Mobile app (optional, if user feedback demands it)**
  - iOS/Android apps (React Native or native)
  - Push notifications (critical for breaking news alerts)
  - Same features as web (event cards, signals, watchlist)
- **Pricing model experiments**
  - Free tier: 10 signals/day, basic event cards
  - Premium tier ($9.99/month): unlimited signals, advanced filters, API access
  - Track conversion rate (free → paid)
  - A/B test pricing ($7.99 vs $9.99 vs $14.99)
- **Analytics & attribution pipeline**
  - Track user behavior (which signals get clicked, which get ignored)
  - Measure signal ROI (did users act on signals? self-reported via surveys)
  - Attribution modeling (which marketing channels bring best users)
- **Community features (if traction warrants it)**
  - Signal sharing (users can share event cards on social media)
  - Leaderboards (top signals by accuracy, if legally safe)
  - Forum/Discord for user discussions

### Success Criteria:
- [ ] 500+ registered users within first month
- [ ] 100+ DAU (daily active users)
- [ ] 10%+ conversion rate (free → paid)
- [ ] <5% churn rate (users canceling premium)
- [ ] Product-market fit validation (NPS >40, strong user testimonials)
- [ ] Press coverage (TechCrunch, Bloomberg, fintech blogs)

### Timeline: 12 weeks
**Week 25-28:** Public beta launch + marketing push  
**Week 29-32:** Pricing experiments + mobile app (if needed)  
**Week 33-36:** Community features + press outreach

---

## Phase 5: Scale & Expand (Month 10+)

**Goal:** Productize for institutional clients, expand to global markets, build moat.

### Long-Term Vision (12-24 months):
- **Institutional product**
  - B2B API for hedge funds, prop shops, family offices
  - Higher pricing ($500-$5000/month for API access)
  - SLA guarantees (99.9% uptime, <1 min signal latency)
  - Custom integrations (Slack, Bloomberg Terminal, trading platforms)
- **Global market expansion**
  - Support international exchanges (LSE, TSE, Euronext)
  - Multi-language news ingestion (non-English sources)
  - Regulatory compliance (GDPR, MiFID II for EU users)
- **Advanced features**
  - Portfolio integration (sync with brokerage accounts, personalized signals)
  - Backtesting tool (users can test signals on historical data)
  - Algorithmic execution (partner with execution platforms, not build in-house)
  - Custom signal builder (users define their own event types + impact models)
- **Data moat**
  - Proprietary labeled dataset (millions of events + market reactions)
  - Exclusive data partnerships (early access to niche news sources)
  - Network effects (more users → more feedback → better models)

### Success Criteria (24-month targets):
- [ ] 10,000+ registered users
- [ ] 1,000+ paying subscribers (retail)
- [ ] 10+ institutional clients (B2B API)
- [ ] $500k+ ARR (annual recurring revenue)
- [ ] Raise Series A funding (if pursuing VC route)
- [ ] Team grows to 5-10 people (hire ML engineer, backend engineer, designer, marketer)

---

## Key Milestones Summary

| Phase | Timeline | Key Deliverable | Success Metric |
|-------|----------|----------------|----------------|
| **Phase 0: Foundation** | Weeks 1-4 | EDGAR ingestion + entity resolution + eval harness + change gating | >85% entity resolution precision |
| **Phase 1: MVP Signals** | Weeks 5-10 | Vector store + RAG-powered impact hypothesis + Risk Gate | >55% signal accuracy, 500+ embedded events |
| **Phase 2: User-Facing MVP** | Weeks 11-16 | Event cards UI + signal dashboard + WS gateway + alpha testing | 10 alpha testers, >95% uptime |
| **Phase 3: Validation** | Weeks 17-24 | Model improvements + user feedback loop | >60% signal accuracy, NPS >30 |
| **Phase 4: Public Beta** | Weeks 25-36 | Public launch + pricing experiments + marketing | 500+ users, 10%+ conversion |
| **Phase 5: Scale** | Month 10+ | Institutional product + global expansion | 10k users, $500k ARR |

---

## Risk Factors & Contingencies

### Risk: User acquisition is slower than expected
**Mitigation:**
- Focus on niche communities (r/algotrading, FinTwit, quant forums)
- Create high-quality content (tutorials, backtests, case studies)
- Offer referral incentives (free premium month for each referral)

### Risk: Signal accuracy doesn't improve beyond 55-60%
**Mitigation:**
- Narrow scope (focus on specific event types where models work well)
- Increase transparency (even mediocre signals are valuable if well-explained)
- Pivot to "news intelligence dashboard" vs. "trading signals" (lower bar)

### Risk: Legal/compliance issues with "investment advice" claims
**Mitigation:**
- Work with compliance lawyer early (Phase 2)
- Strong disclaimers on every output
- Consider registering as RIA (if B2B institutional product takes off)

### Risk: Competitors (Bloomberg, RavenPack) copy our approach
**Mitigation:**
- Focus on retail UX (they're too slow to serve retail well)
- Build proprietary dataset (our labeled events → our moat)
- Network effects (more users → better feedback → better models)

---

## Open Questions for Future Phases

1. **Should we build our own execution layer?** (Or partner with existing brokerages?)
2. **International expansion: which markets first?** (UK? EU? Asia?)
3. **Fundraising strategy:** Bootstrap to profitability or raise VC?
4. **Team growth:** When do we hire? What roles first? (ML engineer, backend engineer, designer, marketer)
5. **Regulatory strategy:** Do we need to register as RIA if we start recommending trades?

---

## Appendix: Related Documents

- `RESEARCH/PRD.md` — Product vision, user personas, core features
- `RESEARCH/DATA_NOTES.md` — Data sources, APIs, constraints
- `RESEARCH/ARCHITECTURE.md` — System design, tech stack
- `RESEARCH/EVALUATION.md` — Metrics, backtesting methodology
- `ROLES.md` — Team ownership, decision-making framework

---

**Document Status:** Draft v0.2
**Last Updated:** March 2026
**Next Review:** End of Phase 0 (Week 4)
**Changelog:** v0.2 — Added meaningful change gating (Phase 0), vector store + RAG-powered impact hypothesis (Phase 1), WebSocket gateway separation (Phase 2), evidence[] requirements. Informed by AgentPredict architecture review.
