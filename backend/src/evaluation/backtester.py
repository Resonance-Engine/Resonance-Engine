"""Backtesting harness — look-ahead bias, survivorship bias, overfitting detection.

Uses Bailey et al. "Probability of Backtest Overfitting" methodology.
PBO <25%: Robust; 25-50%: Moderate risk; >50%: Don't deploy.
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class BiasReport:
    """Summary of bias checks for a backtest run."""

    look_ahead_violations: list[str]
    survivorship_missing_pct: float
    survivorship_included: int
    survivorship_total_delisted: int
    is_clean: bool


def check_look_ahead_bias(signals: list[dict]) -> list[str]:
    """Verify that all signals use only point-in-time data.

    Each signal dict must have:
    - "signal_timestamp": when the signal was generated
    - "data_timestamps": list of timestamps of data used to generate the signal

    Returns list of violation descriptions (empty = clean).

    Args:
        signals: List of signal dicts with timestamp metadata.

    Returns:
        List of violation strings. Empty list means no look-ahead bias.
    """
    violations = []
    for i, sig in enumerate(signals):
        signal_ts = sig.get("signal_timestamp")
        if signal_ts is None:
            violations.append(f"Signal {i}: missing signal_timestamp")
            continue

        if isinstance(signal_ts, str):
            signal_ts = datetime.fromisoformat(signal_ts)

        # Make timezone-aware if naive
        if signal_ts.tzinfo is None:
            signal_ts = signal_ts.replace(tzinfo=timezone.utc)

        data_timestamps = sig.get("data_timestamps", [])
        for j, dt in enumerate(data_timestamps):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            if dt > signal_ts:
                violations.append(
                    f"Signal {i}: data_timestamp[{j}] ({dt.isoformat()}) "
                    f"is after signal_timestamp ({signal_ts.isoformat()})"
                )

    return violations


def check_survivorship_bias(tickers: list[str], delisted_tickers: set[str]) -> dict:
    """Verify that delisted stocks are included in backtest.

    A healthy backtest should include ~2-3% delisted tickers per year.
    Excluding them inflates returns and creates survivorship bias.

    Args:
        tickers: All tickers used in the backtest.
        delisted_tickers: Known set of delisted/dead tickers.

    Returns:
        Dict with keys: included, total_delisted, missing, pct_included, is_healthy.
    """
    if not tickers:
        return {
            "included": 0,
            "total_delisted": len(delisted_tickers),
            "missing": list(delisted_tickers),
            "pct_included": 0.0,
            "is_healthy": len(delisted_tickers) == 0,
        }

    ticker_set = set(tickers)
    included = ticker_set & delisted_tickers
    missing = delisted_tickers - ticker_set

    pct_included = len(included) / len(delisted_tickers) if delisted_tickers else 1.0

    return {
        "included": len(included),
        "total_delisted": len(delisted_tickers),
        "missing": sorted(missing),
        "pct_included": pct_included,
        "is_healthy": pct_included >= 0.80,  # At least 80% of delisted tickers should be present
    }


def probability_of_backtest_overfitting(
    performance_matrix: list[list[float]],
    n_partitions: int = 8,
) -> float:
    """Bailey et al. (2014) Probability of Backtest Overfitting (PBO).

    Combinatorially Symmetric Cross-Validation (CSCV), the actual method:
    1. Split the N time periods into S contiguous blocks (S even).
    2. For EVERY combination of S/2 blocks as in-sample (C(S, S/2)
       combinations — the "combinatorially symmetric" part), the remaining
       S/2 blocks are out-of-sample.
    3. In each combination: pick the best strategy in-sample, then compute
       its out-of-sample RANK among all strategies.
    4. PBO = fraction of combinations where the in-sample winner ranks in
       the bottom half out-of-sample (relative rank ω <= 0.5, i.e.
       logit λ = ln(ω/(1−ω)) <= 0).

    NOTE: an earlier version used contiguous sliding half-splits (a handful
    of trials instead of C(S, S/2)) — a statistically weak estimate that
    let overfit strategies pass the deploy gate.

    Interpretation:
    - PBO < 0.25: Robust strategy
    - 0.25 <= PBO < 0.50: Moderate overfitting risk
    - PBO >= 0.50: Likely overfit, don't deploy

    Args:
        performance_matrix: Matrix of shape [n_strategies, n_periods].
            Each row is a strategy, each column is a time period's return.
        n_partitions: Number of blocks S (even, >= 2). Clamped so each
            block has at least one period. Default 8 → C(8,4)=70 trials.

    Returns:
        PBO estimate in [0.0, 1.0].

    Raises:
        ValueError: If matrix is empty or has fewer than 4 periods.
    """
    from itertools import combinations

    if not performance_matrix or not performance_matrix[0]:
        raise ValueError("Performance matrix cannot be empty")

    n_strategies = len(performance_matrix)
    n_periods = len(performance_matrix[0])

    if n_periods < 4:
        raise ValueError(f"Need at least 4 time periods, got {n_periods}")
    if n_strategies < 2:
        raise ValueError(f"Need at least 2 strategies, got {n_strategies}")

    # Validate rectangular matrix
    for row in performance_matrix:
        if len(row) != n_periods:
            raise ValueError("All strategies must have the same number of periods")

    # S contiguous blocks of (near-)equal size; S even, each block non-empty.
    s = min(n_partitions, n_periods)
    if s % 2 == 1:
        s -= 1
    s = max(s, 2)

    block_size = n_periods // s
    blocks: list[list[int]] = []
    for b in range(s):
        start = b * block_size
        end = (b + 1) * block_size if b < s - 1 else n_periods  # last takes remainder
        blocks.append(list(range(start, end)))

    def _mean_over(strat: list[float], indices: list[int]) -> float:
        return sum(strat[i] for i in indices) / len(indices)

    n_overfit = 0
    n_trials = 0

    for is_blocks in combinations(range(s), s // 2):
        is_set = set(is_blocks)
        is_indices = [i for b in is_blocks for i in blocks[b]]
        oos_indices = [i for b in range(s) if b not in is_set for i in blocks[b]]

        is_perfs = [_mean_over(strat, is_indices) for strat in performance_matrix]
        oos_perfs = [_mean_over(strat, oos_indices) for strat in performance_matrix]

        best_is_idx = max(range(n_strategies), key=lambda i: is_perfs[i])

        # Relative OOS rank of the in-sample winner: ω in (0, 1)
        rank = 1 + sum(
            1 for i in range(n_strategies)
            if i != best_is_idx and oos_perfs[i] < oos_perfs[best_is_idx]
        )
        omega = rank / (n_strategies + 1)

        # λ = ln(ω/(1−ω)) <= 0  ⇔  ω <= 0.5  (bottom half OOS)
        if omega <= 0.5:
            n_overfit += 1
        n_trials += 1

    if n_trials == 0:
        return 0.0

    return n_overfit / n_trials


def run_bias_checks(
    signals: list[dict],
    tickers: list[str],
    delisted_tickers: set[str],
) -> BiasReport:
    """Run all bias checks and return a combined report.

    Args:
        signals: Signal dicts with timestamp metadata for look-ahead check.
        tickers: All tickers in the backtest.
        delisted_tickers: Known delisted tickers.

    Returns:
        BiasReport summarizing all checks.
    """
    la_violations = check_look_ahead_bias(signals)
    surv = check_survivorship_bias(tickers, delisted_tickers)

    return BiasReport(
        look_ahead_violations=la_violations,
        survivorship_missing_pct=1.0 - surv["pct_included"],
        survivorship_included=surv["included"],
        survivorship_total_delisted=surv["total_delisted"],
        is_clean=len(la_violations) == 0 and surv["is_healthy"],
    )
