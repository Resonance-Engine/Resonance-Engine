"""Tests for EDGAR API client — uses mocked httpx responses."""

from unittest.mock import AsyncMock, patch

import pytest

from src.ingestion.edgar.client import (
    _efts_hit_to_filing,
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
            result = await fetch_filing_document("0000320193-26-000042", "0000320193")

            assert result == "<SEC-DOCUMENT>fake filing content</SEC-DOCUMENT>"
            call_url = mock_get.call_args[0][1]
            # Archives paths need the UNPADDED CIK (padded form 301s)
            assert "/edgar/data/320193/" in call_url
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
        """Mock uses the REAL EFTS _source shape (captured from the live API
        2026-07-12). The previous mock invented entity_id/entity_name/
        form_type fields that don't exist — the same wrong assumption the
        parser had, so the test was green while production 404'd on every
        filing URL."""
        mock_data = {
            "hits": {
                "hits": [
                    {
                        "_id": "0000320193-26-000042:aapl-20260315.htm",
                        "_source": {
                            "ciks": ["0000320193"],
                            "display_names": ["Apple Inc.  (AAPL)  (CIK 0000320193)"],
                            "form": "8-K",
                            "root_forms": ["8-K"],
                            "adsh": "0000320193-26-000042",
                            "file_date": "2026-03-15",
                            "file_num": ["001-36743"],
                            "items": ["2.02", "9.01"],
                        },
                    },
                    {
                        # Second document of the SAME filing — must be deduped
                        "_id": "0000320193-26-000042:ex99-1.htm",
                        "_source": {
                            "ciks": ["0000320193"],
                            "display_names": ["Apple Inc.  (AAPL)  (CIK 0000320193)"],
                            "form": "8-K",
                            "adsh": "0000320193-26-000042",
                            "file_date": "2026-03-15",
                            "file_num": ["001-36743"],
                            "items": ["2.02", "9.01"],
                        },
                    },
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

            # Two document hits, ONE filing
            assert len(result) == 1
            filing = result[0]
            assert filing["company_name"] == "Apple Inc."
            assert filing["ticker"] == "AAPL"
            assert filing["cik"] == "320193"
            assert filing["accession_number"] == "0000320193-26-000042"
            assert filing["form_type"] == "8-K"
            assert filing["item_codes"] == ["2.02", "9.01"]
            assert filing["file_url"] == (
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019326000042/0000320193-26-000042.txt"
            )


class TestEftsHitToFiling:
    """_efts_hit_to_filing against real _source shapes from the live API."""

    def test_multi_ticker_takes_first(self):
        # Real example: Occidental "OXY, OXY-WT"
        source = {
            "ciks": ["0000797468"],
            "display_names": ["OCCIDENTAL PETROLEUM CORP /DE/  (OXY, OXY-WT)  (CIK 0000797468)"],
            "form": "8-K",
            "adsh": "0001628280-26-047886",
            "file_date": "2026-07-10",
            "file_num": ["001-09210"],
            "items": ["2.02", "9.01"],
        }
        filing = _efts_hit_to_filing(source, "8-K")
        assert filing["ticker"] == "OXY"
        assert filing["cik"] == "797468"
        assert filing["company_name"] == "OCCIDENTAL PETROLEUM CORP /DE/"

    def test_no_ticker_display_name(self):
        # Companies without tickers: "Name  (CIK 0001234567)" — the first
        # parenthetical is the CIK, not a ticker
        source = {
            "ciks": ["0001234567"],
            "display_names": ["Private Holdings LLC  (CIK 0001234567)"],
            "form": "8-K",
            "adsh": "0001234567-26-000001",
            "file_date": "2026-07-10",
            "file_num": ["001-00001"],
        }
        filing = _efts_hit_to_filing(source, "8-K")
        assert filing["ticker"] == ""
        assert filing["company_name"] == "Private Holdings LLC"

    def test_amended_form_preserved(self):
        """The actual form ("8-K/A") must win over the requested form."""
        source = {
            "ciks": ["0001968487"],
            "display_names": ["Worthington Steel, Inc.  (WS)  (CIK 0001968487)"],
            "form": "8-K/A",
            "adsh": "0001968487-26-000020",
            "file_date": "2026-07-10",
            "file_num": ["001-41830"],
            "items": ["2.02", "9.01"],
        }
        filing = _efts_hit_to_filing(source, "8-K")
        assert filing["form_type"] == "8-K/A"
        assert filing["file_url"] == (
            "https://www.sec.gov/Archives/edgar/data/"
            "1968487/000196848726000020/0001968487-26-000020.txt"
        )

    def test_missing_fields_do_not_crash(self):
        filing = _efts_hit_to_filing({"adsh": "0000000001-26-000001"}, "8-K")
        assert filing["cik"] == ""
        assert filing["company_name"] == ""
        assert filing["ticker"] == ""
        assert filing["item_codes"] == []
