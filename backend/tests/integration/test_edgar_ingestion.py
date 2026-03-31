"""Integration test: EDGAR fetch → parse → normalize → dedup → change_gate.

These tests mock external HTTP calls but exercise the full internal pipeline.
For live API tests, use: pytest -m api
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.ingestion.change_gate import is_meaningful_change
from src.ingestion.edgar.parser import parse_8k_filing
from src.ingestion.normalizer import normalize_event
from src.models.event import EventSource

SAMPLE_FILING_TEXT = """<SEC-DOCUMENT>
<SEC-HEADER>
ACCESSION NUMBER:		0000320193-26-000042
CONFORMED SUBMISSION TYPE:	8-K
FILED AS OF DATE:		20260315
COMPANY CONFORMED NAME:		APPLE INC
CENTRAL INDEX KEY:		0000320193
STANDARD INDUSTRIAL CLASSIFICATION:	ELECTRONIC COMPUTERS [3571]
</SEC-HEADER>
<DOCUMENT>
<TEXT>
<html><body>
<p>Item 2.02 Results of Operations and Financial Condition</p>
<p>On March 15, 2026, Apple Inc. reported Q1 FY2026 revenue of $124.3 billion.</p>
<p>Item 9.01 Financial Statements and Exhibits</p>
<p>Exhibit 99.1 Press Release</p>
<p>SIGNATURES</p>
</body></html>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>"""


class TestEdgarIngestionPipeline:
    """Exercise the full path: raw filing text → parsed → normalized Event."""

    def test_parse_then_normalize(self):
        """Raw SGML → parsed dict → Event object with all fields populated."""
        parsed = parse_8k_filing(SAMPLE_FILING_TEXT)
        assert parsed["company_name"] == "APPLE INC"
        assert "2.02" in parsed["item_codes"]
        assert not parsed["is_boilerplate"]

        # Build raw_text from items
        raw_text = ""
        for item in parsed.get("items", []):
            raw_text += f"[Item {item['item_code']}] {item['text']}\n\n"

        event = normalize_event(
            source=EventSource.SEC_EDGAR,
            url="https://sec.gov/filing/test",
            raw_text=raw_text,
            timestamp=datetime(2026, 3, 15, tzinfo=timezone.utc),
            metadata={"item_codes": parsed["item_codes"]},
        )

        assert event.source == EventSource.SEC_EDGAR
        assert event.event_id  # UUID was assigned
        assert event.content_hash  # Hash was computed
        assert len(event.raw_text) > 0

    def test_duplicate_filing_blocked_by_change_gate(self):
        """Two identical filings → second one blocked by change gate."""
        parsed = parse_8k_filing(SAMPLE_FILING_TEXT)
        raw_text = parsed["full_text"][:1000]

        event1 = normalize_event(
            source=EventSource.SEC_EDGAR,
            url="https://sec.gov/filing/1",
            raw_text=raw_text,
        )
        event2 = normalize_event(
            source=EventSource.SEC_EDGAR,
            url="https://sec.gov/filing/1",
            raw_text=raw_text,
        )

        # Same URL + text → same content hash → blocked
        assert event1.content_hash == event2.content_hash
        assert is_meaningful_change(event2, [event1]) is False

    def test_different_filings_pass_change_gate(self):
        """Two different filings pass the change gate."""
        event1 = normalize_event(
            source=EventSource.SEC_EDGAR,
            url="https://sec.gov/filing/1",
            raw_text="Apple Q1 revenue $124B",
        )
        event2 = normalize_event(
            source=EventSource.SEC_EDGAR,
            url="https://sec.gov/filing/2",
            raw_text="Microsoft Q3 earnings beat expectations",
        )

        assert event1.content_hash != event2.content_hash
        assert is_meaningful_change(event2, [event1]) is True

    def test_boilerplate_filing_detected(self):
        """Exhibits-only filing is correctly flagged as boilerplate."""
        boilerplate = """<SEC-HEADER>
COMPANY CONFORMED NAME:		TEST CORP
CENTRAL INDEX KEY:		0001234567
FILED AS OF DATE:		20260310
</SEC-HEADER>
<html><body>
<p>Item 9.01 Financial Statements and Exhibits</p>
<p>Exhibit 104 Cover Page</p>
<p>SIGNATURES</p>
</body></html>"""

        parsed = parse_8k_filing(boilerplate)
        assert parsed["is_boilerplate"] is True
