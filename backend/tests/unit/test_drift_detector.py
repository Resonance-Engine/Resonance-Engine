"""Tests for drift detection."""

import pytest

from src.evaluation.drift_detector import (
    DriftSeverity,
    detect_accuracy_drop,
    detect_drift,
)


# --- Statistical Drift Detection ---

def test_no_drift_same_distribution():
    """Same distribution should not trigger drift."""
    baseline = [0.70, 0.72, 0.71, 0.73, 0.70]
    current = [0.71, 0.73, 0.70, 0.72, 0.71]
    result = detect_drift(baseline, current)
    assert result.drifted is False
    assert result.severity == DriftSeverity.NONE


def test_severe_drift():
    """Large accuracy drop should trigger severe drift."""
    baseline = [0.80, 0.82, 0.81, 0.83, 0.80]
    current = [0.40, 0.42, 0.38, 0.41, 0.39]
    result = detect_drift(baseline, current)
    assert result.drifted is True
    assert result.severity in (DriftSeverity.MODERATE, DriftSeverity.SEVERE)
    assert "retrain" in result.recommendation.lower()


def test_drift_p_value_range():
    """P-value should be between 0 and 1."""
    baseline = [0.70, 0.72, 0.71]
    current = [0.50, 0.52, 0.51]
    result = detect_drift(baseline, current)
    assert 0.0 <= result.p_value <= 1.0


def test_drift_too_few_values():
    with pytest.raises(ValueError, match="at least 2"):
        detect_drift([0.7], [0.5, 0.6])


def test_drift_returns_means():
    baseline = [0.80, 0.80]
    current = [0.60, 0.60]
    result = detect_drift(baseline, current)
    assert abs(result.baseline_mean - 0.80) < 0.001
    assert abs(result.current_mean - 0.60) < 0.001


# --- Simple Accuracy Drop ---

def test_accuracy_drop_detected():
    baseline = [0.80, 0.82, 0.81]
    current = [0.70, 0.72, 0.71]
    result = detect_accuracy_drop(baseline, current, threshold=0.05)
    assert result["dropped"] is True
    assert result["delta"] > 0.05


def test_accuracy_no_drop():
    baseline = [0.80, 0.82, 0.81]
    current = [0.79, 0.80, 0.81]
    result = detect_accuracy_drop(baseline, current, threshold=0.05)
    assert result["dropped"] is False


def test_accuracy_drop_empty():
    result = detect_accuracy_drop([], [0.5])
    assert result["dropped"] is False
