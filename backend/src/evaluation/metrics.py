"""Evaluation metrics — precision, recall, F1, Brier score for signals."""

import math


def precision_at_k(predictions: list[bool], k: int | None = None) -> float:
    """Precision@k: fraction of the top-k predictions that were correct.

    Args:
        predictions: Ordered list of prediction outcomes (True = correct signal).
        k: Only evaluate the top-k predictions. If None, uses all.

    Returns:
        Precision score in [0.0, 1.0]. Returns 0.0 if no predictions.
    """
    if not predictions:
        return 0.0
    subset = predictions[:k] if k is not None else predictions
    if not subset:
        return 0.0
    return sum(1 for p in subset if p) / len(subset)


def recall_at_k(predictions: list[bool], total_relevant: int) -> float:
    """Recall@k: fraction of all relevant events that were captured.

    Args:
        predictions: Ordered list of prediction outcomes (True = correct signal).
        total_relevant: Total number of material events that should have generated signals.

    Returns:
        Recall score in [0.0, 1.0]. Returns 0.0 if total_relevant is 0.
    """
    if total_relevant <= 0:
        return 0.0
    correct = sum(1 for p in predictions if p)
    return min(correct / total_relevant, 1.0)


def f1_score(precision: float, recall: float) -> float:
    """Harmonic mean of precision and recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def brier_score(confidences: list[float], outcomes: list[bool]) -> float:
    """Brier score for confidence calibration. Lower is better.

    Measures the mean squared error between predicted probabilities and
    actual binary outcomes. Perfect score is 0.0, worst is 1.0.

    Args:
        confidences: Predicted probabilities in [0.0, 1.0].
        outcomes: Actual binary outcomes (True = event occurred as predicted).

    Returns:
        Brier score in [0.0, 1.0].

    Raises:
        ValueError: If inputs have different lengths or are empty.
    """
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(outcomes)} outcomes"
        )
    if not confidences:
        raise ValueError("Cannot compute Brier score on empty inputs")

    total = sum((conf - (1.0 if out else 0.0)) ** 2 for conf, out in zip(confidences, outcomes))
    return total / len(confidences)


def log_loss(confidences: list[float], outcomes: list[bool], eps: float = 1e-15) -> float:
    """Log loss (cross-entropy) for probability predictions.

    Args:
        confidences: Predicted probabilities in [0.0, 1.0].
        outcomes: Actual binary outcomes.
        eps: Small value to avoid log(0).

    Returns:
        Log loss (lower is better). Perfect is 0.0.

    Raises:
        ValueError: If inputs have different lengths or are empty.
    """
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(outcomes)} outcomes"
        )
    if not confidences:
        raise ValueError("Cannot compute log loss on empty inputs")

    total = 0.0
    for conf, out in zip(confidences, outcomes):
        p = max(eps, min(1 - eps, conf))
        if out:
            total -= math.log(p)
        else:
            total -= math.log(1 - p)
    return total / len(confidences)
