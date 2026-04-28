"""Feedback loop — labels expired signals with actual market moves.

Closes the prediction → outcome loop by fetching post-event market data
for each signal whose impact_window has elapsed. Persists actual_move
back to the signal row, enabling downstream evaluation (Brier, ECE,
calibration, drift) on live production data rather than only the
static labeled test set.

Runs as a scheduler loop (see src/scheduler.py) on market hours.
"""

import logging

from src.ingestion.market_data import compute_post_event_returns
from src.storage.signal_repo import list_unlabeled_expired, update_actual_move

logger = logging.getLogger(__name__)


async def label_expired_signals(batch_size: int = 50) -> dict:
    """Find signals whose impact_window has expired and label them.

    For each unlabeled-expired signal:
      1. Call market data API for the signal's specific impact_window
      2. If a return is computable, persist actual_move via signal_repo
      3. Skip silently if no price data is available (free-tier quota,
         delisted ticker, or a window that requires intraday data we
         don't subscribe to).

    Args:
        batch_size: Max signals to label per run (default 50).
            Bounded to keep within Alpha Vantage's 25 req/day free tier
            across multiple loop iterations per day.

    Returns:
        Stats dict with: scanned, labeled, no_data, errors.
    """
    stats = {"scanned": 0, "labeled": 0, "no_data": 0, "errors": 0}

    try:
        signals = await list_unlabeled_expired(limit=batch_size)
    except Exception:
        logger.exception("Feedback loop: failed to query unlabeled signals")
        return stats

    stats["scanned"] = len(signals)
    if not signals:
        return stats

    logger.info("Feedback loop: %d expired signals awaiting labels", len(signals))

    for signal in signals:
        try:
            windows = await compute_post_event_returns(
                ticker=signal.ticker,
                event_timestamp=signal.timestamp,
                windows=[signal.impact_window],
            )
        except Exception:
            logger.exception(
                "Feedback loop: market_data fetch failed for %s (%s)",
                signal.signal_id, signal.ticker,
            )
            stats["errors"] += 1
            continue

        if not windows:
            stats["no_data"] += 1
            continue

        return_pct = windows[0].return_pct
        try:
            updated = await update_actual_move(signal.signal_id, return_pct)
        except Exception:
            logger.exception(
                "Feedback loop: update_actual_move failed for %s",
                signal.signal_id,
            )
            stats["errors"] += 1
            continue

        if updated:
            stats["labeled"] += 1
            logger.info(
                "Feedback loop: labeled %s (%s, window=%s) actual_move=%.4f predicted=%.4f",
                signal.signal_id, signal.ticker, signal.impact_window,
                return_pct, signal.predicted_move or 0.0,
            )

    return stats
