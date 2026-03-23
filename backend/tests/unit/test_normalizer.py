"""Tests for ingestion normalizer."""

from src.ingestion.normalizer import generate_content_hash, normalize_event
from src.models.event import EventSource


def test_content_hash_deterministic():
    """Same inputs should produce same hash."""
    hash1 = generate_content_hash("SEC_EDGAR", "https://sec.gov/1", "Filing text")
    hash2 = generate_content_hash("SEC_EDGAR", "https://sec.gov/1", "Filing text")
    assert hash1 == hash2


def test_content_hash_different_inputs():
    """Different inputs should produce different hashes."""
    hash1 = generate_content_hash("SEC_EDGAR", "https://sec.gov/1", "Filing text A")
    hash2 = generate_content_hash("SEC_EDGAR", "https://sec.gov/1", "Filing text B")
    assert hash1 != hash2


def test_normalize_event_assigns_uuid():
    """Normalized event should have a UUID event_id."""
    event = normalize_event(
        source=EventSource.SEC_EDGAR,
        url="https://sec.gov/test",
        raw_text="Test filing text",
    )
    assert event.event_id is not None
    assert len(event.event_id) == 36  # UUID format


def test_normalize_event_computes_hash():
    """Normalized event should have a content_hash."""
    event = normalize_event(
        source=EventSource.SEC_EDGAR,
        url="https://sec.gov/test",
        raw_text="Test filing text",
    )
    assert event.content_hash is not None
    assert len(event.content_hash) == 16
