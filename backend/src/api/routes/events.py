"""Event routes — GET /events, GET /events/{event_id}."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.storage import event_repo

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ticker: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    since: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """List events with optional filters, ordered by timestamp descending."""
    events = await event_repo.list_events(
        limit=limit,
        offset=offset,
        ticker=ticker,
        event_type=event_type,
        source=source,
        since=since,
        session=db,
    )
    total = await event_repo.count_events(
        event_type=event_type,
        source=source,
        since=since,
        session=db,
    )
    return {
        "items": [e.model_dump(mode="json") for e in events],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """Get a single event by ID."""
    event = await event_repo.get_event(event_id, session=db)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.model_dump(mode="json")
