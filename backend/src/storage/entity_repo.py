"""Entity repository — CRUD operations for the entities table."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity import Entity
from src.storage.database import async_session
from src.storage.models import EntityModel

logger = logging.getLogger(__name__)


def _entity_to_row(entity: Entity) -> dict:
    """Convert a Pydantic Entity to a dict suitable for EntityModel insert."""
    return {
        "ticker": entity.ticker,
        "cik": entity.cik,
        "name": entity.name,
        "sic_code": entity.sic_code,
        "metadata_": {},
        "updated_at": datetime.now(timezone.utc),
    }


def _row_to_entity(row: EntityModel) -> Entity:
    """Convert an SQLAlchemy EntityModel row back to a Pydantic Entity."""
    return Entity(
        ticker=row.ticker,
        cik=row.cik,
        name=row.name,
        sic_code=row.sic_code,
    )


async def upsert_entity(entity: Entity, session: AsyncSession | None = None) -> None:
    """Upsert an entity — insert or update name/CIK/SIC on conflict.

    Args:
        entity: Pydantic Entity object to persist.
        session: Optional async session (uses default pool if not provided).
    """
    row_data = _entity_to_row(entity)

    async def _do_upsert(sess: AsyncSession) -> None:
        stmt = (
            pg_insert(EntityModel)
            .values(**row_data)
            .on_conflict_do_update(
                index_elements=["ticker"],
                set_={
                    "cik": row_data["cik"],
                    "name": row_data["name"],
                    "sic_code": row_data["sic_code"],
                    "updated_at": row_data["updated_at"],
                },
            )
        )
        await sess.execute(stmt)
        await sess.commit()
        logger.info("Upserted entity %s (%s)", entity.ticker, entity.name)

    if session is not None:
        await _do_upsert(session)
    else:
        async with async_session() as sess:
            await _do_upsert(sess)


async def get_entity(ticker: str, session: AsyncSession | None = None) -> Entity | None:
    """Get entity by ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        session: Optional async session.

    Returns:
        Entity if found, None otherwise.
    """
    async def _do_get(sess: AsyncSession) -> Entity | None:
        stmt = select(EntityModel).where(EntityModel.ticker == ticker)
        result = await sess.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_entity(row) if row else None

    if session is not None:
        return await _do_get(session)
    async with async_session() as sess:
        return await _do_get(sess)


async def get_entity_by_cik(cik: str, session: AsyncSession | None = None) -> Entity | None:
    """Get entity by CIK number.

    Args:
        cik: SEC Central Index Key.
        session: Optional async session.

    Returns:
        Entity if found, None otherwise.
    """
    async def _do_get(sess: AsyncSession) -> Entity | None:
        stmt = select(EntityModel).where(EntityModel.cik == cik)
        result = await sess.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_entity(row) if row else None

    if session is not None:
        return await _do_get(session)
    async with async_session() as sess:
        return await _do_get(sess)


async def list_entities(
    limit: int = 100,
    offset: int = 0,
    name_contains: str | None = None,
    session: AsyncSession | None = None,
) -> list[Entity]:
    """List entities with optional name filter, ordered alphabetically by ticker.

    Args:
        limit: Max results (default 100, max 1000).
        offset: Pagination offset.
        name_contains: Case-insensitive substring match on company name.
        session: Optional async session.
    """
    limit = min(limit, 1000)

    async def _do_list(sess: AsyncSession) -> list[Entity]:
        stmt = select(EntityModel).order_by(EntityModel.ticker.asc())

        if name_contains is not None:
            stmt = stmt.where(EntityModel.name.ilike(f"%{name_contains}%"))

        stmt = stmt.offset(offset).limit(limit)
        result = await sess.execute(stmt)
        rows = result.scalars().all()
        return [_row_to_entity(row) for row in rows]

    if session is not None:
        return await _do_list(session)
    async with async_session() as sess:
        return await _do_list(sess)


async def count_entities(session: AsyncSession | None = None) -> int:
    """Count total entities in the database."""
    async def _do_count(sess: AsyncSession) -> int:
        stmt = select(func.count(EntityModel.ticker))
        result = await sess.execute(stmt)
        return result.scalar_one()

    if session is not None:
        return await _do_count(session)
    async with async_session() as sess:
        return await _do_count(sess)
