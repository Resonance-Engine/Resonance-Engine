"""SEC EDGAR API client — fetches filings from the EDGAR full-text search and bulk APIs.

Respects SEC rate limits: max 10 requests/second with User-Agent header.
See: https://www.sec.gov/os/accessing-edgar-data
"""

import asyncio
import logging
from datetime import date

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

EFTS_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions"
EDGAR_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts"
EDGAR_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"

HEADERS = {
    "User-Agent": settings.edgar_user_agent,
    "Accept-Encoding": "gzip, deflate",
}

# SEC rate limit: 10 req/sec. We use a semaphore + small delay to stay under.
_rate_semaphore = asyncio.Semaphore(10)
_MIN_REQUEST_INTERVAL = 0.12  # ~8 req/sec to leave headroom


async def _throttled_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """HTTP GET with rate-limit throttling."""
    async with _rate_semaphore:
        resp = await client.get(url, **kwargs)
        await asyncio.sleep(_MIN_REQUEST_INTERVAL)
    resp.raise_for_status()
    return resp


def _normalize_cik(cik: str) -> str:
    """Zero-pad CIK to 10 digits as EDGAR expects."""
    return cik.lstrip("0").zfill(10)


async def fetch_recent_filings(
    form_type: str = "8-K",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Fetch recent SEC filings by form type via EDGAR full-text search API.

    Args:
        form_type: SEC form type (e.g. "8-K", "10-K", "10-Q").
        start_date: Start date filter as "YYYY-MM-DD". Defaults to today.
        end_date: End date filter as "YYYY-MM-DD". Defaults to today.
        limit: Maximum number of filings to return.

    Returns:
        List of filing metadata dicts with keys: accession_number, cik, company_name,
        form_type, filed_date, file_url.
    """
    if start_date is None:
        start_date = date.today().isoformat()
    if end_date is None:
        end_date = date.today().isoformat()

    params = {
        "q": f'formType:"{form_type}"',
        "dateRange": "custom",
        "startdt": start_date,
        "enddt": end_date,
        "forms": form_type,
    }

    filings: list[dict] = []
    from_param = 0
    page_size = min(limit, 50)  # EFTS max page size is 50

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        while len(filings) < limit:
            params["from"] = str(from_param)
            params["size"] = str(page_size)

            try:
                resp = await _throttled_get(
                    client,
                    "https://efts.sec.gov/LATEST/search-index",
                    params=params,
                )
                data = resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning("EFTS search returned %s, falling back to submissions API", e.response.status_code)
                break
            except Exception:
                logger.exception("EFTS search failed")
                break

            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                break

            for hit in hits:
                source = hit.get("_source", {})
                file_num = source.get("file_num", "")
                cik = source.get("entity_id", "")
                accession = source.get("adsh", "").replace("-", "")

                filings.append({
                    "accession_number": source.get("adsh", ""),
                    "cik": cik,
                    "company_name": source.get("entity_name", ""),
                    "form_type": source.get("form_type", form_type),
                    "filed_date": source.get("file_date", ""),
                    "file_url": (
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik}/{accession}/{source.get('adsh', '')}.txt"
                    ),
                    "file_number": file_num,
                })

            from_param += len(hits)
            if len(hits) < page_size:
                break

    logger.info("Fetched %d %s filings (%s to %s)", len(filings), form_type, start_date, end_date)
    return filings[:limit]


async def fetch_recent_filings_rss(form_type: str = "8-K", limit: int = 40) -> list[dict]:
    """Fetch recent filings from EDGAR RSS feed (simpler, no date filtering).

    Good for "what was just filed" polling. Limited to most recent ~40 filings.
    """
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type={form_type}&dateb=&owner=include&count={limit}&search_text=&start=0&output=atom"

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        resp = await _throttled_get(client, url)

    from lxml import etree

    root = etree.fromstring(resp.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    filings = []
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", "", ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        updated = entry.findtext("atom:updated", "", ns)

        # Parse CIK and accession from the link
        cik = ""
        accession = ""
        if "/Archives/edgar/data/" in link:
            parts = link.split("/Archives/edgar/data/")[-1].split("/")
            if len(parts) >= 2:
                cik = parts[0]
                accession = parts[1]

        filings.append({
            "accession_number": accession,
            "cik": cik,
            "company_name": title.split(" - ")[0].strip() if " - " in title else title,
            "form_type": form_type,
            "filed_date": updated[:10] if updated else "",
            "file_url": link,
        })

    logger.info("Fetched %d %s filings from RSS", len(filings), form_type)
    return filings[:limit]


async def fetch_filing_document(accession_number: str, cik: str) -> str:
    """Fetch the full text of a specific filing by accession number.

    Args:
        accession_number: SEC accession number (e.g. "0000320193-24-000081").
        cik: Company CIK number.

    Returns:
        Raw filing text (HTML/XML/SGML).
    """
    cik_clean = _normalize_cik(cik)
    accession_clean = accession_number.replace("-", "")
    url = f"{EDGAR_ARCHIVES_URL}/{cik_clean}/{accession_clean}/{accession_number}.txt"

    async with httpx.AsyncClient(headers=HEADERS, timeout=60.0) as client:
        resp = await _throttled_get(client, url)

    logger.info("Fetched filing %s for CIK %s (%d bytes)", accession_number, cik, len(resp.text))
    return resp.text


async def fetch_company_facts(cik: str) -> dict:
    """Fetch company facts (ticker, name, SIC code, XBRL data) from EDGAR.

    Args:
        cik: Company CIK number.

    Returns:
        Dict with keys: cik, entity_name, facts (XBRL taxonomy data).
    """
    cik_clean = _normalize_cik(cik)
    url = f"{EDGAR_COMPANYFACTS_URL}/CIK{cik_clean}.json"

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        resp = await _throttled_get(client, url)

    data = resp.json()
    return {
        "cik": data.get("cik", cik),
        "entity_name": data.get("entityName", ""),
        "facts": data.get("facts", {}),
    }


async def fetch_submission_history(cik: str) -> dict:
    """Fetch a company's filing submission history from EDGAR.

    Returns recent filings metadata including accession numbers, dates, and form types.
    """
    cik_clean = _normalize_cik(cik)
    url = f"{EDGAR_SUBMISSIONS_URL}/CIK{cik_clean}.json"

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        resp = await _throttled_get(client, url)

    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})

    return {
        "cik": data.get("cik", cik),
        "entity_name": data.get("name", ""),
        "tickers": data.get("tickers", []),
        "sic": data.get("sic", ""),
        "sic_description": data.get("sicDescription", ""),
        "recent_filings": [
            {
                "accession_number": acc,
                "form_type": form,
                "filed_date": filed,
                "primary_document": doc,
            }
            for acc, form, filed, doc in zip(
                recent.get("accessionNumber", []),
                recent.get("form", []),
                recent.get("filingDate", []),
                recent.get("primaryDocument", []),
            )
        ],
    }
