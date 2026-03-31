"""SEC EDGAR filing parser — extracts structured data from raw filings.

Handles 8-K, 10-K, 10-Q, and Form 4 filing formats (XML/SGML/HTML).
"""

import logging
import re
from html import unescape

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 8-K item code descriptions
ITEM_8K_DESCRIPTIONS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "1.04": "Mine Safety",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate or Increase a Direct Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Transfer",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Election of Directors or Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.04": "Temporary Suspension of Trading Under Employee Benefit Plans",
    "5.05": "Amendments to Code of Ethics",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "5.08": "Shareholder Nominations",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}

# Patterns that signal boilerplate / low-information filings
_BOILERPLATE_PATTERNS = [
    re.compile(r"(?i)this\s+form\s+8-k\s+is\s+being\s+filed\s+solely\s+to\s+satisfy"),
    re.compile(r"(?i)pursuant\s+to\s+(?:item\s+)?9\.01.*?exhibits?\s+only"),
]


def _extract_sgml_header(raw_text: str) -> dict:
    """Extract metadata from the SGML header of a filing."""
    header = {}

    patterns = {
        "company_name": r"COMPANY CONFORMED NAME:\s*(.+)",
        "cik": r"CENTRAL INDEX KEY:\s*(\d+)",
        "sic": r"STANDARD INDUSTRIAL CLASSIFICATION:\s*(.+?)(?:\s*\[|$)",
        "sic_code": r"\[(\d+)\]",
        "filed_date": r"FILED AS OF DATE:\s*(\d+)",
        "accession_number": r"ACCESSION NUMBER:\s*([\d\-]+)",
        "form_type": r"FORM TYPE:\s*(.+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text[:5000])
        if match:
            header[key] = match.group(1).strip()

    return header


def _extract_items_from_8k(text: str) -> list[dict]:
    """Extract 8-K item numbers and their associated text content."""
    items = []

    # Match "Item X.XX" patterns in the filing body
    item_pattern = re.compile(
        r"(?:ITEM|Item)\s+(\d+\.\d+)\s*[:\.\-—–]?\s*(.*?)(?=(?:ITEM|Item)\s+\d+\.\d+|SIGNATURE|$)",
        re.DOTALL,
    )

    for match in item_pattern.finditer(text):
        item_code = match.group(1)
        item_text = match.group(2).strip()

        # Clean up the item text
        item_text = re.sub(r"\s+", " ", item_text)
        item_text = item_text[:5000]  # Cap per-item text to prevent massive payloads

        items.append({
            "item_code": item_code,
            "item_description": ITEM_8K_DESCRIPTIONS.get(item_code, "Unknown"),
            "text": item_text,
        })

    return items


def _html_to_text(html: str) -> str:
    """Convert HTML/SGML to plain text, preserving paragraph structure."""
    soup = BeautifulSoup(html, "lxml")

    # Remove script and style elements
    for tag in soup(["script", "style", "head"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Collapse whitespace but keep paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return unescape(text.strip())


def _is_boilerplate_8k(items: list[dict], full_text: str) -> bool:
    """Heuristic: is this 8-K just a boilerplate exhibits-only filing?"""
    # If the only item is 9.01 (Exhibits), it's likely boilerplate
    if len(items) == 1 and items[0]["item_code"] == "9.01":
        return True

    for pattern in _BOILERPLATE_PATTERNS:
        if pattern.search(full_text[:3000]):
            return True

    return False


def parse_8k_filing(raw_text: str) -> dict:
    """Parse an 8-K current report filing.

    Args:
        raw_text: Raw filing text as fetched from EDGAR (SGML/HTML/XML).

    Returns:
        Dict with keys: company_name, cik, filed_date, form_type, accession_number,
        items (list of {item_code, item_description, text}), full_text, is_boilerplate.
    """
    header = _extract_sgml_header(raw_text)
    plain_text = _html_to_text(raw_text)
    items = _extract_items_from_8k(plain_text)

    return {
        "company_name": header.get("company_name", ""),
        "cik": header.get("cik", ""),
        "sic_code": header.get("sic_code", ""),
        "filed_date": header.get("filed_date", ""),
        "form_type": header.get("form_type", "8-K"),
        "accession_number": header.get("accession_number", ""),
        "items": items,
        "item_codes": [item["item_code"] for item in items],
        "full_text": plain_text[:50000],  # Cap total text size
        "is_boilerplate": _is_boilerplate_8k(items, plain_text),
    }


def parse_10k_filing(raw_text: str) -> dict:
    """Parse a 10-K annual report filing.

    Extracts risk factors, MD&A, and key sections.

    Args:
        raw_text: Raw filing text.

    Returns:
        Dict with keys: company_name, cik, filed_date, sections, full_text.
    """
    header = _extract_sgml_header(raw_text)
    plain_text = _html_to_text(raw_text)

    sections = {}
    section_patterns = {
        "risk_factors": re.compile(
            r"(?:ITEM|Item)\s+1A[\.\s]*[:\-—–]?\s*Risk\s+Factors\s*(.*?)(?=(?:ITEM|Item)\s+\d+[A-Z]?[\.\s])",
            re.DOTALL | re.IGNORECASE,
        ),
        "mda": re.compile(
            r"(?:ITEM|Item)\s+7[\.\s]*[:\-—–]?\s*Management'?s?\s+Discussion\s*(.*?)(?=(?:ITEM|Item)\s+\d+[A-Z]?[\.\s])",
            re.DOTALL | re.IGNORECASE,
        ),
        "business": re.compile(
            r"(?:ITEM|Item)\s+1[\.\s]*[:\-—–]?\s*Business\s*(.*?)(?=(?:ITEM|Item)\s+\d+[A-Z]?[\.\s])",
            re.DOTALL | re.IGNORECASE,
        ),
    }

    for section_name, pattern in section_patterns.items():
        match = pattern.search(plain_text)
        if match:
            text = re.sub(r"\s+", " ", match.group(1).strip())
            sections[section_name] = text[:30000]

    return {
        "company_name": header.get("company_name", ""),
        "cik": header.get("cik", ""),
        "sic_code": header.get("sic_code", ""),
        "filed_date": header.get("filed_date", ""),
        "form_type": header.get("form_type", "10-K"),
        "accession_number": header.get("accession_number", ""),
        "sections": sections,
        "full_text": plain_text[:50000],
    }


def parse_form4(raw_text: str) -> dict:
    """Parse a Form 4 insider transaction filing (XML format).

    Args:
        raw_text: Raw Form 4 XML.

    Returns:
        Dict with insider name, title, transactions.
    """
    soup = BeautifulSoup(raw_text, "lxml-xml")

    issuer = soup.find("issuer")
    owner = soup.find("reportingOwner")

    transactions = []
    for txn in soup.find_all("nonDerivativeTransaction"):
        shares_el = txn.find("transactionShares")
        price_el = txn.find("transactionPricePerShare")
        code_el = txn.find("transactionCode")

        transactions.append({
            "security_title": txn.findtext("securityTitle value", "").strip(),
            "transaction_date": txn.findtext("transactionDate value", "").strip(),
            "transaction_code": code_el.findtext("value", "").strip() if code_el else "",
            "shares": shares_el.findtext("value", "0").strip() if shares_el else "0",
            "price_per_share": price_el.findtext("value", "0").strip() if price_el else "0",
            "acquired_disposed": txn.findtext("transactionAcquiredDisposedCode value", "").strip(),
        })

    return {
        "issuer_cik": issuer.findtext("issuerCik", "").strip() if issuer else "",
        "issuer_name": issuer.findtext("issuerName", "").strip() if issuer else "",
        "issuer_ticker": issuer.findtext("issuerTradingSymbol", "").strip() if issuer else "",
        "owner_name": owner.findtext("reportingOwnerId rptOwnerName", "").strip() if owner else "",
        "owner_title": owner.findtext("reportingOwnerRelationship officerTitle", "").strip() if owner else "",
        "is_director": bool(owner and owner.findtext("reportingOwnerRelationship isDirector", "").strip() == "1"),
        "is_officer": bool(owner and owner.findtext("reportingOwnerRelationship isOfficer", "").strip() == "1"),
        "transactions": transactions,
    }
