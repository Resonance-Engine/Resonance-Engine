# Data Sources, APIs & Pipeline Design
## Resonance Engine Data Strategy

**Last Updated:** March 2026  
**Owner and Co-Owner:** Reiyyan (Product & Architecture) and Fairoz (AI/ML & Data Platform)  
**Reviewers:** Reiyyan - Product & Architecture Lead

---

## Overview

This document catalogs all data sources, APIs, licensing constraints, rate limits, and pipeline design decisions for Resonance Engine's MVP and future phases.

**Core principle:** Start with free/public sources, validate product-market fit, then invest in premium data if justified by user demand.

---

## Data Sources (Current & Planned)

### 1. SEC EDGAR (U.S. Public Company Filings)

**What it provides:**
- 8-K filings (material events: earnings, M&A, lawsuits, FDA approvals, executive changes)
- 10-K/10-Q filings (annual/quarterly reports with risk factors, MD&A)
- S-1 filings (IPO registrations)
- Insider trading reports (Form 4)
- Companyfacts.zip (structured fundamental data: CIK, ticker, SIC code, filing history)
- Submissions.zip (metadata for all filings)

**Access:**
- **API:** https://www.sec.gov/edgar/sec-api-documentation
- **Bulk downloads:** https://www.sec.gov/dera/data/financial-statement-data-sets.html
- **Rate limits:** 10 requests/second per IP (enforced via User-Agent header)
- **Cost:** Free
- **Licensing:** Public domain (U.S. government data)

**Usage in Resonance Engine:**
- **Phase 0:** Ingest 8-K filings (Item 2.02 for earnings, Item 8.01 for material events)
- **Phase 1:** Parse 10-K risk factors for sentiment analysis
- **Phase 3:** Add insider trading signals (Form 4 cluster analysis)

**Implementation notes:**
- Use `companyfacts.zip` to build ticker → CIK mapping (canonical entity resolution)
- Parse XML filings using `lxml` or `BeautifulSoup`
- Store in PostgreSQL with jsonb fields for flexible schema
- Set User-Agent header to comply with SEC rate limit policy (include email contact)

**Example request:**
```python
import requests

headers = {"User-Agent": "ResonanceEngine/0.1 (contact@resonanceengine.com)"}
url = "https://data.sec.gov/submissions/CIK0000320193.json"  # Apple Inc.
response = requests.get(url, headers=headers)
data = response.json()
```

---

### 2. GDELT Project (Global News & Event Data)

**What it provides:**
- Real-time news monitoring (15-minute updates)
- Global coverage (100+ languages, 100+ countries)
- Event extraction (actors, actions, locations, sentiment, tone)
- News source metadata (URL, domain, publish date)

**Access:**
- **API:** https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- **BigQuery:** https://console.cloud.google.com/marketplace/product/gdelt-bq/gdelt-2-events
- **Rate limits:** No official limit, but recommend <100 requests/hour for free tier
- **Cost:** Free (API), BigQuery has query costs (~$5/TB scanned)
- **Licensing:** Open data (cite GDELT Project)

**Usage in Resonance Engine:**
- **Phase 2:** Broad event monitoring (supplement EDGAR with global news)
- **Phase 3:** Topic clustering (identify emerging themes across sources)

**Implementation notes:**
- GDELT data is noisy → need heavy filtering (source quality, language, relevance)
- Use BigQuery for historical analysis (cheaper than downloading full dataset)
- Deduplicate against EDGAR and NewsAPI (same story from multiple sources)

**Example query (BigQuery):**
```sql
SELECT
  SOURCEURL,
  DATE,
  Actor1Name,
  Actor2Name,
  EventCode,
  AvgTone
FROM
  `gdelt-bq.gdeltv2.events`
WHERE
  Actor1CountryCode = 'USA'
  AND DATE > 20260301
LIMIT 100;
```

---

### 3. NewsAPI (Breaking News Aggregator)

**What it provides:**
- Breaking news from 150+ sources (CNN, Reuters, Bloomberg, TechCrunch, etc.)
- `/v2/everything` endpoint (search by keyword, date, source)
- `/v2/top-headlines` endpoint (breaking news by category, country)

**Access:**
- **API:** https://newsapi.org/docs
- **Rate limits:**
  - **Free tier:** 100 requests/day, 1 request/second
  - **Developer tier ($449/month):** 250,000 requests/month, live data
