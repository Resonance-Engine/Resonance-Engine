"""Tests for the API quota tracker."""

from src.ingestion.quota import QuotaTracker


class TestQuotaTracker:
    def test_allows_within_limit(self):
        tracker = QuotaTracker("test_api", daily_limit=5)
        assert tracker.allow() is True
        assert tracker.used == 1
        assert tracker.remaining == 4

    def test_blocks_at_limit(self):
        tracker = QuotaTracker("test_block", daily_limit=3)
        assert tracker.allow() is True
        assert tracker.allow() is True
        assert tracker.allow() is True
        assert tracker.allow() is False  # 4th call blocked
        assert tracker.remaining == 0

    def test_status_dict(self):
        tracker = QuotaTracker("test_status", daily_limit=10)
        tracker.allow()
        tracker.allow()
        status = tracker.status()
        assert status["api"] == "test_status"
        assert status["used"] == 2
        assert status["limit"] == 10
        assert status["remaining"] == 8
        assert status["exhausted"] is False

    def test_exhausted_status(self):
        tracker = QuotaTracker("test_exhaust", daily_limit=1)
        tracker.allow()
        status = tracker.status()
        assert status["exhausted"] is True
        assert status["remaining"] == 0
