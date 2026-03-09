# Evaluation Methodology & Metrics
## How We Test, Validate & Avoid Fooling Ourselves

**Last Updated:** March 2026  
**Owner:** Fairoz (AI/ML + Data Platform)  
**Reviewers:** Product & Architecture Lead

---

## Evaluation Philosophy

**Core principle:** Be rigorous about what we claim to know, and honest about what we don't.

Trading research is littered with false positives (strategies that work in backtest but fail live). We avoid this by:
1. **Point-in-time data discipline** (no look-ahead bias)
2. **Survivorship bias checks** (include delisted stocks)
3. **Overfitting detection** (use Bailey et al. methodology)
4. **Out-of-sample validation** (never test on training data)
5. **Confidence calibration** (predicted probabilities match outcomes)

**Remember:** Our job is NOT to make the numbers look good. Our job is to find out if this actually works.

---

## Evaluation Stages

### Stage 1: Offline Evaluation (Pre-Launch)
**Goal:** Validate NLP pipeline + signal generation on historical data

**Components:**
1. Entity resolution accuracy
2. Event extraction quality
3. Signal precision/recall
4. Confidence calibration
5. Backtest safety checks

**Timeline:** Phase 0-1 (Weeks 1-10)

---

### Stage 2: Alpha Testing (Controlled Launch)
**Goal:** Collect real user feedback, monitor live signal accuracy

**Components:**
1. User engagement metrics
2. Signal click-through rate
3. User feedback (thumbs up/down)
4. Live signal accuracy (compare predictions to outcomes)

**Timeline:** Phase 2 (Weeks 11-16)

---

### Stage 3: Production Monitoring (Post-Launch)
**Goal:** Detect model drift, maintain quality over time

**Components:**
1. Monthly accuracy reports
2. Drift detection (compare to baseline)
3. A/B testing new models
4. User retention/churn analysis

**Timeline:** Phase 3+ (Ongoing)

---

## Offline Evaluation Metrics

### 1. Entity Resolution

**Test set:**
- 200 hand-labeled news articles with company mentions
- Mix of easy cases ("Apple Inc." → AAPL) and hard cases ("Apple" → AAPL vs APLE)

**Metrics:**
- **Precision:** % of resolved entities that are correct
  - Target: >85% (Phase 0), >90% (Phase 3)
- **Recall:** % of true entities that were found
  - Target: >80% (Phase 0), >85% (Phase 3)
- **F1 score:** Harmonic mean of precision and recall
  - Target: >0.82 (Phase 0), >0.87 (Phase 3)

**Error analysis:**
- Log all misclassifications (false positives, false negatives)
- Categorize errors (typos, abbreviations, ambiguous mentions, missing entities)
- Prioritize fixes (highest-volume error types first)

**Example evaluation code:**
```python
from sklearn.metrics import precision_recall_fscore_support

true_labels = ["AAPL", "TSLA", "GOOGL", ...]
predicted_labels = ["AAPL", "TSLA", "GOOG", ...]  # GOOG vs GOOGL error

precision, recall, f1, _ = precision_recall_fscore_support(
    true_labels, predicted_labels, average='micro'
)

print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1: {f1:.2f}")
```

---

### 2. Event Extraction

**Test set:**
- 500 hand-labeled events (100 per event type: earnings, FDA, lawsuit, guidance, macro)
- Each event labeled with: event_type, sentiment (positive/negative/neutral), confidence

**Metrics:**
- **F1 score per event type:**
  - earnings: Target >0.70
  - fda_approval: Target >0.65
  - lawsuit: Target >0.60
  - guidance_revision: Target >0.65
  - macro_data: Target >0.55 (hardest to classify)
- **Confusion matrix:** Which event types get misclassified as others?
- **Sentiment accuracy:** % of events with correct sentiment label
  - Target: >70% (Phase 0), >80% (Phase 3)

**Baseline comparison:**
- Compare to FinBERT (pretrained sentiment model)
- Compare to Loughran-McDonald lexicon (rule-based)
- Our model must beat both baselines by >5% to justify deployment

