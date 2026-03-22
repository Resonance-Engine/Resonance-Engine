"""Event repository — CRUD operations for the events table."""

from src.models.event import Event


async def insert_event(event: Event) -> None:
    """Insert a new event into the database.

    TODO: Phase 0 deliverable
    - Convert Pydantic Event to SQLAlchemy EventModel
    - Insert via async session
    - Handle unique constraint on event_id
    """
    raise NotImplementedError("Event insert — Phase 0 deliverable")


async def get_event(event_id: str) -> Event | None:
    """Get a single event by ID.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Event get — Phase 0 deliverable")


async def list_events(
    limit: int = 50,
    offset: int = 0,
    ticker: str | None = None,
    event_type: str | None = None,
) -> list[Event]:
    """List events with optional filters.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Event list — Phase 0 deliverable")
