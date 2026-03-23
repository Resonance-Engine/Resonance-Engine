"""Tests for risk/policy gate agent."""

from src.agents.risk_gate import contains_blocked_language


def test_blocks_buy():
    assert contains_blocked_language("You should buy AAPL now") is True


def test_blocks_sell():
    assert contains_blocked_language("Sell your TSLA shares") is True


def test_blocks_guaranteed():
    assert contains_blocked_language("This is guaranteed to go up") is True


def test_allows_historical_language():
    assert contains_blocked_language("Historically, FDA approvals lead to positive moves") is False


def test_allows_probability_language():
    assert contains_blocked_language("High probability of volatility increase") is False


def test_blocks_you_should():
    assert contains_blocked_language("You should consider this opportunity") is True
