# Risks, Guardrails & Compliance
## How We Stay Safe, Legal & Trustworthy

**Last Updated:** March 2026  
**Owner:** Product & Architecture Lead  
**Contributors:** Fairoz (AI/ML + Data Platform)

---

## Overview

Resonance Engine operates in a high-stakes domain (financial markets) where:
- Users can lose money based on our outputs
- Regulatory scrutiny is intense (SEC, FINRA, state securities laws)
- Reputation damage from bad signals is irreversible

**Core principle:** Err on the side of caution. Better to under-promise and over-deliver than vice versa.

---

## Risk Categories

### 1. Legal/Regulatory Risks
### 2. Model/Technical Risks
### 3. User Harm Risks
### 4. Business/Reputation Risks

---

## 1. Legal & Regulatory Risks

### Risk: Classified as "Investment Adviser" by SEC

**What triggers this:**
- Providing personalized recommendations (e.g., "YOU should buy AAPL")
- Charging fees for trading advice
- Managing client assets or portfolios

**Current status:**
- We do NOT provide personalized recommendations (signals are generic, educational)
- We do NOT manage user assets (no portfolio integration in MVP)
- We charge for software access, not advice

**Mitigation:**
- **Strong disclaimers:** Every output includes "This is not investment advice"
- **Generic signals only:** No "buy/sell/hold" language
- **Educational framing:** "Here's what historically happened" vs "Here's what you should do"
- **Terms of Service:** Users acknowledge they are solely responsible for trading decisions
- **Legal review:** Consult securities lawyer before launch (Phase 2)

**If we cross the line:**
- May need to register as Registered Investment Adviser (RIA) — expensive compliance burden
- May face SEC enforcement action — fines, cease-and-desist

**Reference:** Investment Advisers Act of 1940, SEC Rule 202(a)(11)

---

### Risk: Securities Fraud / Market Manipulation

**What triggers this:**
- Pump-and-dump schemes (hyping stocks we own)
- Front-running (trading based on signals before users see them)
- Spreading false information

**Mitigation:**
- **No proprietary trading:** We do NOT trade based on our signals (conflict of interest)
- **No front-running:** Signals are released to ALL users simultaneously (no VIP early access)
- **Fact-checking:** Risk Gate validates citations (signals must link to real events)
- **Audit trail:** Every signal has provenance chain (which event triggered it, which model generated it)

**If we violate:**
- SEC enforcement (civil/criminal penalties)
- Lawsuits from users ("you lied to us")
- Platform bans (Apple/Google may delist our app)

**Reference:** Securities Exchange Act of 1934, SEC Rule 10b-5

---

### Risk: GDPR / CCPA Privacy Violations

**What triggers this:**
- Collecting user data without consent
- Not honoring deletion requests
- Sharing user data with third parties

**Mitigation:**
- **Minimal data collection:** We only collect email, password, watchlist preferences (no brokerage data in MVP)
- **Clear privacy policy:** Explain what we collect, why, and how long we keep it
- **Right to deletion:** Users can delete their account + data at any time
- **No third-party sharing:** We don't sell user data (monetize via subscriptions, not ads)

**If we violate:**
- GDPR fines (up to €20M or 4% of revenue)
- CCPA fines ($2,500 - $7,500 per violation)
- User lawsuits (class action risk)

**Reference:** GDPR Art. 17 (Right to Erasure), CCPA § 1798.105

---

## 2. Model & Technical Risks

### Risk: Model Hallucinations (False Signals)

**What triggers this:**
- LLM generates plausible-sounding but incorrect event extraction
- Entity resolution maps wrong company ("Apple" → Apple Hospitality REIT instead of Apple Inc.)
- Impact hypothesis is based on flawed historical data

**Impact:**
- Users act on false signals → lose money → blame us
- Reputation damage (TrustPilot reviews, social media backlash)

