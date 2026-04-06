"""Tests for evaluation metrics."""

import pytest

from src.evaluation.metrics import brier_score, f1_score, log_loss, precision_at_k, recall_at_k


# --- F1 Score ---

def test_f1_perfect():
    assert f1_score(1.0, 1.0) == 1.0


def test_f1_zero_precision():
    assert f1_score(0.0, 1.0) == 0.0


def test_f1_zero_recall():
    assert f1_score(1.0, 0.0) == 0.0


def test_f1_both_zero():
    assert f1_score(0.0, 0.0) == 0.0


def test_f1_balanced():
    result = f1_score(0.8, 0.6)
    assert abs(result - 0.6857) < 0.001


# --- Precision@k ---

def test_precision_at_k_perfect():
    assert precision_at_k([True, True, True]) == 1.0


def test_precision_at_k_none_correct():
    assert precision_at_k([False, False, False]) == 0.0


def test_precision_at_k_mixed():
    assert abs(precision_at_k([True, False, True]) - 2 / 3) < 0.001


def test_precision_at_k_with_k():
    # Only look at top 2
    assert precision_at_k([True, False, True, True], k=2) == 0.5


def test_precision_at_k_empty():
    assert precision_at_k([]) == 0.0


# --- Recall@k ---

def test_recall_at_k_perfect():
    assert recall_at_k([True, True, True], total_relevant=3) == 1.0


def test_recall_at_k_partial():
    assert abs(recall_at_k([True, False], total_relevant=4) - 0.25) < 0.001


def test_recall_at_k_zero_relevant():
    assert recall_at_k([True], total_relevant=0) == 0.0


def test_recall_at_k_empty_predictions():
    assert recall_at_k([], total_relevant=5) == 0.0


# --- Brier Score ---

def test_brier_perfect_positive():
    # Confident and correct
    assert brier_score([1.0], [True]) == 0.0


def test_brier_perfect_negative():
    # Confident and correct about negative
    assert brier_score([0.0], [False]) == 0.0


def test_brier_worst_case():
    # Confident but wrong
    assert brier_score([1.0], [False]) == 1.0


def test_brier_mixed():
    result = brier_score([0.8, 0.3], [True, False])
    expected = ((0.8 - 1.0) ** 2 + (0.3 - 0.0) ** 2) / 2
    assert abs(result - expected) < 0.001


def test_brier_length_mismatch():
    with pytest.raises(ValueError, match="Length mismatch"):
        brier_score([0.5, 0.5], [True])


def test_brier_empty():
    with pytest.raises(ValueError, match="empty"):
        brier_score([], [])


# --- Log Loss ---

def test_log_loss_perfect():
    result = log_loss([0.99], [True])
    assert result < 0.02


def test_log_loss_wrong():
    result = log_loss([0.01], [True])
    assert result > 4.0  # Very high loss


def test_log_loss_length_mismatch():
    with pytest.raises(ValueError, match="Length mismatch"):
        log_loss([0.5], [True, False])