- **Cost:** Free tier for MVP, upgrade if needed
- **Licensing:** Free tier is for personal/non-commercial projects; commercial use requires paid plan

**Usage in Resonance Engine:**
- **Phase 2:** Prototype ingestion pipeline (100 requests/day = ~3-4 per hour, enough for testing)
- **Phase 4:** Upgrade to paid tier if user demand justifies ($449/month < cost of hiring someone to scrape news)

**Implementation notes:**
- Cache responses aggressively (news doesn't change minute-to-minute)
- Batch requests (search for multiple tickers in one query: `q=AAPL OR TSLA OR GOOGL`)
- Use `pageSize` parameter to maximize data per request (100 articles max)

**Example request:**
```python
import requests

api_key = "YOUR_API_KEY"
url = "https://newsapi.org/v2/everything"
params = {
    "q": "FDA approval",
    "from": "2026-03-01",
    "sortBy": "publishedAt",
    "pageSize": 100,
    "apiKey": api_key
}
response = requests.get(url, params=params)
articles = response.json()["articles"]
```

---

### 4. Alpha Vantage (Market Data for Labeling)

**What it provides:**
- Stock prices (daily, intraday)
- Technical indicators (SMA, EMA, RSI, MACD)
- Fundamental data (earnings, balance sheet, income statement)
- News & sentiment (via partnership with Tiingo)

**Access:**
- **API:** https://www.alphavantage.co/documentation/
- **Rate limits:**
  - **Free tier:** 25 requests/day, 5 requests/minute
  - **Premium ($49.99/month):** 75 requests/minute, 1200 requests/day
- **Cost:** Free tier for Phase 0-1, upgrade if needed
- **Licensing:** Free tier is for personal use; commercial use requires attribution

**Usage in Resonance Engine:**
- **Phase 1:** Label events with post-event returns (pull intraday prices for 1h, 4h, 24h windows)
- **Phase 3:** Technical indicator features (e.g., "signal triggered during oversold RSI" → higher confidence)

**Implementation notes:**
- Free tier is very limiting (25 requests/day = can only label 25 events/day)
- Cache historical data aggressively (don't re-fetch same ticker/date)
- Consider switching to Polygon.io or Finnhub if we need more throughput

**Example request:**
```python
import requests

api_key = "YOUR_API_KEY"
url = "https://www.alphavantage.co/query"
params = {
    "function": "TIME_SERIES_INTRADAY",
    "symbol": "AAPL",
    "interval": "5min",
    "apikey": api_key
}
response = requests.get(url, params=params)
data = response.json()
```

---

### 5. Finnhub (Market Data Alternative)

**What it provides:**
- Real-time stock prices (WebSocket + REST)
- Company news (aggregated from multiple sources)
- Earnings calendars, IPO calendar, economic calendar
- Insider transactions, analyst ratings, price targets

**Access:**
- **API:** https://finnhub.io/docs/api
- **Rate limits:**
  - **Free tier:** 60 API calls/minute
  - **Starter ($19.99/month):** 300 API calls/minute
- **Cost:** Free tier for Phase 0-1, upgrade if needed
- **Licensing:** Free tier allows commercial use (check ToS)

**Usage in Resonance Engine:**
- **Phase 1:** Alternative to Alpha Vantage (higher rate limits)
- **Phase 2:** News endpoint for deduplication (cross-check GDELT/NewsAPI)
- **Phase 3:** Earnings calendar integration (pre-populate watchlist with upcoming events)

**Implementation notes:**
- Free tier is more generous than Alpha Vantage (60 calls/min vs 5 calls/min)
- News endpoint includes sentiment scores (can use as baseline comparison)

**Example request:**
```python
import requests

api_key = "YOUR_API_KEY"
url = "https://finnhub.io/api/v1/company-news"
params = {
    "symbol": "AAPL",
    "from": "2026-03-01",
    "to": "2026-03-09",
    "token": api_key
}
response = requests.get(url, params=params)
news = response.json()
```

---

### 6. Polygon.io (Premium Market Data)

**What it provides:**
- Real-time + historical stock prices (tick-level data)
- News API (aggregated from 20+ sources)
- Options data, crypto data, forex data
- WebSocket streaming (real-time tickers)

**Access:**
- **API:** https://polygon.io/docs/stocks
- **Rate limits:**
  - **Free tier:** 5 API calls/minute
  - **Starter ($29/month):** Unlimited calls, real-time data
- **Cost:** Not using in Phase 0-1 (too expensive for MVP), consider for Phase 3+
- **Licensing:** Commercial use allowed

**Usage in Resonance Engine:**
- **Phase 3+:** If we need tick-level data for precise event timing
- **Phase 4:** WebSocket for real-time signal generation (<1 min latency)

---

### 7. Reddit & Twitter/X (Social Signals — Optional)

**Reddit Data API:**
- **Access:** https://www.reddit.com/dev/api/
- **Rate limits:** 60 requests/minute (OAuth), 10 requests/minute (unauthenticated)
- **Licensing:** Commercial use requires separate agreement (per ToS)
- **Cost:** Free for now, may require paid partnership later

**Twitter/X API:**
- **Access:** https://developer.twitter.com/en/docs/twitter-api
- **Rate limits:** Varies by tier (Free tier is very limited, ~1500 tweets/month)
- **Cost:** Basic tier ($100/month) for 10k tweets/month
- **Licensing:** Commercial use allowed (check ToS)

**Usage in Resonance Engine:**
- **Phase 3+:** Only if user feedback demands social signals
- **Compliance risk:** Both platforms prohibit certain commercial uses → need legal review

**Implementation notes:**
- High noise-to-signal ratio (Reddit/Twitter sentiment is often unreliable)
- Deduplication is critical (same rumor spreads across platforms)
- Consider waiting until we have strong user demand before investing here

---

## Data Sources NOT Using (and Why)

| Source | Why Not Using |
|--------|---------------|
| **IEX Cloud** | Discontinued as of late 2024 |
| **Bloomberg Terminal** | $24k/year, institutional pricing (not viable for MVP) |
| **Reuters Eikon** | Similar to Bloomberg (too expensive for retail product) |
| **RavenPack News Analytics** | Institutional pricing ($10k+/year), overkill for MVP |
| **Quandl (Nasdaq Data Link)** | Many datasets require paid subscriptions |
| **Web scraping (any source)** | Legal risk, ToS violations, unreliable (sources change HTML frequently) |

---

## Data Pipeline Architecture

### High-Level Flow:
```
[External APIs] → [Ingestion Layer] → [Normalization/Dedupe] → [Entity Resolution]
     → [Event Extraction] → [Impact Hypothesis] → [Signal Store] → [API/UI]
```

### Phase 0-1 Stack (MVP):
- **Ingestion:** Python scripts (schedule via cron or Celery)
- **Storage:** PostgreSQL (events, entities, signals tables)
- **Message queue:** Redis (for async task processing)
- **Caching:** Redis (entity resolution lookups, API responses)
- **Monitoring:** Python logging + simple Prometheus metrics

### Phase 3+ Stack (Production):
- **Event streaming:** Kafka (immutable event log, replay capability)
- **Stream processing:** Flink or Kafka Streams (stateful transformations)
- **Storage:** PostgreSQL + TimescaleDB (time-series extension)
- **Caching:** Redis Cluster (distributed cache)
- **Monitoring:** Prometheus + Grafana + OpenTelemetry (full observability)

---

## Database Schema (Draft)

### `events` table:
```sql
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,  -- 'SEC_EDGAR', 'GDELT', 'NewsAPI'
    url TEXT,
    raw_text TEXT,
    entities JSONB,  -- [{"ticker": "AAPL", "cik": "0000320193"}]
    event_type TEXT,  -- 'earnings', 'fda_approval', 'lawsuit', etc.
    summary TEXT,
    confidence FLOAT,
    metadata JSONB,  -- Flexible field for source-specific data
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_entities ON events USING GIN(entities);
```

### `signals` table:
```sql
CREATE TABLE signals (
    signal_id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(event_id),
    timestamp TIMESTAMPTZ NOT NULL,
    ticker TEXT NOT NULL,
    signal_text TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    rationale TEXT,
    uncertainty TEXT,
    impact_window TEXT,  -- '1h', '4h', '24h'
    predicted_move FLOAT,  -- e.g., +0.05 for +5%
    actual_move FLOAT,  -- Post-event outcome (for eval)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX idx_signals_ticker ON signals(ticker);
```

### `entities` table (canonical ticker/CIK mapping):
```sql
CREATE TABLE entities (
    cik TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    sic_code TEXT,
    metadata JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entities_ticker ON entities(ticker);
```

---

## Data Quality & Validation

### Ingestion Validation:
- [ ] Every event has a valid timestamp (no future dates, no null timestamps)
- [ ] Every event has a source URL (citation trail)
- [ ] Entity resolution finds at least one ticker/CIK (or flags as "unknown entity")
- [ ] Deduplication: hash(source + URL + timestamp) to detect duplicates

### Entity Resolution Validation:
- [ ] Precision >85% on hand-labeled test set
- [ ] Ambiguous mentions are flagged (e.g., "Apple" → [AAPL, APLE])
- [ ] Edge cases documented (e.g., "Meta" → META vs "Meta Materials" → MMAT)

### Event Extraction Validation:
- [ ] F1 score >0.60 on hand-labeled test set (Phase 0 baseline)
- [ ] Confidence scores are calibrated (70% confidence → 70% accuracy)
- [ ] Unknown event types are flagged (not forced into wrong category)

### Signal Generation Validation:
- [ ] Every signal has a confidence score (0.0–1.0)
- [ ] Every signal has a rationale (why it was generated)
- [ ] Every signal has an uncertainty statement ("what we don't know")
- [ ] Risk Gate blocks 100% of non-compliant outputs

---

## Data Retention & Privacy

### Retention Policy:
- **Raw ingestion data:** Keep for 90 days (for debugging + backfill)
- **Processed events:** Keep indefinitely (needed for backtesting)
- **Signals:** Keep indefinitely (needed for eval + user history)
- **User data:** Follow GDPR/CCPA (delete on request)

### Privacy Considerations:
- We do NOT collect:
  - User brokerage account data (no portfolio syncing in MVP)
  - User trading history (no execution tracking)
  - Personal financial info (no income, net worth, etc.)
- We DO collect:
  - Email, password (for account management)
  - Signal preferences (watchlist, notification thresholds)
  - Usage analytics (which signals get clicked, time spent on platform)

---

## Cost Estimates (MVP Phase)

| Item | Cost/Month | Notes |
|------|-----------|-------|
| **SEC EDGAR** | $0 | Free (public data) |
| **GDELT** | $0 | Free API |
| **NewsAPI** | $0 | Free tier (100 req/day) |
| **Alpha Vantage** | $0 | Free tier (25 req/day) |
| **Finnhub** | $0 | Free tier (60 req/min) |
| **PostgreSQL (AWS RDS)** | $15 | db.t3.micro (20GB) |
| **Redis (AWS ElastiCache)** | $13 | cache.t3.micro |
| **Compute (AWS EC2)** | $20 | t3.small (2 vCPU, 2GB RAM) |
| **Total** | **$48/month** | Scales to ~$200/month in Phase 3 |

---

## Future Data Sources (Post-MVP)

| Source | Phase | Use Case | Estimated Cost |
|--------|-------|----------|----------------|
| **Earnings call transcripts** | Phase 3 | Sentiment analysis, executive tone | $50/month (Seeking Alpha API) |
| **Options flow data** | Phase 4 | Unusual activity signals | $100/month (Market Chameleon) |
| **Satellite imagery** | Phase 5 | Alternative data (parking lots, shipping) | $500+/month (Orbital Insight) |
| **Credit card transactions** | Phase 5 | Consumer spending trends | $1000+/month (Second Measure) |

---

## Appendix: API Response Examples

### EDGAR 8-K Filing (JSON):
```json
{
  "cik": "0000320193",
  "entityType": "operating",
  "sic": "3571",
  "sicDescription": "Electronic Computers",
  "name": "Apple Inc.",
  "tickers": ["AAPL"],
  "filings": {
    "recent": {
      "accessionNumber": ["0000320193-26-000008"],
      "filingDate": ["2026-03-09"],
      "reportDate": ["2026-03-09"],
      "form": ["8-K"],
      "items": ["2.02"]
    }
  }
}
```

### NewsAPI Article (JSON):
```json
{
  "source": {"id": "bloomberg", "name": "Bloomberg"},
  "author": "Jane Doe",
  "title": "Apple Revises Q2 Guidance Amid Supply Chain Woes",
  "description": "Apple Inc. cut its revenue forecast...",
  "url": "https://bloomberg.com/...",
  "publishedAt": "2026-03-09T14:32:00Z",
  "content": "Apple Inc. (AAPL) announced today that..."
}
```

---

**Document Status:** Draft v0.1  
**Last Updated:** March 2026  
**Next Review:** After Phase 0 ingestion prototype
