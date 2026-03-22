"""SEC EDGAR API client — fetches filings from the EDGAR full-text search and bulk APIs.

Respects SEC rate limits: max 10 requests/second with User-Agent header.
See: https://www.sec.gov/os/accessing-edgar-data
"""

import httpx

from src.config import settings

EDGAR_FULL_TEXT_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FILINGS_URL = "https://data.sec.gov/submissions"
EDGAR_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts"

# SEC requires a User-Agent with contact info
HEADERS = {"User-Agent": settings.edgar_user_agent}


async def fetch_recent_filings(
    form_type: str = "8-K",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Fetch recent SEC filings by form type.

    TODO: Implement EDGAR full-text search API integration
    TODO: Parse response into list of filing metadata dicts
    TODO: Handle pagination for large result sets
    """
    raise NotImplementedError("EDGAR filing fetch — Phase 0 deliverable")


async def fetch_filing_document(accession_number: str, cik: str) -> str:
    """Fetch the full text of a specific filing by accession number.

    TODO: Construct URL from CIK + accession number
    TODO: Fetch and return raw filing text (HTML/XML/SGML)
    """
    raise NotImplementedError("EDGAR document fetch — Phase 0 deliverable")


async def fetch_company_facts(cik: str) -> dict:
    """Fetch company facts (ticker, name, SIC code) from EDGAR.

    TODO: Query companyfacts API
    TODO: Return structured company metadata
    """
    raise NotImplementedError("EDGAR company facts — Phase 0 deliverable")
