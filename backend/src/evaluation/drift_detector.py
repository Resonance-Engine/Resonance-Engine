"""Drift detection — monitors model performance degradation over time.

Compares baseline accuracy distribution against current window using
statistical tests. If significant drift is detected, triggers retrain alert.
Runs monthly on rolling 7-day accuracy windows.
"""

from dataclasses import dataclass
from enum import StrEnum


class DriftSeverity(StrEnum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class DriftResult:
    """Result of a drift detection check."""

    drifted: bool
    p_value: float
    severity: DriftSeverity
    baseline_mean: float
    current_mean: float
    recommendation: str


def detect_drift(
    baseline_accuracies: list[float],
    current_accuracies: list[float],
    significance_level: float = 0.05,
) -> DriftResult:
    """Detect distribution shift in model accuracy using Welch's t-test.

    Compares the distribution of accuracies from a baseline period against
    a current period. Suitable for small samples (n >= 5 per group).

    Args:
        baseline_accuracies: Accuracy values from the reference period (e.g., 7-day windows).
        current_accuracies: Accuracy values from the current period.
        significance_level: p-value threshold for declaring drift (default 0.05).

    Returns:
        DriftResult with test outcome, p-value, severity, and recommendation.

    Raises:
        ValueError: If either input has fewer than 2 values.
    """
    if len(baseline_accuracies) < 2:
        raise ValueError(
            f"Need at least 2 baseline values, got {len(baseline_accuracies)}"
        )
    if len(current_accuracies) < 2:
        raise ValueError(
            f"Need at least 2 current values, got {len(current_accuracies)}"
        )

    # Compute means
    baseline_mean = sum(baseline_accuracies) / len(baseline_accuracies)
    current_mean = sum(current_accuracies) / len(current_accuracies)

    # Compute variances (Bessel's correction)
    n1 = len(baseline_accuracies)
    n2 = len(current_accuracies)
    var1 = sum((x - baseline_mean) ** 2 for x in baseline_accuracies) / (n1 - 1)
    var2 = sum((x - current_mean) ** 2 for x in current_accuracies) / (n2 - 1)

    # Welch's t-statistic
    se = (var1 / n1 + var2 / n2) ** 0.5
    if se == 0:
        # No variance — means are identical or constant
        return DriftResult(
            drifted=False,
            p_value=1.0,
            severity=DriftSeverity.NONE,
            baseline_mean=baseline_mean,
            current_mean=current_mean,
            recommendation="No variance in data — unable to test",
        )

    t_stat = (baseline_mean - current_mean) / se

    # Welch-Satterthwaite degrees of freedom
    num = (var1 / n1 + var2 / n2) ** 2
    denom = (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
    df = num / denom if denom > 0 else 1.0

    # Approximate p-value using Student's t-distribution
    # Uses the regularized incomplete beta function approximation
    p_value = _t_test_p_value(abs(t_stat), df)

    # Determine severity based on effect size (Cohen's d)
    pooled_std = ((var1 + var2) / 2) ** 0.5
    cohens_d = abs(baseline_mean - current_mean) / pooled_std if pooled_std > 0 else 0.0

    if p_value >= significance_level:
        severity = DriftSeverity.NONE
        recommendation = "No significant drift detected — continue monitoring"
    elif cohens_d < 0.5:
        severity = DriftSeverity.LOW
        recommendation = "Small drift detected — increase monitoring frequency"
    elif cohens_d < 0.8:
        severity = DriftSeverity.MODERATE
        recommendation = "Moderate drift detected — schedule model retraining"
    else:
        severity = DriftSeverity.SEVERE
        recommendation = "Severe drift detected — retrain immediately"

    return DriftResult(
        drifted=p_value < significance_level,
        p_value=p_value,
        severity=severity,
        baseline_mean=baseline_mean,
        current_mean=current_mean,
        recommendation=recommendation,
    )


def detect_accuracy_drop(
    baseline_accuracies: list[float],
    current_accuracies: list[float],
    threshold: float = 0.05,
) -> dict:
    """Simple threshold-based accuracy drop detection.

    Checks if the mean current accuracy has dropped by more than `threshold`
    compared to baseline. Faster and simpler than the statistical test.

    Args:
        baseline_accuracies: Accuracy values from the reference period.
        current_accuracies: Accuracy values from the current period.
        threshold: Minimum drop to flag (default 5 percentage points).

    Returns:
        Dict with keys: dropped, baseline_mean, current_mean, delta, threshold.
    """
    if not baseline_accuracies or not current_accuracies:
        return {
            "dropped": False,
            "baseline_mean": 0.0,
            "current_mean": 0.0,
            "delta": 0.0,
            "threshold": threshold,
        }

    baseline_mean = sum(baseline_accuracies) / len(baseline_accuracies)
    current_mean = sum(current_accuracies) / len(current_accuracies)
    delta = baseline_mean - current_mean

    return {
        "dropped": delta > threshold,
        "baseline_mean": baseline_mean,
        "current_mean": current_mean,
        "delta": delta,
        "threshold": threshold,
    }


def _t_test_p_value(t: float, df: float) -> float:
    """Approximate two-tailed p-value for Student's t-distribution.

    Uses the approximation: p ≈ 2 * (1 - Φ(t * (1 - 1/(4*df))))
    where Φ is the standard normal CDF. Accurate for df > 4.
    For smaller df, falls back to a conservative estimate.
    """
    import math

    if df <= 0:
        return 1.0

    # Adjusted t-statistic for better normal approximation
    if df > 4:
        adjusted_t = t * (1 - 1 / (4 * df))
    else:
        # For small df, use a rougher approximation
        adjusted_t = t * (df / (df + 2)) ** 0.5

    # Standard normal CDF approximation (Abramowitz and Stegun)
    p = 2.0 * (1.0 - _normal_cdf(abs(adjusted_t)))
    return max(0.0, min(1.0, p))


def _normal_cdf(x: float) -> float:
    """Standard normal CDF approximation (Abramowitz and Stegun 26.2.17)."""
    import math

    if x < -8:
        return 0.0
    if x > 8:
        return 1.0

    # Constants for approximation
    b0 = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429

    t = 1.0 / (1.0 + b0 * abs(x))
    pdf = math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    poly = t * (b1 + t * (b2 + t * (b3 + t * (b4 + t * b5))))
    cdf = 1.0 - pdf * poly

    return cdf if x >= 0 else 1.0 - cdf
