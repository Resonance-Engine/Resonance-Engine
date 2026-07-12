"""Confidence calibration — ECE, reliability diagrams, and Platt scaling.

Ensures that when the model says "78% confidence", it's right ~78% of the time.
Target: <15% calibration error (Phase 1), <10% (Phase 3).
"""

from dataclasses import dataclass


@dataclass
class CalibrationBin:
    """A single bin in a reliability diagram."""

    bin_lower: float
    bin_upper: float
    avg_confidence: float
    avg_accuracy: float
    count: int


def calibration_error(
    confidences: list[float],
    outcomes: list[bool],
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error (ECE).

    Bins predictions by confidence, computes weighted |avg_confidence - avg_accuracy|
    per bin. Lower is better — 0.0 means perfectly calibrated.

    Args:
        confidences: Predicted probabilities in [0.0, 1.0].
        outcomes: Actual binary outcomes.
        n_bins: Number of equal-width bins (default 10).

    Returns:
        ECE score in [0.0, 1.0].

    Raises:
        ValueError: If inputs have different lengths or are empty.
    """
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(outcomes)} outcomes"
        )
    if not confidences:
        raise ValueError("Cannot compute calibration error on empty inputs")

    n = len(confidences)
    bin_width = 1.0 / n_bins
    ece = 0.0

    for i in range(n_bins):
        bin_lower = i * bin_width
        bin_upper = (i + 1) * bin_width

        # Gather predictions in this bin
        bin_confs = []
        bin_outcomes = []
        for conf, out in zip(confidences, outcomes):
            if bin_lower <= conf < bin_upper or (i == n_bins - 1 and conf == 1.0):
                bin_confs.append(conf)
                bin_outcomes.append(out)

        if not bin_confs:
            continue

        avg_conf = sum(bin_confs) / len(bin_confs)
        avg_acc = sum(1 for o in bin_outcomes if o) / len(bin_outcomes)
        ece += (len(bin_confs) / n) * abs(avg_conf - avg_acc)

    return ece


def maximum_calibration_error(
    confidences: list[float],
    outcomes: list[bool],
    n_bins: int = 10,
) -> float:
    """Maximum Calibration Error (MCE) — worst-case bin deviation.

    Args:
        confidences: Predicted probabilities in [0.0, 1.0].
        outcomes: Actual binary outcomes.
        n_bins: Number of equal-width bins.

    Returns:
        MCE score in [0.0, 1.0].
    """
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(outcomes)} outcomes"
        )
    if not confidences:
        raise ValueError("Cannot compute MCE on empty inputs")

    bin_width = 1.0 / n_bins
    mce = 0.0

    for i in range(n_bins):
        bin_lower = i * bin_width
        bin_upper = (i + 1) * bin_width

        bin_confs = []
        bin_outcomes = []
        for conf, out in zip(confidences, outcomes):
            if bin_lower <= conf < bin_upper or (i == n_bins - 1 and conf == 1.0):
                bin_confs.append(conf)
                bin_outcomes.append(out)

        if not bin_confs:
            continue

        avg_conf = sum(bin_confs) / len(bin_confs)
        avg_acc = sum(1 for o in bin_outcomes if o) / len(bin_outcomes)
        mce = max(mce, abs(avg_conf - avg_acc))

    return mce


def reliability_diagram(
    confidences: list[float],
    outcomes: list[bool],
    n_bins: int = 10,
) -> list[CalibrationBin]:
    """Compute reliability diagram data (for plotting).

    Args:
        confidences: Predicted probabilities in [0.0, 1.0].
        outcomes: Actual binary outcomes.
        n_bins: Number of equal-width bins.

    Returns:
        List of CalibrationBin objects, one per non-empty bin.
    """
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(outcomes)} outcomes"
        )

    bin_width = 1.0 / n_bins
    bins: list[CalibrationBin] = []

    for i in range(n_bins):
        bin_lower = i * bin_width
        bin_upper = (i + 1) * bin_width

        bin_confs = []
        bin_outcomes = []
        for conf, out in zip(confidences, outcomes):
            if bin_lower <= conf < bin_upper or (i == n_bins - 1 and conf == 1.0):
                bin_confs.append(conf)
                bin_outcomes.append(out)

        if not bin_confs:
            continue

        bins.append(CalibrationBin(
            bin_lower=bin_lower,
            bin_upper=bin_upper,
            avg_confidence=sum(bin_confs) / len(bin_confs),
            avg_accuracy=sum(1 for o in bin_outcomes if o) / len(bin_outcomes),
            count=len(bin_confs),
        ))

    return bins


def calibrate_platt(raw_scores: list[float], labels: list[bool]) -> callable:
    """Fit Platt scaling (logistic regression on raw scores).

    Returns a calibration function: raw_score -> calibrated_probability.
    Uses simple sigmoid fitting: P(y=1|s) = 1 / (1 + exp(A*s + B))

    Args:
        raw_scores: Uncalibrated model scores.
        labels: Binary ground truth labels.

    Returns:
        A callable that maps raw scores to calibrated probabilities.

    Raises:
        ValueError: If inputs have different lengths or are empty.
    """
    if len(raw_scores) != len(labels):
        raise ValueError(
            f"Length mismatch: {len(raw_scores)} scores vs {len(labels)} labels"
        )
    if not raw_scores:
        raise ValueError("Cannot fit Platt scaling on empty inputs")

    import math

    # Simple gradient descent to fit A, B in sigmoid(A*s + B)
    a = 0.0
    b = 0.0
    lr = 0.01
    n = len(raw_scores)

    # Target values with Laplace smoothing (Platt 1999)
    n_pos = sum(1 for lbl in labels if lbl)
    n_neg = n - n_pos
    target_pos = (n_pos + 1) / (n_pos + 2) if n_pos > 0 else 0.5
    target_neg = 1 / (n_neg + 2) if n_neg > 0 else 0.5
    targets = [target_pos if lbl else target_neg for lbl in labels]

    for _ in range(1000):
        grad_a = 0.0
        grad_b = 0.0
        for s, t in zip(raw_scores, targets):
            z = a * s + b
            p = 1.0 / (1.0 + math.exp(-z)) if z > -500 else 0.0
            diff = p - t
            grad_a += diff * s
            grad_b += diff
        a -= lr * grad_a / n
        b -= lr * grad_b / n

    def calibrate(score: float) -> float:
        z = a * score + b
        if z > 500:
            return 1.0
        if z < -500:
            return 0.0
        return 1.0 / (1.0 + math.exp(-z))

    return calibrate
