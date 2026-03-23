"""Confidence calibration — Platt scaling and isotonic regression.

Ensures that when the model says "78% confidence", it's right ~78% of the time.
Target: <15% calibration error (Phase 1), <10% (Phase 3).
"""


def calibrate_platt(raw_scores: list[float], labels: list[bool]) -> callable:
    """Fit Platt scaling (logistic regression on raw scores).

    Returns a calibration function: raw_score → calibrated_probability.

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("Platt scaling — Phase 1 deliverable")


def calibration_error(confidences: list[float], outcomes: list[bool], n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE).

    Bins predictions by confidence, computes |avg_confidence - avg_accuracy| per bin.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Calibration error — Phase 0 deliverable")
