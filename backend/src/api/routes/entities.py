"""Entity routes — GET /entities, GET /entities/{ticker}."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.storage import entity_repo

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("")
async def list_entities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    name_contains: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """List entities with optional name filter."""
    entities = await entity_repo.list_entities(
        limit=limit,
        offset=offset,
        name_contains=name_contains,
        session=db,
    )
    total = await entity_repo.count_entities(session=db)
    return {
        "items": [e.model_dump(mode="json") for e in entities],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{ticker}")
async def get_entity(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """Get entity by ticker symbol."""
    entity = await entity_repo.get_entity(ticker.upper(), session=db)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity.model_dump(mode="json")
