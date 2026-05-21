"""Tests for EDGAR filing parser."""

from src.ingestion.edgar.parser import (
    ITEM_8K_DESCRIPTIONS,
    _extract_items_from_8k,
    _extract_sgml_header,
    _html_to_text,
    _is_boilerplate_8k,
    parse_8k_filing,
    parse_10k_filing,
)

SAMPLE_8K_SGML = """<SEC-DOCUMENT>
<SEC-HEADER>
ACCESSION NUMBER:		0000320193-26-000042
CONFORMED SUBMISSION TYPE:	8-K
FILED AS OF DATE:		20260315
COMPANY CONFORMED NAME:		APPLE INC
CENTRAL INDEX KEY:		0000320193
STANDARD INDUSTRIAL CLASSIFICATION:	ELECTRONIC COMPUTERS [3571]
</SEC-HEADER>
<DOCUMENT>
<TYPE>8-K
<SEQUENCE>1
<TEXT>
<html>
<body>
<h2>CURRENT REPORT</h2>
<p>Pursuant to Section 13 or 15(d) of the Securities Exchange Act of 1934</p>

<p>Item 2.02 Results of Operations and Financial Condition</p>
<p>On March 15, 2026, Apple Inc. issued a press release announcing financial results
for its fiscal first quarter ended January 2026. Revenue was $124.3 billion,
representing a 9% increase year-over-year. Earnings per share were $2.18.</p>

<p>Item 9.01 Financial Statements and Exhibits</p>
<p>Exhibit 99.1 Press Release dated March 15, 2026.</p>

<p>SIGNATURES</p>
<p>Pursuant to the requirements of the Securities Exchange Act of 1934.</p>
</body>
</html>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>"""


SAMPLE_BOILERPLATE_8K = """<SEC-DOCUMENT>
<SEC-HEADER>
COMPANY CONFORMED NAME:		BORING CORP
CENTRAL INDEX KEY:		0001234567
FILED AS OF DATE:		20260310
</SEC-HEADER>
<DOCUMENT>
<TEXT>
<html><body>
<p>Item 9.01 Financial Statements and Exhibits</p>
<p>Exhibit 104 Cover Page Interactive Data File.</p>
<p>SIGNATURES</p>
</body></html>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>"""


class TestSgmlHeader:
    def test_extracts_company_name(self):
        header = _extract_sgml_header(SAMPLE_8K_SGML)
        assert header["company_name"] == "APPLE INC"

    def test_extracts_cik(self):
        header = _extract_sgml_header(SAMPLE_8K_SGML)
        assert header["cik"] == "0000320193"

    def test_extracts_filed_date(self):
        header = _extract_sgml_header(SAMPLE_8K_SGML)
        assert header["filed_date"] == "20260315"

    def test_extracts_sic_code(self):
        header = _extract_sgml_header(SAMPLE_8K_SGML)
        assert header["sic_code"] == "3571"

    def test_extracts_accession_number(self):
        header = _extract_sgml_header(SAMPLE_8K_SGML)
        assert header["accession_number"] == "0000320193-26-000042"


class TestHtmlToText:
    def test_strips_tags(self):
        html = "<p>Hello <b>world</b></p>"
        text = _html_to_text(html)
        assert "Hello" in text
        assert "world" in text
        assert "<p>" not in text

    def test_removes_scripts(self):
        html = "<html><script>alert('x')</script><body>content</body></html>"
        text = _html_to_text(html)
        assert "alert" not in text
        assert "content" in text


class TestExtractItems:
    def test_extracts_item_codes(self):
        text = (
            "Item 2.02 Results of Operations\n"
            "Revenue was $124.3 billion.\n"
            "Item 9.01 Financial Statements\n"
            "Exhibit 99.1 attached."
        )
        items = _extract_items_from_8k(text)
        codes = [i["item_code"] for i in items]
        assert "2.02" in codes
        assert "9.01" in codes

    def test_item_has_text(self):
        text = "Item 2.02 Results\nRevenue was strong.\nItem 9.01 Exhibits\nAttached."
        items = _extract_items_from_8k(text)
        item_202 = next(i for i in items if i["item_code"] == "2.02")
        assert "Revenue" in item_202["text"]

    def test_item_descriptions_populated(self):
        text = "Item 5.02: Officer departure details here. Item 9.01 Exhibits."
        items = _extract_items_from_8k(text)
        item_502 = next(i for i in items if i["item_code"] == "5.02")
        assert "Departure" in item_502["item_description"]


class TestBoilerplateDetection:
    def test_exhibits_only_is_boilerplate(self):
        items = [{"item_code": "9.01", "text": "Exhibit 104"}]
        assert _is_boilerplate_8k(items, "") is True

    def test_real_items_not_boilerplate(self):
        items = [
            {"item_code": "2.02", "text": "Revenue was strong"},
            {"item_code": "9.01", "text": "Exhibit 99.1"},
        ]
        assert _is_boilerplate_8k(items, "") is False


class TestParse8K:
    def test_full_parse(self):
        result = parse_8k_filing(SAMPLE_8K_SGML)
        assert result["company_name"] == "APPLE INC"
        assert result["cik"] == "0000320193"
        assert result["filed_date"] == "20260315"
        assert "2.02" in result["item_codes"]
        assert result["is_boilerplate"] is False

    def test_boilerplate_detected(self):
        result = parse_8k_filing(SAMPLE_BOILERPLATE_8K)
        assert result["is_boilerplate"] is True

    def test_full_text_present(self):
        result = parse_8k_filing(SAMPLE_8K_SGML)
        assert len(result["full_text"]) > 0
        assert "Revenue" in result["full_text"] or "revenue" in result["full_text"].lower()


class TestParse10K:
    def test_parses_header(self):
        raw = """<SEC-HEADER>
COMPANY CONFORMED NAME:		APPLE INC
CENTRAL INDEX KEY:		0000320193
FILED AS OF DATE:		20260215
FORM TYPE:		10-K
</SEC-HEADER>
<html><body>
Item 1A. Risk Factors
Global supply chain disruptions could materially impact revenue.
Item 7. Management's Discussion and Analysis
Revenue increased 12% year over year driven by services growth.
Item 8. Financial Statements
</body></html>"""
        result = parse_10k_filing(raw)
        assert result["company_name"] == "APPLE INC"
        assert result["form_type"] == "10-K"


class TestItemDescriptions:
    def test_all_common_items_have_descriptions(self):
        common_items = ["1.01", "2.02", "5.02", "7.01", "8.01", "9.01"]
        for item in common_items:
            assert item in ITEM_8K_DESCRIPTIONS, f"Missing description for Item {item}"
