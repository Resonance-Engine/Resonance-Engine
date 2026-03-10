# References & Resources
## APIs, Papers, Tools & Datasets

**Last Updated:** March 2026  
**Owner and Co-Owner:** Reiyyan (Product & Architecture) and Fairoz (AI/ML & Data Platform)  
**Reviewers:** Reiyyan - Product & Architecture Lead
---

## Data Sources & APIs

### SEC EDGAR (U.S. Public Company Filings)
- **API Documentation:** https://www.sec.gov/edgar/sec-api-documentation
- **Bulk Downloads:** https://www.sec.gov/dera/data/financial-statement-data-sets.html
- **Companyfacts.zip:** https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip
- **Rate Limits:** 10 requests/second per IP
- **Cost:** Free (public domain)

### GDELT Project (Global News & Events)
- **Main Site:** https://www.gdeltproject.org/
- **API Documentation:** https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- **BigQuery:** https://console.cloud.google.com/marketplace/product/gdelt-bq/gdelt-2-events
- **Cost:** Free (API), BigQuery charges apply

### NewsAPI (Breaking News Aggregator)
- **API Documentation:** https://newsapi.org/docs
- **Pricing:** https://newsapi.org/pricing
- **Rate Limits:** Free tier = 100 requests/day
- **Cost:** Free (personal), $449/month (commercial)

### Alpha Vantage (Market Data)
- **API Documentation:** https://www.alphavantage.co/documentation/
- **Rate Limits:** Free tier = 25 requests/day, 5 requests/minute
- **Pricing:** https://www.alphavantage.co/premium/
- **Cost:** Free (basic), $49.99/month (premium)

### Finnhub (Market Data Alternative)
- **API Documentation:** https://finnhub.io/docs/api
- **Rate Limits:** https://finnhub.io/pricing
- **Cost:** Free tier = 60 API calls/minute

### Polygon.io (Premium Market Data)
- **API Documentation:** https://polygon.io/docs/stocks
- **Pricing:** https://polygon.io/pricing
- **Cost:** $29/month (starter), $99/month (developer)

### Reddit Data API
- **API Documentation:** https://www.reddit.com/dev/api/
- **Terms of Service:** https://www.redditinc.com/policies/data-api-terms
- **Rate Limits:** 60 requests/minute (OAuth)

### Twitter/X API
- **API Documentation:** https://developer.twitter.com/en/docs/twitter-api
- **Pricing:** https://developer.twitter.com/en/portal/products
- **Cost:** Basic tier = $100/month (10k tweets/month)

---

## Academic Papers & Research

### Financial NLP & Sentiment Analysis

**FinBERT: Financial Sentiment Analysis with Pre-trained Language Models**
- Authors: Dogu Araci (2019)
- Link: https://arxiv.org/abs/1908.10063
- Summary: BERT fine-tuned on financial news for sentiment classification
- Relevance: Our baseline sentiment model

**Loughran-McDonald Sentiment Word Lists**
- Authors: Tim Loughran, Bill McDonald (2011)
- Link: https://sraf.nd.edu/lm-sentiment-word-lists/
- Summary: Finance-specific sentiment lexicons (positive, negative, uncertainty, litigious)
- Relevance: Lexicon-based event extraction

**Textual Analysis in Finance**
- Authors: Tetlock, P. C. (2007). "Giving Content to Investor Sentiment: The Role of Media in the Stock Market." *Journal of Finance*.
- Link: https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2007.01232.x
- Summary: Evidence that media content predicts market activity
- Relevance: Academic validation for "news → signals" approach

---

### Backtesting & Overfitting

**The Probability of Backtest Overfitting**
- Authors: Bailey, D. H., Borwein, J., Lopez de Prado, M., & Zhu, Q. J. (2014)
- Link: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- Summary: Method to detect overfitting in trading strategies
- Relevance: Our backtesting safety checks

**Advances in Financial Machine Learning**
- Author: Marcos Lopez de Prado (2018)
- Book: https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086
- Summary: Practical techniques for avoiding common ML pitfalls in finance
- Relevance: Look-ahead bias, survivorship bias, sample weights

---

### Agentic AI & Tool Use

**ReAct: Synergizing Reasoning and Acting in Language Models**
- Authors: Yao, S., Zhao, J., Yu, D., et al. (2022)
- Link: https://arxiv.org/abs/2210.03629
- Summary: LLMs that interleave reasoning (thought) and actions (tool use)
- Relevance: Foundation for our agentic workflow

**LangGraph Documentation**
- Link: https://langchain-ai.github.io/langgraph/
- Summary: Framework for building multi-agent workflows with typed state
- Relevance: Our agent orchestration layer

---

### ML Production & Documentation

**Hidden Technical Debt in Machine Learning Systems**
- Authors: Sculley, D., et al. (2015)
- Link: https://proceedings.neurips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf
- Summary: Common anti-patterns in production ML systems
- Relevance: Avoid technical debt as we scale

**The ML Test Score: A Rubric for ML Production Readiness**
- Authors: Breck, E., et al. (2017)
- Link: https://research.google/pubs/pub46555/
- Summary: 28 tests for production ML systems (data, model, monitoring)
- Relevance: Our Phase 3 production checklist

**Datasheets for Datasets**
- Authors: Gebru, T., et al. (2018)
- Link: https://arxiv.org/abs/1803.09010
- Summary: Template for documenting datasets (motivation, composition, uses, maintenance)
- Relevance: Document our labeled event dataset

