"""Tests for confidence calibration."""

import pytest

from src.evaluation.calibration import (
    CalibrationBin,
    calibrate_platt,
    calibration_error,
    maximum_calibration_error,
    reliability_diagram,
)


# --- Expected Calibration Error ---

def test_ece_perfect_calibration():
    """Perfectly calibrated predictions should have ECE near 0."""
    # In the 0.9-1.0 bin: avg confidence 0.9, accuracy 1.0 (1/1)
    # In the 0.1-0.2 bin: avg confidence 0.1, accuracy 0.0 (0/1)
    # This is close to calibrated
    confs = [0.9, 0.1]
    outcomes = [True, False]
    ece = calibration_error(confs, outcomes)
    assert ece < 0.15  # Near-perfectly calibrated


def test_ece_overconfident():
    """Overconfident predictions: high confidence, low accuracy."""
    confs = [0.9, 0.9, 0.9, 0.9]
    outcomes = [True, False, False, False]  # Only 25% accuracy at 90% confidence
    ece = calibration_error(confs, outcomes)
    assert ece > 0.5  # Heavily miscalibrated


def test_ece_all_correct_high_conf():
    """All correct at high confidence should have low ECE."""
    confs = [0.95, 0.92, 0.88, 0.91]
    outcomes = [True, True, True, True]
    ece = calibration_error(confs, outcomes)
    assert ece < 0.15


def test_ece_length_mismatch():
    with pytest.raises(ValueError, match="Length mismatch"):
        calibration_error([0.5], [True, False])


def test_ece_empty():
    with pytest.raises(ValueError, match="empty"):
        calibration_error([], [])


# --- Maximum Calibration Error ---

def test_mce_perfect():
    confs = [0.95, 0.92]
    outcomes = [True, True]
    mce = maximum_calibration_error(confs, outcomes)
    assert mce < 0.15


def test_mce_overconfident():
    confs = [0.9, 0.9, 0.9, 0.9]
    outcomes = [True, False, False, False]
    mce = maximum_calibration_error(confs, outcomes)
    assert mce > 0.5


# --- Reliability Diagram ---

def test_reliability_diagram_returns_bins():
    confs = [0.1, 0.3, 0.5, 0.7, 0.9]
    outcomes = [False, False, True, True, True]
    bins = reliability_diagram(confs, outcomes)
    assert isinstance(bins, list)
    assert all(isinstance(b, CalibrationBin) for b in bins)
    assert len(bins) > 0


def test_reliability_diagram_bin_counts():
    confs = [0.15, 0.15, 0.85, 0.85]
    outcomes = [False, True, True, True]
    bins = reliability_diagram(confs, outcomes, n_bins=10)
    # Should have 2 non-empty bins: 0.1-0.2 and 0.8-0.9
    assert len(bins) == 2
    assert bins[0].count == 2
    assert bins[1].count == 2


# --- Platt Scaling ---

def test_platt_returns_callable():
    scores = [0.1, 0.3, 0.5, 0.7, 0.9]
    labels = [False, False, True, True, True]
    calibrate = calibrate_platt(scores, labels)
    assert callable(calibrate)


def test_platt_output_range():
    scores = [0.1, 0.3, 0.5, 0.7, 0.9]
    labels = [False, False, True, True, True]
    calibrate = calibrate_platt(scores, labels)
    for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
        p = calibrate(s)
        assert 0.0 <= p <= 1.0


def test_platt_monotonic():
    """Higher raw scores should map to higher calibrated probabilities."""
    scores = [0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]
    labels = [False, False, False, True, True, True, True]
    calibrate = calibrate_platt(scores, labels)
    calibrated = [calibrate(s) for s in [0.1, 0.5, 0.9]]
    assert calibrated[0] < calibrated[1] < calibrated[2]


def test_platt_empty():
    with pytest.raises(ValueError, match="empty"):
        calibrate_platt([], [])
