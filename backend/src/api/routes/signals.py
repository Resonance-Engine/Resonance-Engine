"""Signal routes — GET /signals, GET /signals/{signal_id}."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.storage import signal_repo

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("")
async def list_signals(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ticker: str | None = None,
    event_id: str | None = None,
    signal_type: str | None = None,
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    since: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """List signals with optional filters, ordered by timestamp descending."""
    signals = await signal_repo.list_signals(
        limit=limit,
        offset=offset,
        ticker=ticker,
        event_id=event_id,
        signal_type=signal_type,
        min_confidence=min_confidence,
        since=since,
        session=db,
    )
    total = await signal_repo.count_signals(
        ticker=ticker,
        signal_type=signal_type,
        min_confidence=min_confidence,
        since=since,
        session=db,
    )
    return {
        "items": [s.model_dump(mode="json") for s in signals],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{signal_id}")
async def get_signal(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """Get a single signal by ID with full evidence and citations."""
    signal = await signal_repo.get_signal(signal_id, session=db)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal.model_dump(mode="json")