**Model Cards for Model Reporting**
- Authors: Mitchell, M., et al. (2019)
- Link: https://arxiv.org/abs/1810.03993
- Summary: Template for documenting models (intended use, performance, limitations)
- Relevance: Document our NLP models (FinBERT, event extractors)

---

### AI Risk & Governance

**NIST AI Risk Management Framework**
- Link: https://www.nist.gov/itl/ai-risk-management-framework
- Summary: Framework for identifying, assessing, and managing AI risks
- Relevance: Our RISKS_GUARDRAILS.md aligns with NIST RMF

---

## Tools & Libraries

### Python ML/NLP Libraries
- **Transformers (Hugging Face):** https://huggingface.co/docs/transformers/
- **spaCy:** https://spacy.io/
- **NLTK:** https://www.nltk.org/
- **scikit-learn:** https://scikit-learn.org/
- **PyTorch:** https://pytorch.org/
- **TensorFlow:** https://www.tensorflow.org/

### Data Engineering
- **pandas:** https://pandas.pydata.org/
- **Polars:** https://pola.rs/
- **DuckDB:** https://duckdb.org/
- **Apache Kafka:** https://kafka.apache.org/
- **Apache Flink:** https://flink.apache.org/
- **Redis:** https://redis.io/
- **PostgreSQL:** https://www.postgresql.org/

### MLOps & Experiment Tracking
- **MLflow:** https://mlflow.org/
- **Weights & Biases:** https://wandb.ai/
- **DVC (Data Version Control):** https://dvc.org/
- **Great Expectations:** https://greatexpectations.io/

### Observability & Monitoring
- **Prometheus:** https://prometheus.io/
- **Grafana:** https://grafana.com/
- **OpenTelemetry:** https://opentelemetry.io/
- **Loki (Logging):** https://grafana.com/oss/loki/

### API Frameworks
- **FastAPI:** https://fastapi.tiangolo.com/
- **Flask:** https://flask.palletsprojects.com/
- **Django:** https://www.djangoproject.com/

### Frontend
- **React:** https://react.dev/
- **TypeScript:** https://www.typescriptlang.org/
- **Tailwind CSS:** https://tailwindcss.com/
- **Zustand (State Management):** https://zustand-demo.pmnd.rs/

---

## Datasets

### Financial PhraseBank
- **Link:** https://www.researchgate.net/publication/251231364_FinancialPhraseBank-v10
- **Description:** 4,840 sentences from financial news, labeled with sentiment
- **Use Case:** Baseline for sentiment classification evaluation

### SEC EDGAR Historical Archives
- **Link:** https://www.sec.gov/Archives/edgar/
- **Description:** Complete archive of SEC filings (1994-present)
- **Use Case:** Historical event dataset, entity resolution

### GDELT Event Database
- **Link:** https://www.gdeltproject.org/data.html
- **Description:** 400M+ events from global news (1979-present)
- **Use Case:** Broad event pattern exploration

---

## Industry Reports & Whitepapers

### Bloomberg Terminal (Competitor Analysis)
- **Link:** https://www.bloomberg.com/professional/solution/bloomberg-terminal/
- **Relevance:** Understand what institutional tools offer

### RavenPack News Analytics
- **Link:** https://www.ravenpack.com/
- **Relevance:** Competitor in news analytics space

### Benzinga News API
- **Link:** https://www.benzinga.com/apis/
- **Relevance:** Alternative news data provider

---

## Legal & Compliance

### Investment Advisers Act of 1940
- **Link:** https://www.sec.gov/investment/laws-and-rules
- **Relevance:** Defines what counts as "investment advice"

### SEC Rule 10b-5 (Securities Fraud)
- **Link:** https://www.sec.gov/rules-regulations/1934-act-rules/10b-5
- **Relevance:** Anti-fraud provisions

### GDPR (EU Privacy Law)
- **Link:** https://gdpr.eu/
- **Relevance:** User data protection (if we expand to EU)

### CCPA (California Privacy Law)
- **Link:** https://oag.ca.gov/privacy/ccpa
- **Relevance:** User data protection (California users)

---

## Community & Forums

### r/algotrading (Reddit)
- **Link:** https://www.reddit.com/r/algotrading/
- **Relevance:** Target user community

### QuantConnect (Algo Trading Platform)
- **Link:** https://www.quantconnect.com/
- **Relevance:** Competitor, learning resource

### Kaggle Competitions (Finance)
- **Link:** https://www.kaggle.com/competitions?searchQuery=finance
- **Relevance:** Benchmark datasets, model ideas

---

## Recommended Reading

### Books
1. **"Advances in Financial Machine Learning"** — Marcos Lopez de Prado
2. **"Machine Learning for Asset Managers"** — Marcos Lopez de Prado
3. **"Quantitative Trading"** — Ernest Chan
4. **"Algorithmic Trading"** — Ernest Chan
5. **"Deep Learning for Finance"** — Sofien Kaabar

### Blogs & Newsletters
- **Quantocracy:** https://quantocracy.com/ (curated quant finance links)
- **Alpha Architect:** https://alphaarchitect.com/ (factor investing research)
- **Quantifiable Edges:** https://quantifiableedges.com/ (market analysis)

---

**Document Status:** Living document (updated as we add resources)  
**Last Updated:** March 2026  
**Next Review:** Quarterly
