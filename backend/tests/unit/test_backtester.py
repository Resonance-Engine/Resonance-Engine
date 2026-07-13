"""Tests for backtesting harness."""

import pytest

from src.evaluation.backtester import (
    check_look_ahead_bias,
    check_survivorship_bias,
    probability_of_backtest_overfitting,
    run_bias_checks,
)


# --- Look-Ahead Bias ---

def test_look_ahead_clean():
    """No violations when all data precedes signal."""
    signals = [
        {
            "signal_timestamp": "2026-03-09T14:30:00+00:00",
            "data_timestamps": [
                "2026-03-09T14:00:00+00:00",
                "2026-03-09T14:25:00+00:00",
            ],
        }
    ]
    violations = check_look_ahead_bias(signals)
    assert violations == []


def test_look_ahead_violation():
    """Future data should be flagged."""
    signals = [
        {
            "signal_timestamp": "2026-03-09T14:30:00+00:00",
            "data_timestamps": [
                "2026-03-09T14:00:00+00:00",
                "2026-03-09T15:00:00+00:00",  # After signal!
            ],
        }
    ]
    violations = check_look_ahead_bias(signals)
    assert len(violations) == 1
    assert "after signal_timestamp" in violations[0]


def test_look_ahead_missing_timestamp():
    signals = [{"data_timestamps": ["2026-03-09T14:00:00+00:00"]}]
    violations = check_look_ahead_bias(signals)
    assert len(violations) == 1
    assert "missing signal_timestamp" in violations[0]


def test_look_ahead_empty():
    assert check_look_ahead_bias([]) == []


# --- Survivorship Bias ---

def test_survivorship_all_included():
    """All delisted tickers present — healthy."""
    tickers = ["AAPL", "MSFT", "LEHM", "BEAR"]
    delisted = {"LEHM", "BEAR"}
    result = check_survivorship_bias(tickers, delisted)
    assert result["is_healthy"] is True
    assert result["pct_included"] == 1.0


def test_survivorship_missing():
    """Missing delisted tickers — unhealthy."""
    tickers = ["AAPL", "MSFT"]
    delisted = {"LEHM", "BEAR", "ENRN"}
    result = check_survivorship_bias(tickers, delisted)
    assert result["is_healthy"] is False
    assert result["included"] == 0
    assert len(result["missing"]) == 3


def test_survivorship_partial():
    """Some delisted present, some missing."""
    tickers = ["AAPL", "LEHM"]
    delisted = {"LEHM", "BEAR"}
    result = check_survivorship_bias(tickers, delisted)
    assert result["included"] == 1
    assert result["pct_included"] == 0.5


def test_survivorship_no_delisted():
    """No delisted tickers to check."""
    result = check_survivorship_bias(["AAPL"], set())
    assert result["is_healthy"] is True


# --- Probability of Backtest Overfitting ---

def test_pbo_robust_strategy():
    """Consistent strategy should have low PBO."""
    # Strategy 0 consistently beats strategy 1
    matrix = [
        [0.1, 0.12, 0.11, 0.13, 0.10, 0.12],
        [0.02, 0.01, 0.03, 0.01, 0.02, 0.01],
    ]
    pbo = probability_of_backtest_overfitting(matrix)
    assert pbo < 0.5  # Should be robust


def test_pbo_overfit_strategy():
    """Strategy that only works in-sample should have high PBO."""
    # Strategy 0 great in first half, terrible in second
    matrix = [
        [0.5, 0.5, 0.5, -0.5, -0.5, -0.5],
        [0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
    ]
    pbo = probability_of_backtest_overfitting(matrix)
    assert pbo > 0.0  # Should show overfitting risk


def test_pbo_empty():
    with pytest.raises(ValueError, match="empty"):
        probability_of_backtest_overfitting([])


def test_pbo_too_few_periods():
    with pytest.raises(ValueError, match="at least 4"):
        probability_of_backtest_overfitting([[0.1, 0.2], [0.3, 0.4]])


# --- Combined Bias Report ---

def test_run_bias_checks_clean():
    signals = [
        {
            "signal_timestamp": "2026-03-09T14:30:00+00:00",
            "data_timestamps": ["2026-03-09T14:00:00+00:00"],
        }
    ]
    tickers = ["AAPL", "LEHM"]
    delisted = {"LEHM"}
    report = run_bias_checks(signals, tickers, delisted)
    assert report.is_clean is True
    assert len(report.look_ahead_violations) == 0


# --- CSCV combinatorial behavior (Bailey et al. 2014) ---

def test_pbo_dominant_strategy_is_zero():
    """A strategy that wins in EVERY period must have PBO = 0 under real
    CSCV — the in-sample winner always ranks top out-of-sample."""
    matrix = [
        [0.10] * 16,
        [0.01] * 16,
        [0.02] * 16,
    ]
    assert probability_of_backtest_overfitting(matrix) == 0.0


def test_pbo_pure_noise_is_high():
    """With antisymmetric noise (each strategy's IS win implies OOS loss),
    the in-sample winner should usually rank bottom-half OOS.

    The old sliding-half-split version produced very few trials and a
    biased estimate; combinatorial CSCV over C(8,4)=70 trials catches it."""
    import random
    rng = random.Random(42)
    # Strategies with zero-mean returns, independent across periods
    matrix = [[rng.gauss(0, 1) for _ in range(16)] for _ in range(10)]
    pbo = probability_of_backtest_overfitting(matrix)
    assert pbo >= 0.3  # noise → selection is not predictive OOS


def test_pbo_uses_combinatorial_trials():
    """8 partitions → C(8,4) = 70 trials, exercised without error on a
    non-divisible period count (17 periods → last block takes remainder)."""
    matrix = [
        [0.1] * 17,
        [0.05] * 17,
    ]
    assert probability_of_backtest_overfitting(matrix, n_partitions=8) == 0.0
