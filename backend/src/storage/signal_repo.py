"""Signal repository — CRUD operations for the signals table."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.evidence import EvidenceItem
from src.models.signal import Citation, Signal, SignalType
from src.storage.database import async_session
from src.storage.models import SignalModel

logger = logging.getLogger(__name__)

# Mapping for impact_window string → timedelta (used for expiry checks)
_WINDOW_DELTAS = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "24h": timedelta(hours=24),
    "1w": timedelta(weeks=1),
}


def _signal_to_row(signal: Signal) -> dict:
    """Convert a Pydantic Signal to a dict suitable for SignalModel insert."""
    return {
        "signal_id": signal.signal_id,
        "event_id": signal.event_id,
        "timestamp": signal.timestamp,
        "ticker": signal.ticker,
        "signal_type": signal.signal_type.value,
        "signal_text": signal.signal_text,
        "confidence": signal.confidence,
        "rationale": signal.rationale,
        "uncertainty": signal.uncertainty,
        "impact_window": signal.impact_window,
        "predicted_move": signal.predicted_move,
        "actual_move": signal.actual_move,
        "evidence": [e.model_dump() for e in signal.evidence],
        "citations": [c.model_dump() for c in signal.citations],
        "metadata_": signal.metadata,
    }


def _row_to_signal(row: SignalModel) -> Signal:
    """Convert an SQLAlchemy SignalModel row back to a Pydantic Signal."""
    return Signal(
        signal_id=row.signal_id,
        event_id=row.event_id,
        timestamp=row.timestamp,
        ticker=row.ticker,
        signal_type=SignalType(row.signal_type),
        signal_text=row.signal_text,
        confidence=row.confidence,
        rationale=row.rationale,
        uncertainty=row.uncertainty,
        impact_window=row.impact_window,
        predicted_move=row.predicted_move,
        actual_move=row.actual_move,
        evidence=[EvidenceItem(**e) for e in (row.evidence or [])],
        citations=[Citation(**c) for c in (row.citations or [])],
        metadata=row.metadata_ or {},
    )


async def insert_signal(signal: Signal, session: AsyncSession | None = None) -> None:
    """Insert a new signal into the database. Skips on conflict (idempotent).

    Args:
        signal: Pydantic Signal object to persist.
        session: Optional async session (uses default pool if not provided).
    """
    row_data = _signal_to_row(signal)

    async def _do_insert(sess: AsyncSession, own_session: bool) -> None:
        stmt = pg_insert(SignalModel).values(**row_data).on_conflict_do_nothing(
            index_elements=["signal_id"]
        )
        await sess.execute(stmt)
        if own_session:
            await sess.commit()
        else:
            # Caller owns the transaction — flush, don't commit
            await sess.flush()
        logger.info("Inserted signal %s for ticker %s", signal.signal_id, signal.ticker)

    if session is not None:
        await _do_insert(session, own_session=False)
    else:
        async with async_session() as sess:
            await _do_insert(sess, own_session=True)


async def get_signal(signal_id: str, session: AsyncSession | None = None) -> Signal | None:
    """Get a single signal by ID.

    Args:
        signal_id: UUID of the signal.
        session: Optional async session.

    Returns:
        Signal if found, None otherwise.
    """
    async def _do_get(sess: AsyncSession) -> Signal | None:
        stmt = select(SignalModel).where(SignalModel.signal_id == signal_id)
        result = await sess.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_signal(row) if row else None

    if session is not None:
        return await _do_get(session)
    async with async_session() as sess:
        return await _do_get(sess)


async def list_signals(
    limit: int = 50,
    offset: int = 0,
    ticker: str | None = None,
    event_id: str | None = None,
    signal_type: str | None = None,
    min_confidence: float | None = None,
    since: datetime | None = None,
    session: AsyncSession | None = None,
) -> list[Signal]:
    """List signals with optional filters, ordered by timestamp descending.

    Args:
        limit: Max results (default 50, max 500).
        offset: Pagination offset.
        ticker: Filter by ticker symbol.
        event_id: Filter by triggering event ID.
        signal_type: Filter by signal type.
        min_confidence: Only signals with confidence >= this value.
        since: Only signals after this timestamp.
        session: Optional async session.
    """
    limit = min(limit, 500)

    async def _do_list(sess: AsyncSession) -> list[Signal]:
        stmt = select(SignalModel).order_by(SignalModel.timestamp.desc())

        if ticker is not None:
            stmt = stmt.where(SignalModel.ticker == ticker)
        if event_id is not None:
            stmt = stmt.where(SignalModel.event_id == event_id)
        if signal_type is not None:
            stmt = stmt.where(SignalModel.signal_type == signal_type)
        if min_confidence is not None:
            stmt = stmt.where(SignalModel.confidence >= min_confidence)
        if since is not None:
            stmt = stmt.where(SignalModel.timestamp >= since)

        stmt = stmt.offset(offset).limit(limit)
        result = await sess.execute(stmt)
        rows = result.scalars().all()
        return [_row_to_signal(row) for row in rows]

    if session is not None:
        return await _do_list(session)
    async with async_session() as sess:
        return await _do_list(sess)


async def count_signals(
    ticker: str | None = None,
    signal_type: str | None = None,
    min_confidence: float | None = None,
    since: datetime | None = None,
    session: AsyncSession | None = None,
) -> int:
    """Count signals matching filters."""
    async def _do_count(sess: AsyncSession) -> int:
        stmt = select(func.count(SignalModel.signal_id))
        if ticker is not None:
            stmt = stmt.where(SignalModel.ticker == ticker)
        if signal_type is not None:
            stmt = stmt.where(SignalModel.signal_type == signal_type)
        if min_confidence is not None:
            stmt = stmt.where(SignalModel.confidence >= min_confidence)
        if since is not None:
            stmt = stmt.where(SignalModel.timestamp >= since)
        result = await sess.execute(stmt)
        return result.scalar_one()

    if session is not None:
        return await _do_count(session)
    async with async_session() as sess:
        return await _do_count(sess)


async def list_unlabeled_expired(
    limit: int = 100,
    session: AsyncSession | None = None,
) -> list[Signal]:
    """List signals whose impact_window has expired but actual_move is still NULL.

    Filters in two passes for efficiency:
      1. SQL: actual_move IS NULL AND timestamp <= now() - 1h (the shortest window)
      2. Python: keep only signals where timestamp + impact_window <= now()

    Args:
        limit: Max signals to return (default 100).
        session: Optional async session.

    Returns:
        Signals ready to be labeled with actual_move from market data.
    """
    now = datetime.now(timezone.utc)
    earliest_possible = now - _WINDOW_DELTAS["1h"]

    async def _do_list(sess: AsyncSession) -> list[Signal]:
        stmt = (
            select(SignalModel)
            .where(SignalModel.actual_move.is_(None))
            .where(SignalModel.timestamp <= earliest_possible)
            .order_by(SignalModel.timestamp.asc())
            .limit(limit * 4)  # over-fetch since some won't be expired yet by exact window
        )
        result = await sess.execute(stmt)
        rows = result.scalars().all()

        expired: list[Signal] = []
        for row in rows:
            delta = _WINDOW_DELTAS.get(row.impact_window)
            if delta is None:
                continue
            if row.timestamp + delta <= now:
                expired.append(_row_to_signal(row))
            if len(expired) >= limit:
                break
        return expired

    if session is not None:
        return await _do_list(session)
    async with async_session() as sess:
        return await _do_list(sess)


async def update_actual_move(
    signal_id: str,
    actual_move: float,
    session: AsyncSession | None = None,
) -> bool:
    """Update a signal's actual_move after market data confirms the outcome.

    Args:
        signal_id: UUID of the signal to update.
        actual_move: The observed market move (e.g., +0.03 for +3%).
        session: Optional async session.

    Returns:
        True if signal was found and updated, False if not found.
    """
    from sqlalchemy import update

    async def _do_update(sess: AsyncSession, own_session: bool) -> bool:
        stmt = (
            update(SignalModel)
            .where(SignalModel.signal_id == signal_id)
            .values(actual_move=actual_move)
        )
        result = await sess.execute(stmt)
        if own_session:
            await sess.commit()
        else:
            # Caller owns the transaction — flush, don't commit
            await sess.flush()
        updated = result.rowcount > 0
        if updated:
            logger.info("Updated actual_move for signal %s: %.4f", signal_id, actual_move)
        return updated

    if session is not None:
        return await _do_update(session, own_session=False)
    async with async_session() as sess:
        return await _do_update(sess, own_session=True)