**Mitigation:**
- **Multi-agent validation:** Each agent validates previous agent's output
- **Typed outputs:** Pydantic schemas enforce structure (can't generate gibberish)
- **Confidence thresholds:** Don't generate signals with confidence <0.4 (too uncertain)
- **Human-in-the-loop (Phase 3+):** Flag low-confidence signals for manual review
- **User feedback loop:** Track thumbs up/down → retrain models on flagged errors

**Metrics:**
- False positive rate <30% (Phase 1), <20% (Phase 3)
- User feedback: >60% thumbs up (Phase 2)

---

### Risk: Model Drift (Performance Degradation)

**What triggers this:**
- Market regime shifts (patterns that worked in 2020-2025 fail in 2026)
- Data distribution changes (new types of events not in training data)
- Adversarial behavior (users gaming the system)

**Impact:**
- Signal accuracy drops below random baseline (50%)
- Users lose trust, cancel subscriptions

**Mitigation:**
- **Monthly drift checks:** Compare current accuracy to Phase 1 baseline
- **Statistical tests:** Chi-squared test (is degradation significant?)
- **Automated alerts:** If accuracy <50% for 3+ days → email team immediately
- **Model retraining:** Retrain monthly (or more frequently if drift detected)
- **A/B testing:** Never deploy new model without validating it beats baseline

**Metrics:**
- Drift detection: Chi-squared p-value <0.05 → retrain
- Accuracy monitoring: Daily dashboard, 7-day rolling average

---

### Risk: System Downtime / Latency Spikes

**What triggers this:**
- API rate limits hit (Alpha Vantage, NewsAPI)
- Database overload (too many concurrent users)
- Third-party service outages (AWS, SEC EDGAR)

**Impact:**
- Users miss breaking news → lose trade opportunities
- Reputation damage ("unreliable service")

**Mitigation:**
- **Uptime target:** 99%+ (Phase 2), 99.9%+ (Phase 3)
- **Caching:** Redis cache for entity lookups, API responses
- **Rate limit management:** Batch API calls, prioritize high-value events
- **Monitoring:** Prometheus alerts (latency >5s, error rate >5%)
- **Fallback:** If NewsAPI fails, fall back to GDELT

**SLA (Phase 3+):**
- Event ingestion → signal generation: <10 min (95th percentile)
- API response time: <500ms (95th percentile)

---

## 3. User Harm Risks

### Risk: Users Lose Money Acting on Signals

**What triggers this:**
- Signal is accurate but user mistimes entry/exit
- Signal is wrong (false positive)
- User over-leverages based on high-confidence signal

**Impact:**
- Financial harm to users
- Lawsuits ("you told me to buy, I lost money")
- Regulatory scrutiny (SEC investigates complaints)

**Mitigation:**
- **Strong disclaimers:** "This is not investment advice. You are solely responsible for your trading decisions."
- **Uncertainty statements:** Every signal includes "what we don't know"
- **Confidence calibration:** Avoid overconfident signals (reject if >0.9 without review)
- **Educational content:** Tutorials on risk management, position sizing
- **No execution integration (MVP):** Don't link to brokerage APIs (removes temptation to "one-click trade")

**Legal protection:**
- Terms of Service: Users waive right to sue for losses
- Arbitration clause: Disputes resolved via arbitration, not courts

**Note:** ToS clauses are not bulletproof; we still need to act responsibly.

---

### Risk: Addiction / Compulsive Trading

**What triggers this:**
- Gamification (leaderboards, badges, "you're on a streak!")
- Push notifications creating FOMO (fear of missing out)
- High-frequency signals encouraging overtrading

**Impact:**
- Users harm themselves (financial, mental health)
- Regulatory scrutiny (FTC, state AGs crack down on "predatory design")

**Mitigation:**
- **No gamification:** No leaderboards, no badges, no "streaks"
- **Configurable notifications:** Users set their own thresholds (don't spam)
- **Rate limiting:** Don't generate >10 signals/day (prevents overtrading)
- **Educational content:** "Trading is not gambling; manage your risk"

**Ethical stance:** We are NOT in the business of encouraging overtrading.

---

## 4. Business & Reputation Risks

### Risk: Competitors Copy Our Approach

**What triggers this:**
- Bloomberg, RavenPack, or other institutional players launch retail-facing product
- Open-source projects replicate our pipeline (LangChain + FinBERT + EDGAR)

**Impact:**
- Lost market share
- Price competition (race to the bottom)

**Mitigation:**
- **Build moat via data:** Our labeled dataset (events + outcomes) is proprietary
- **Network effects:** More users → more feedback → better models
- **UX differentiation:** Focus on simplicity, explainability (institutions are slow to adapt)
- **Speed of iteration:** Ship features faster than competitors

**Acceptance:** Competition is inevitable; focus on execution.

---

### Risk: Negative Press / Social Media Backlash

**What triggers this:**
- High-profile signal fails ("Resonance Engine said TSLA would go up, it crashed")
- User lawsuit (even if frivolous, press covers it)
- Competitor FUD (fear, uncertainty, doubt)

**Impact:**
- User churn
- Apple/Google app store removal (if reviews tank)
- Difficulty fundraising

**Mitigation:**
- **Transparency:** Publish monthly accuracy reports (own our mistakes)
- **Proactive communication:** If accuracy drops, email users explaining why
- **User testimonials:** Collect success stories (with permission)
- **Crisis plan:** Pre-draft response templates for common scenarios

---

## Risk/Policy Gate Agent (Automated Guardrails)

The **Risk/Policy Gate Agent** is the last step in the agentic pipeline. It enforces compliance rules BEFORE signals reach users.

### Rule 1: No Investment Advice Language

**Blocked phrases:**
- "Buy", "Sell", "Hold"
- "Guaranteed", "Sure thing", "Can't lose"
- "You should", "You must", "Recommended"

**Allowed phrases:**
- "High probability", "Medium confidence", "Historically"
- "Based on precedent", "Similar events"

**Implementation:**
```python
BLOCKED_PHRASES = ["buy", "sell", "hold", "guaranteed", "you should"]

def check_compliance(signal_text: str) -> bool:
    for phrase in BLOCKED_PHRASES:
        if phrase.lower() in signal_text.lower():
            return False  # Reject signal
    return True  # Approve
```

---

### Rule 2: Disclaimer Enforcement

**Every signal must include:**
> "This is not investment advice. Signals are educational and based on historical patterns which may not repeat. Past performance does not guarantee future results. You are solely responsible for your trading decisions."

**Implementation:**
```python
DISCLAIMER = "This is not investment advice. Signals are educational..."

def add_disclaimer(signal: Signal) -> Signal:
    if DISCLAIMER not in signal.metadata.get("disclaimer", ""):
        signal.metadata["disclaimer"] = DISCLAIMER
    return signal
```

---

### Rule 3: Citation Validation

**Reject signals if:**
- No citations provided (empty list)
- Event ID doesn't exist in database
- Historical data query is invalid (SQL syntax error, empty result set)

**Implementation:**
```python
def validate_citations(signal: Signal, db) -> bool:
    if not signal.citations:
        return False  # No citations
    
    for citation in signal.citations:
        if citation["type"] == "event":
            if not db.event_exists(citation["id"]):
                return False  # Event doesn't exist
    
    return True  # All citations valid
```

---

### Rule 4: Confidence Bounds

**Reject signals if:**
- Confidence <0.4 (too uncertain; don't generate signal)
- Confidence >0.9 without human review (possible overfitting)

**Implementation:**
```python
def check_confidence(signal: Signal) -> bool:
    if signal.confidence < 0.4:
        return False  # Too uncertain
    if signal.confidence > 0.9:
        # Flag for human review (Phase 3+)
        signal.metadata["requires_review"] = True
    return True
```

---

### Rule 5: Uncertainty Requirement

**Reject signals if:**
- Uncertainty field is empty
- Uncertainty is too generic ("Anything can happen")

**Implementation:**
```python
GENERIC_UNCERTAINTY = ["anything can happen", "uncertain", "unknown"]

def check_uncertainty(signal: Signal) -> bool:
    if not signal.uncertainty:
        return False  # Empty uncertainty
    
    for generic in GENERIC_UNCERTAINTY:
        if signal.uncertainty.lower() == generic:
            return False  # Too generic
    
    return True  # Acceptable uncertainty
```

---

## Compliance Checklist (Pre-Launch)

### Legal:
- [ ] Consult securities lawyer (confirm we're NOT an investment adviser)
- [ ] Draft Terms of Service (user waives right to sue for losses)
- [ ] Draft Privacy Policy (GDPR/CCPA compliant)
- [ ] Register business entity (LLC or C-Corp)

### Technical:
- [ ] Risk Gate blocks 100% of non-compliant outputs on test set
- [ ] All signals have citations, rationale, uncertainty
- [ ] Disclaimer appears on every signal (UI + API)
- [ ] Audit trail: Every signal logs which model/version generated it

### User Safety:
- [ ] No gamification (no leaderboards, badges, streaks)
- [ ] Configurable notifications (users set thresholds)
- [ ] Educational content (risk management tutorials)
- [ ] Crisis response plan (template emails for bad events)

---

## Incident Response Plan

### Scenario 1: Signal Accuracy Drops Below 50%

**Trigger:** 3+ days of accuracy <50% (worse than random)

**Actions:**
1. Email team immediately (Slack alert + email)
2. Disable signal generation (stop sending new signals to users)
3. Investigate root cause (model drift? data quality issue? API outage?)
4. Email users: "We've paused signal generation while we investigate quality issues. We'll update you within 24 hours."
5. Fix issue (retrain model, fix data pipeline, switch API)
6. Re-enable signals only after validation (backtest on recent data)

---

### Scenario 2: User Files Lawsuit

**Trigger:** Receive legal notice (complaint, subpoena, cease-and-desist)

**Actions:**
1. Do NOT respond without lawyer (anything you say can be used against you)
2. Contact securities lawyer immediately
3. Preserve all records (signals, user activity, system logs)
4. Do NOT delete anything (spoliation of evidence = bad)
5. Follow lawyer's advice (settle, fight, etc.)

---

### Scenario 3: Negative Press Coverage

**Trigger:** Article in TechCrunch, Bloomberg, WSJ criticizing our product

**Actions:**
1. Assess accuracy of claims (are they right? partially right? wrong?)
2. If right: Own it. "We're aware of the issue and here's what we're doing to fix it."
3. If wrong: Correct factual errors politely. "We appreciate the coverage, but want to clarify..."
4. Proactive outreach: Email users before they see the article
5. Monitor social media (Twitter/X, Reddit) for sentiment

---

## Appendix: Related Documents

- `RESEARCH/PRD.md` — Compliance requirements, disclaimers
- `RESEARCH/SIGNAL_SPEC.md` — Risk Gate rules, confidence bounds
- `RESEARCH/EVALUATION.md` — Accuracy monitoring, drift detection
- `ROLES.md` — Who owns compliance (Product Lead + Fairoz)

---

**Document Status:** Draft v0.1  
**Last Updated:** March 2026  
**Next Review:** Before alpha launch (Phase 2)
