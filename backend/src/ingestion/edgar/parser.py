"""SEC EDGAR filing parser — extracts structured data from raw filings.

Handles 8-K, 10-K, 10-Q, and Form 4 filing formats (XML/SGML/HTML).
"""


def parse_8k_filing(raw_text: str) -> dict:
    """Parse an 8-K current report filing.

    Extracts: company name, CIK, filing date, item codes, exhibit text.

    TODO: Implement XML/SGML parsing with lxml
    TODO: Extract item codes (e.g., Item 2.02 = Results of Operations)
    TODO: Handle multiple items per filing
    """
    raise NotImplementedError("8-K parser — Phase 0 deliverable")


def parse_10k_filing(raw_text: str) -> dict:
    """Parse a 10-K annual report filing.

    TODO: Extract risk factors, MD&A, financial highlights
    TODO: Support text-diff against prior year for change gating
    """
    raise NotImplementedError("10-K parser — Phase 0 deliverable")


def parse_form4(raw_text: str) -> dict:
    """Parse a Form 4 insider transaction filing.

    TODO: Extract insider name, title, transaction type, shares, price
    """
    raise NotImplementedError("Form 4 parser — Phase 1 deliverable")
