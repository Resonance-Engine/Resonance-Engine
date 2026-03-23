"""Tests for meaningful change gating."""

from datetime import datetime, timedelta

from src.ingestion.change_gate import is_meaningful_change
from src.models.entity import Entity
from src.models.event import Event, EventSource


def _make_event(
    content_hash: str = "abc123",
    ticker: str | None = "AAPL",
    event_type: str | None = "earnings",
    minutes_ago: int = 0,
) -> Event:
    """Helper to create test events."""
    entities = [Entity(ticker=ticker, name="Test Co")] if ticker else []
    return Event(
        event_id="test",
        timestamp=datetime.utcnow() - timedelta(minutes=minutes_ago),
        source=EventSource.SEC_EDGAR,
        url="https://test.com",
        raw_text="Test",
        content_hash=content_hash,
        entities=entities,
        event_type=event_type,
    )


def test_duplicate_hash_blocked():
    """Exact content hash match should be filtered."""
    event = _make_event(content_hash="same_hash")
    recent = [_make_event(content_hash="same_hash")]
    assert is_meaningful_change(event, recent) is False


def test_new_hash_passes():
    """New content hash should pass through."""
    event = _make_event(content_hash="new_hash")
    recent = [_make_event(content_hash="old_hash")]
    assert is_meaningful_change(event, recent) is True


def test_same_story_different_source_blocked():
    """Same entity + event type within 2h window should be filtered."""
    event = _make_event(content_hash="hash_a", ticker="AAPL", event_type="earnings", minutes_ago=0)
    recent = [_make_event(content_hash="hash_b", ticker="AAPL", event_type="earnings", minutes_ago=30)]
    assert is_meaningful_change(event, recent) is False


def test_same_entity_different_type_passes():
    """Same entity but different event type should pass."""
    event = _make_event(content_hash="hash_a", ticker="AAPL", event_type="fda_approval")
    recent = [_make_event(content_hash="hash_b", ticker="AAPL", event_type="earnings")]
    assert is_meaningful_change(event, recent) is True


def test_empty_recent_always_passes():
    """No recent events means everything passes."""
    event = _make_event()
    assert is_meaningful_change(event, []) is True
