"""Tests for hash-based deduplication (claim/release semantics).

Regression coverage: the old check-and-set marked a hash as seen BEFORE
processing succeeded, so a pipeline failure permanently dropped the event
for the 7-day TTL. claim()/release() lets failed processing be retried.
"""

from src.ingestion.deduplicator import DEDUP_TTL_SECONDS, claim, is_duplicate, release


class FakeRedis:
    """Minimal Redis stand-in supporting SET NX EX and DELETE."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None):
        if nx and key in self.store:
            return None  # redis returns None when NX fails
        self.store[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    def delete(self, key: str) -> int:
        existed = key in self.store
        self.store.pop(key, None)
        self.ttls.pop(key, None)
        return int(existed)

    def exists(self, key: str) -> int:
        return int(key in self.store)


def test_claim_new_hash_succeeds():
    r = FakeRedis()
    assert claim("abc123", client=r) is True
    assert "dedup:abc123" in r.store


def test_claim_sets_ttl():
    r = FakeRedis()
    claim("abc123", client=r)
    assert r.ttls["dedup:abc123"] == DEDUP_TTL_SECONDS


def test_second_claim_fails():
    """Atomic NX: only one claimer wins — no check-then-act race window."""
    r = FakeRedis()
    assert claim("abc123", client=r) is True
    assert claim("abc123", client=r) is False


def test_release_allows_reclaim():
    """Regression: a failed pipeline run must be retryable — releasing the
    claim lets the next poll process the same event."""
    r = FakeRedis()
    assert claim("abc123", client=r) is True
    release("abc123", client=r)
    assert claim("abc123", client=r) is True


def test_release_unknown_hash_is_noop():
    r = FakeRedis()
    release("never-claimed", client=r)  # must not raise


def test_is_duplicate_backcompat():
    """is_duplicate keeps its historical contract: False (and claims) on
    first sight, True on second."""
    r = FakeRedis()
    assert is_duplicate("xyz", client=r) is False
    assert is_duplicate("xyz", client=r) is True


def test_distinct_hashes_do_not_collide():
    r = FakeRedis()
    assert claim("hash-a", client=r) is True
    assert claim("hash-b", client=r) is True
