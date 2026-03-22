"""Hash-based deduplication using Redis."""

import redis

from src.config import settings

DEDUP_TTL_SECONDS = 7 * 86400  # 7 days


def get_redis_client() -> redis.Redis:
    """Create Redis client for dedup checks."""
    return redis.from_url(settings.redis_url, decode_responses=True)


def is_duplicate(content_hash: str, client: redis.Redis | None = None) -> bool:
    """Check if we've already processed an event with this content hash.

    Returns True if duplicate (skip), False if new (process).
    """
    if client is None:
        client = get_redis_client()

    key = f"dedup:{content_hash}"
    if client.exists(key):
        return True

    client.setex(key, DEDUP_TTL_SECONDS, "1")
    return False