**Example evaluation code:**
```python
from sklearn.metrics import classification_report, confusion_matrix

true_labels = ["earnings", "fda_approval", "lawsuit", ...]
predicted_labels = ["earnings", "earnings", "lawsuit", ...]  # 2nd is wrong

print(classification_report(true_labels, predicted_labels))
print(confusion_matrix(true_labels, predicted_labels))
```

---

### 3. Signal Precision & Recall

**Test set:**
- 200 historical events (2020-2025) with known outcomes
- Label each with: did_move (yes/no), direction (up/down), magnitude (% change), volatility_spike (yes/no)

**Metrics:**
- **Precision:** % of generated signals that were correct
  - Target: >55% (Phase 1), >60% (Phase 3)
  - "Correct" = outcome matched prediction (e.g., predicted volatility spike → actual volatility >2x avg)
- **Recall:** % of material events that generated signals
  - Target: >70% (don't miss important events)
- **False positive rate:** % of signals that didn't pan out
  - Target: <30% (Phase 1), <20% (Phase 3)

**Per-signal-type accuracy:**
- volatility_spike: Target >65% (easier to predict)
- positive_drift: Target >55% (directional signals are harder)
- negative_drift: Target >55%

**Example evaluation code:**
```python
# For each signal, compare prediction to outcome
signals = [
    {"predicted": "volatility_spike", "actual": "volatility_spike"},  # TP
    {"predicted": "positive_drift", "actual": "negative_drift"},       # FP
    {"predicted": "volatility_spike", "actual": "no_move"},            # FP
]

tp = sum(1 for s in signals if s["predicted"] == s["actual"])
fp = sum(1 for s in signals if s["predicted"] != s["actual"])

precision = tp / (tp + fp)
print(f"Signal precision: {precision:.2f}")
```

---

### 4. Confidence Calibration

**Goal:** Ensure predicted probabilities match real-world outcomes.

**Method:**
1. Bin signals by confidence (0.4-0.5, 0.5-0.6, 0.6-0.7, 0.7-0.8, 0.8-0.9)
2. For each bin, compute actual accuracy (% correct)
3. Plot: x-axis = predicted confidence, y-axis = actual accuracy
4. Perfect calibration = points fall on diagonal line (y=x)

**Metric:**
- **Calibration error:** Mean absolute difference between predicted and actual
  - Target: <15% (Phase 1), <10% (Phase 3)
  - Example: If we say 70% confidence, we should be right 60-80% of the time (±10%)

**Example evaluation code:**
```python
import numpy as np
import matplotlib.pyplot as plt

# Bin signals by confidence
bins = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
confidences = [0.45, 0.55, 0.68, 0.72, 0.85, ...]
outcomes = [0, 1, 1, 1, 1, ...]  # 1 = correct, 0 = wrong

bin_indices = np.digitize(confidences, bins)
calibration = []

for i in range(1, len(bins)):
    bin_mask = bin_indices == i
    if bin_mask.sum() > 0:
        bin_conf = np.mean([confidences[j] for j in range(len(confidences)) if bin_mask[j]])
        bin_acc = np.mean([outcomes[j] for j in range(len(outcomes)) if bin_mask[j]])
        calibration.append((bin_conf, bin_acc))

# Plot calibration curve
x = [c[0] for c in calibration]
y = [c[1] for c in calibration]
plt.plot(x, y, 'o-', label='Model')
plt.plot([0.4, 0.9], [0.4, 0.9], 'k--', label='Perfect calibration')
plt.xlabel('Predicted confidence')
plt.ylabel('Actual accuracy')
plt.legend()
plt.show()
```

**If calibration is off:**
- Use Platt scaling or isotonic regression to recalibrate
- Retrain model with better loss function (e.g., focal loss for imbalanced data)

---

## Backtesting Safety Checks

### 1. Look-Ahead Bias

**Problem:** Using future information in past predictions (e.g., using tomorrow's price to predict today's signal).

**Solution:**
- **Point-in-time data only:** For each event at time T, only use data available at T
- **No peeking:** Market data labels (returns, volatility) must be computed AFTER event timestamp
- **Validation:** Manually inspect 10 random signals → verify timestamps are consistent

**Example:**
```python
# WRONG: Using future price to label past event
event_time = "2026-03-09 14:30:00"
price_time = "2026-03-09 18:00:00"  # 4 hours AFTER event
label = (price_time - event_time) / event_time  # This is CORRECT

# WRONG: Using price from BEFORE event
price_time = "2026-03-09 12:00:00"  # 2 hours BEFORE event
label = (price_time - event_time) / event_time  # This is WRONG (look-ahead bias)
```

---

### 2. Survivorship Bias

**Problem:** Only including stocks that are currently trading (ignoring delisted/bankrupt companies).

**Solution:**
- **Include delisted stocks:** Use datasets that have full corporate action history
- **Check:** Count how many companies in backtest are delisted → should be ~2-3% per year
- **Validation:** Compare backtest results with/without survivorship adjustment

**Example:**
```python
# WRONG: Only test on current S&P 500 constituents
tickers = get_current_sp500()  # Survivorship bias!

# CORRECT: Use historical S&P 500 constituents (point-in-time)
tickers = get_sp500_as_of_date("2020-01-01")  # Includes companies that were delisted
```

---

### 3. Overfitting Detection (Bailey et al. Methodology)

**Problem:** Strategy works in backtest but fails live (data mining, overfitting).

**Solution:** Use "Probability of Backtest Overfitting" (PBO) metric.

**Method:**
1. Split historical data into N partitions (e.g., 10)
2. For each partition, compute strategy performance (Sharpe ratio, accuracy)
3. Check consistency: Does strategy work in ALL partitions, or just some?
4. Compute PBO: Probability that performance rank in first half > second half by chance

**Interpretation:**
- PBO <25%: Strategy is robust (unlikely to be overfit)
- PBO 25-50%: Moderate risk of overfitting
- PBO >50%: High risk of overfitting (don't deploy)

**Reference:** Bailey, D. H., Borwein, J., Lopez de Prado, M., & Zhu, Q. J. (2014). "The Probability of Backtest Overfitting." *Journal of Computational Finance*.

**Implementation note:** Use `mlfinlab` library (Python) for PBO calculation.

---

## Online Evaluation (Live Monitoring)

### 1. Signal Accuracy Tracking

**Method:**
- For each signal, store `predicted_move` and `actual_move`
- After impact window (1h, 4h, 24h), query market data and compute actual outcome
- Compare: Did prediction match outcome?

**Metrics:**
- **Accuracy:** % of signals where prediction matched outcome
  - Target: >55% (Phase 2), >60% (Phase 3)
- **Accuracy vs. baseline:** Compare to random (50%) and "always predict volatility" baseline
  - Target: +10-15% improvement over best baseline

**Dashboard:**
- Daily accuracy chart (rolling 7-day window)
- Per-signal-type accuracy (volatility, positive_drift, negative_drift)
- Per-ticker accuracy (which stocks do we predict well?)

**Alerting:**
- If accuracy drops below 50% for 3+ days → investigate immediately
- If specific signal type <45% accuracy → disable that signal type

---

### 2. Drift Detection

**Problem:** Models degrade over time (market regimes change, patterns break down).

**Solution:**
- **Monthly baseline comparison:** Compare current month accuracy to Phase 1 baseline
- **Statistical test:** Chi-squared test (is current accuracy significantly worse?)
- **Trigger:** If p-value <0.05 → model drift detected → retrain

**Example:**
```python
from scipy.stats import chisquare

baseline_accuracy = 0.58  # From Phase 1 backtest
current_accuracy = 0.52   # Current month

# Chi-squared test
observed = [52, 48]  # 52 correct, 48 wrong
expected = [58, 42]  # Expected based on baseline
chi2, p_value = chisquare(observed, expected)

if p_value < 0.05:
    print("Model drift detected! Retrain immediately.")
```

---

### 3. A/B Testing New Models

**Method:**
- Deploy new model to 10% of users (B group)
- Keep old model for 90% of users (A group)
- After 2 weeks, compare metrics:
  - Signal accuracy
  - User engagement (click-through rate)
  - User feedback (thumbs up/down)
- If B > A by >5% → roll out to 100%
- If B ≤ A → keep old model, investigate why new model failed

**Guardrail:** Never A/B test something that makes accuracy worse (even if engagement improves).

---

## User Engagement Metrics

### 1. Click-Through Rate (CTR)

**Metric:** % of signals that users click (to see rationale/citations)

**Target:**
- Phase 2: >30% CTR
- Phase 3: >40% CTR

**Interpretation:**
- High CTR = users find signals interesting/useful
- Low CTR = signals are not compelling OR users don't trust them

---

### 2. User Feedback (Thumbs Up/Down)

**Metric:** % of signals that get thumbs up

**Target:**
- Phase 2: >60% thumbs up
- Phase 3: >70% thumbs up

**Use case:**
- Retrain models using user feedback as labels (reinforcement learning from human feedback)
- Identify which signal types users like/dislike

---

### 3. User Retention

**Metric:** % of users who return after 1 week, 1 month

**Target:**
- 1-week retention: >50%
- 1-month retention: >30%

**Interpretation:**
- High retention = product is useful
- Low retention = users don't see value (or signals are inaccurate)

---

## Evaluation Checklist (Pre-Launch)

Before launching to users, verify:

### Entity Resolution:
- [ ] Precision >85% on test set
- [ ] Recall >80% on test set
- [ ] Error analysis complete (top 10 error types documented)

### Event Extraction:
- [ ] F1 score >0.60 on test set (per event type)
- [ ] Beats FinBERT baseline by >5%
- [ ] Confusion matrix reviewed (no catastrophic misclassifications)

### Signal Generation:
- [ ] Precision >55% on backtest set
- [ ] Recall >70% (don't miss material events)
- [ ] False positive rate <30%

### Confidence Calibration:
- [ ] Calibration error <15%
- [ ] Calibration curve plotted (no major deviations from diagonal)

### Backtesting Safety:
- [ ] Look-ahead bias check (manually inspect 10 random signals)
- [ ] Survivorship bias check (delisted stocks included)
- [ ] PBO <50% (strategy is not overfit)

### Risk Gate:
- [ ] 100% of non-compliant outputs blocked on test set
- [ ] All signals have citations, rationale, uncertainty

---

## Evaluation Reports (Templates)

### Monthly Accuracy Report (Phase 3+):
```markdown
# Signal Accuracy Report — March 2026

## Summary
- Total signals generated: 1,247
- Accuracy: 58.2% (vs 55% baseline)
- Confidence calibration error: 8.3% (target: <10%)
- False positive rate: 22.1% (target: <30%)

## Per-Signal-Type Breakdown
| Signal Type       | Count | Accuracy | Baseline | Improvement |
|-------------------|-------|----------|----------|-------------|
| volatility_spike  | 512   | 64.3%    | 60%      | +4.3%       |
| positive_drift    | 387   | 54.1%    | 50%      | +4.1%       |
| negative_drift    | 348   | 56.0%    | 50%      | +6.0%       |

## Top Errors
1. TSLA volatility_spike (predicted spike, no move) — 18 occurrences
2. NVDA positive_drift (predicted +5%, actual -3%) — 12 occurrences

## Recommendations
- Investigate TSLA false positives (possibly overfitting to Elon tweets)
- Recalibrate NVDA drift model (semiconductor sector volatility increased)
```

---

## Appendix: Related Documents

- `RESEARCH/PRD.md` — Success metrics (DAU, CTR, retention)
- `RESEARCH/SIGNAL_SPEC.md` — Signal schema, confidence scoring
- `RESEARCH/ARCHITECTURE.md` — Evaluation harness architecture
- `RESEARCH/RISKS_GUARDRAILS.md` — Risk Gate rules
- `ROLES.md` — Fairoz owns evaluation pipeline

---

**Document Status:** Draft v0.1  
**Last Updated:** March 2026  
**Next Review:** After Phase 1 evaluation harness
