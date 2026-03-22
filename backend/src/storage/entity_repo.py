"""Entity repository — CRUD operations for the entities table."""

from src.models.entity import Entity


async def upsert_entity(entity: Entity) -> None:
    """Upsert an entity (insert or update on conflict).

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Entity upsert — Phase 0 deliverable")


async def get_entity(ticker: str) -> Entity | None:
    """Get entity by ticker.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Entity get — Phase 0 deliverable")
