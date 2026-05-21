"""Tests for EDGAR API client — uses mocked httpx responses."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.ingestion.edgar.client import (
    _normalize_cik,
    fetch_company_facts,
    fetch_filing_document,
    fetch_recent_filings,
    fetch_submission_history,
)


class TestNormalizeCik:
    def test_pads_short_cik(self):
        assert _normalize_cik("320193") == "0000320193"

    def test_strips_leading_zeros_then_pads(self):
        assert _normalize_cik("0000320193") == "0000320193"

    def test_single_digit(self):
        assert _normalize_cik("5") == "0000000005"


class TestFetchFilingDocument:
    @pytest.mark.asyncio
    async def test_constructs_correct_url(self):
        mock_response = AsyncMock()
        mock_response.text = "<SEC-DOCUMENT>fake filing content</SEC-DOCUMENT>"
        mock_response.raise_for_status = lambda: None

        with patch("src.ingestion.edgar.client._throttled_get", return_value=mock_response) as mock_get:
            result = await fetch_filing_document("0000320193-26-000042", "320193")

            assert result == "<SEC-DOCUMENT>fake filing content</SEC-DOCUMENT>"
            call_url = mock_get.call_args[0][1]
            assert "0000320193" in call_url
            assert "000032019326000042" in call_url


class TestFetchCompanyFacts:
    @pytest.mark.asyncio
    async def test_returns_structured_data(self):
        mock_data = {
            "cik": 320193,
            "entityName": "Apple Inc.",
            "facts": {"us-gaap": {"Revenue": {}}},
        }
        mock_response = AsyncMock()
        mock_response.json = lambda: mock_data
        mock_response.raise_for_status = lambda: None

        with patch("src.ingestion.edgar.client._throttled_get", return_value=mock_response):
            result = await fetch_company_facts("320193")

            assert result["entity_name"] == "Apple Inc."
            assert "us-gaap" in result["facts"]


class TestFetchSubmissionHistory:
    @pytest.mark.asyncio
    async def test_parses_recent_filings(self):
        mock_data = {
            "cik": "320193",
            "name": "Apple Inc.",
            "tickers": ["AAPL"],
            "sic": "3571",
            "sicDescription": "Electronic Computers",
            "filings": {
                "recent": {
                    "accessionNumber": ["0000320193-26-000042", "0000320193-26-000041"],
                    "form": ["8-K", "10-Q"],
                    "filingDate": ["2026-03-15", "2026-03-01"],
                    "primaryDocument": ["filing.htm", "filing.htm"],
                }
            },
        }
        mock_response = AsyncMock()
        mock_response.json = lambda: mock_data
        mock_response.raise_for_status = lambda: None

        with patch("src.ingestion.edgar.client._throttled_get", return_value=mock_response):
            result = await fetch_submission_history("320193")

            assert result["entity_name"] == "Apple Inc."
            assert result["tickers"] == ["AAPL"]
            assert len(result["recent_filings"]) == 2
            assert result["recent_filings"][0]["form_type"] == "8-K"


class TestFetchRecentFilings:
    @pytest.mark.asyncio
    async def test_returns_empty_on_no_hits(self):
        mock_response = AsyncMock()
        mock_response.json = lambda: {"hits": {"hits": []}}
        mock_response.raise_for_status = lambda: None

        with patch("src.ingestion.edgar.client._throttled_get", return_value=mock_response):
            result = await fetch_recent_filings(form_type="8-K", limit=10)
            assert result == []

    @pytest.mark.asyncio
    async def test_parses_search_results(self):
        mock_data = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "adsh": "0000320193-26-000042",
                            "entity_id": "320193",
                            "entity_name": "Apple Inc.",
                            "form_type": "8-K",
                            "file_date": "2026-03-15",
                            "file_num": "001-36743",
                        }
                    }
                ]
            }
        }
        mock_response = AsyncMock()
        mock_response.json = lambda: mock_data
        mock_response.raise_for_status = lambda: None

        with patch("src.ingestion.edgar.client._throttled_get", return_value=mock_response):
            result = await fetch_recent_filings(
                form_type="8-K",
                start_date="2026-03-15",
                end_date="2026-03-15",
                limit=10,
            )

            assert len(result) == 1
            assert result[0]["company_name"] == "Apple Inc."
            assert result[0]["cik"] == "320193"
            assert result[0]["accession_number"] == "0000320193-26-000042"
