"""Backtesting harness — look-ahead bias, survivorship bias, overfitting detection.

Uses Bailey et al. "Probability of Backtest Overfitting" methodology.
PBO <25%: Robust; 25-50%: Moderate risk; >50%: Don't deploy.
"""


def check_look_ahead_bias(signals: list[dict]) -> list[str]:
    """Verify that all signals use only point-in-time data.

    Returns list of violations found (empty = clean).

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("Look-ahead bias check — Phase 1 deliverable")


def check_survivorship_bias(tickers: list[str], delisted_tickers: set[str]) -> dict:
    """Verify that delisted stocks are included in backtest.

    Should be ~2-3% of total per year.

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("Survivorship bias check — Phase 1 deliverable")


def probability_of_backtest_overfitting(
    performance_matrix: list[list[float]],
) -> float:
    """Bailey et al. PBO methodology.

    Split data into N partitions, compute performance in each.
    PBO <25%: Robust; 25-50%: Moderate risk; >50%: Don't deploy.

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("PBO computation — Phase 1 deliverable")
