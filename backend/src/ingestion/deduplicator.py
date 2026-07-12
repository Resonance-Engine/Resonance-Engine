"""Hash-based deduplication using Redis.

Claim/release semantics: callers atomically CLAIM a content hash before
processing and RELEASE it if processing fails, so a crashed pipeline run
doesn't permanently swallow the event (the old check-and-set marked the
hash as seen up front — a pipeline failure then made every retry see a
"duplicate" and drop the event for the 7-day TTL).
"""

import redis

from src.config import settings

DEDUP_TTL_SECONDS = 7 * 86400  # 7 days


def get_redis_client() -> redis.Redis:
    """Create Redis client for dedup checks."""
    return redis.from_url(settings.redis_url, decode_responses=True)


def _key(content_hash: str) -> str:
    return f"dedup:{content_hash}"


def claim(content_hash: str, client: redis.Redis | None = None) -> bool:
    """Atomically claim a content hash for processing.

    Uses SET NX so two concurrent loops can't both claim the same hash
    (the old EXISTS-then-SETEX pattern was a check-then-act race).

    Args:
        content_hash: The event's content hash.
        client: Optional Redis client (created if omitted).

    Returns:
        True if the hash was newly claimed (caller should process the
        event), False if it was already claimed/processed (duplicate).
    """
    if client is None:
        client = get_redis_client()
    return bool(client.set(_key(content_hash), "1", nx=True, ex=DEDUP_TTL_SECONDS))


def release(content_hash: str, client: redis.Redis | None = None) -> None:
    """Release a claimed content hash after FAILED processing.

    Lets a later poll retry the event instead of dropping it for the TTL.

    Args:
        content_hash: The event's content hash.
        client: Optional Redis client (created if omitted).
    """
    if client is None:
        client = get_redis_client()
    client.delete(_key(content_hash))


def is_duplicate(content_hash: str, client: redis.Redis | None = None) -> bool:
    """Claim-style duplicate check (kept for backward compatibility).

    Equivalent to ``not claim(...)``: returns True if the hash was already
    seen, False (and claims it) if new. Prefer claim()/release() in new
    code so failed processing can release the claim.

    Args:
        content_hash: The event's content hash.
        client: Optional Redis client (created if omitted).

    Returns:
        True if duplicate (skip), False if new (process).
    """
    return not claim(content_hash, client=client)
