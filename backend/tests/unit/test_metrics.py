"""Tests for evaluation metrics."""

from src.evaluation.metrics import f1_score


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
