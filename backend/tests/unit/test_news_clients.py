"""Tests for GDELT and NewsAPI client parsing logic.

These tests validate article parsing without making real API calls.
"""

from src.ingestion.newsapi.client import _parse_articles


class TestNewsAPIParser:
    def test_parse_valid_articles(self):
        raw = [
            {
                "title": "Apple reports record earnings",
                "description": "Revenue grew 12% year-over-year.",
                "url": "https://example.com/apple-earnings",
                "publishedAt": "2026-04-09T14:00:00Z",
                "source": {"name": "Reuters"},
                "author": "John Doe",
            },
            {
                "title": "Fed holds rates steady",
                "description": "The Federal Reserve left rates unchanged.",
                "url": "https://example.com/fed-rates",
                "publishedAt": "2026-04-09T13:00:00Z",
                "source": {"name": "Bloomberg"},
                "author": None,
            },
        ]
        result = _parse_articles(raw)
        assert len(result) == 2
        assert result[0]["title"] == "Apple reports record earnings"
        assert result[0]["source_name"] == "Reuters"
        assert "Revenue grew" in result[0]["raw_text"]
        assert result[1]["author"] is None

    def test_skips_empty_title(self):
        raw = [
            {"title": "", "url": "https://x.com/a", "description": "No title"},
            {"title": None, "url": "https://x.com/b", "description": "Null title"},
        ]
        result = _parse_articles(raw)
        assert len(result) == 0

    def test_skips_empty_url(self):
        raw = [{"title": "Good title", "url": "", "description": "No URL"}]
        result = _parse_articles(raw)
        assert len(result) == 0

    def test_raw_text_combines_title_and_description(self):
        raw = [
            {
                "title": "Big news",
                "description": "Details here",
                "url": "https://x.com/news",
                "publishedAt": "2026-04-09T12:00:00Z",
                "source": {"name": "Test"},
            },
        ]
        result = _parse_articles(raw)
        assert result[0]["raw_text"] == "Big news. Details here"

    def test_raw_text_title_only_when_no_description(self):
        raw = [
            {
                "title": "Headline only",
                "description": "",
                "url": "https://x.com/headline",
                "publishedAt": "2026-04-09T12:00:00Z",
                "source": {"name": "Test"},
            },
        ]
        result = _parse_articles(raw)
        assert result[0]["raw_text"] == "Headline only"
