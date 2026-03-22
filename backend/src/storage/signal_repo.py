"""Signal repository — CRUD operations for the signals table."""

from src.models.signal import Signal


async def insert_signal(signal: Signal) -> None:
    """Insert a new signal into the database.

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("Signal insert — Phase 1 deliverable")


async def get_signal(signal_id: str) -> Signal | None:
    """Get a single signal by ID.

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("Signal get — Phase 1 deliverable")


async def list_signals(
    limit: int = 50,
    offset: int = 0,
    ticker: str | None = None,
    min_confidence: float | None = None,
) -> list[Signal]:
    """List signals with optional filters.

    TODO: Phase 1 deliverable
    """
    raise NotImplementedError("Signal list — Phase 1 deliverable")
