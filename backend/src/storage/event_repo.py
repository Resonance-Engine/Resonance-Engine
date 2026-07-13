"""Event repository — CRUD operations for the events table."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import Event, EventSource
from src.storage.database import async_session
from src.storage.models import EventModel

logger = logging.getLogger(__name__)


def _event_to_row(event: Event) -> dict:
    """Convert a Pydantic Event to a dict suitable for EventModel insert."""
    return {
        "event_id": event.event_id,
        "timestamp": event.timestamp,
        "source": event.source.value,
        "url": event.url,
        "raw_text": event.raw_text,
        "content_hash": event.content_hash,
        "entities": [e.model_dump() for e in event.entities],
        "event_type": event.event_type,
        "summary": event.summary,
        "confidence": event.confidence,
        "metadata_": event.metadata,
    }


def _row_to_event(row: EventModel) -> Event:
    """Convert an SQLAlchemy EventModel row back to a Pydantic Event."""
    return Event(
        event_id=row.event_id,
        timestamp=row.timestamp,
        source=EventSource(row.source),
        url=row.url,
        raw_text=row.raw_text,
        content_hash=row.content_hash,
        entities=row.entities or [],
        event_type=row.event_type,
        summary=row.summary,
        confidence=row.confidence,
        metadata=row.metadata_ or {},
    )


async def insert_event(event: Event, session: AsyncSession | None = None) -> None:
    """Insert a new event into the database. Skips on conflict (idempotent).

    Args:
        event: Pydantic Event object to persist.
        session: Optional async session (uses default pool if not provided).
    """
    row_data = _event_to_row(event)

    async def _do_insert(sess: AsyncSession, own_session: bool) -> None:
        stmt = pg_insert(EventModel).values(**row_data).on_conflict_do_nothing(
            index_elements=["event_id"]
        )
        await sess.execute(stmt)
        if own_session:
            await sess.commit()
        else:
            # Caller owns the transaction — committing here would break
            # multi-write atomicity (partial commits the caller can't roll back)
            await sess.flush()
        logger.info("Inserted event %s", event.event_id)

    if session is not None:
        await _do_insert(session, own_session=False)
    else:
        async with async_session() as sess:
            await _do_insert(sess, own_session=True)


async def get_event(event_id: str, session: AsyncSession | None = None) -> Event | None:
    """Get a single event by ID.

    Args:
        event_id: UUID of the event.
        session: Optional async session.

    Returns:
        Event if found, None otherwise.
    """
    async def _do_get(sess: AsyncSession) -> Event | None:
        stmt = select(EventModel).where(EventModel.event_id == event_id)
        result = await sess.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_event(row) if row else None

    if session is not None:
        return await _do_get(session)
    async with async_session() as sess:
        return await _do_get(sess)


async def list_events(
    limit: int = 50,
    offset: int = 0,
    ticker: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    since: datetime | None = None,
    session: AsyncSession | None = None,
) -> list[Event]:
    """List events with optional filters, ordered by timestamp descending.

    Args:
        limit: Max results (default 50, max 500).
        offset: Pagination offset.
        ticker: Filter by entity ticker (searches JSONB entities array).
        event_type: Filter by event type.
        source: Filter by event source (SEC_EDGAR, GDELT, NEWSAPI).
        since: Only events after this timestamp.
        session: Optional async session.
    """
    limit = min(limit, 500)

    async def _do_list(sess: AsyncSession) -> list[Event]:
        stmt = select(EventModel).order_by(EventModel.timestamp.desc())

        if event_type is not None:
            stmt = stmt.where(EventModel.event_type == event_type)
        if source is not None:
            stmt = stmt.where(EventModel.source == source)
        if since is not None:
            stmt = stmt.where(EventModel.timestamp >= since)
        if ticker is not None:
            # Search in the JSONB entities array for matching ticker
            stmt = stmt.where(
                EventModel.entities.contains([{"ticker": ticker}])
            )

        stmt = stmt.offset(offset).limit(limit)
        result = await sess.execute(stmt)
        rows = result.scalars().all()
        return [_row_to_event(row) for row in rows]

    if session is not None:
        return await _do_list(session)
    async with async_session() as sess:
        return await _do_list(sess)


async def count_events(
    event_type: str | None = None,
    source: str | None = None,
    since: datetime | None = None,
    session: AsyncSession | None = None,
) -> int:
    """Count events matching filters."""
    from sqlalchemy import func

    async def _do_count(sess: AsyncSession) -> int:
        stmt = select(func.count(EventModel.event_id))
        if event_type is not None:
            stmt = stmt.where(EventModel.event_type == event_type)
        if source is not None:
            stmt = stmt.where(EventModel.source == source)
        if since is not None:
            stmt = stmt.where(EventModel.timestamp >= since)
        result = await sess.execute(stmt)
        return result.scalar_one()

    if session is not None:
        return await _do_count(session)
    async with async_session() as sess:
        return await _do_count(sess)
