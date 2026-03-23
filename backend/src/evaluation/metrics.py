"""Evaluation metrics — precision, recall, F1, Brier score for signals."""


def precision_at_k(predictions: list[bool], k: int | None = None) -> float:
    """Precision: % of generated signals that were correct.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Precision metric — Phase 0 deliverable")


def recall_at_k(predictions: list[bool], total_relevant: int) -> float:
    """Recall: % of material events that generated signals.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Recall metric — Phase 0 deliverable")


def f1_score(precision: float, recall: float) -> float:
    """Harmonic mean of precision and recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def brier_score(confidences: list[float], outcomes: list[bool]) -> float:
    """Brier score for confidence calibration. Lower is better.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Brier score — Phase 0 deliverable")
