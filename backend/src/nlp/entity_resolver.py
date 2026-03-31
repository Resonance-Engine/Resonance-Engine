"""Entity resolver — maps company mentions to canonical tickers/CIKs.

Uses SEC company_tickers.json for authoritative ticker-CIK mapping,
plus fuzzy string matching for typos and abbreviations.

Data source: https://www.sec.gov/files/company_tickers.json
  (lighter than companyfacts.zip — same ticker/CIK/name data without XBRL facts)
"""

import json
import logging
import re
from difflib import get_close_matches
from pathlib import Path

import httpx

from src.config import settings
from src.models.entity import Entity

logger = logging.getLogger(__name__)

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"

# Module-level lookup tables (populated by load_company_lookup)
_name_to_entity: dict[str, Entity] = {}
_ticker_to_entity: dict[str, Entity] = {}
_cik_to_entity: dict[str, Entity] = {}
_all_names: list[str] = []
_loaded = False

# Common words that are also tickers — require context to disambiguate
_AMBIGUOUS_TICKERS = {"A", "AN", "ALL", "ARE", "AT", "BE", "BIG", "CAN", "CAR", "DO", "FOR", "HAS", "IT", "MAN", "NOW", "ONE", "OUT", "RUN", "SEE", "SO", "TWO", "WAS"}

# Patterns for extracting candidate company names from text
_COMPANY_SUFFIXES = re.compile(
    r"\b([A-Z][A-Za-z\s&\.\,]+?\s(?:Inc\.?|Corp\.?|Co\.?|Ltd\.?|LLC|LP|PLC|Group|Holdings?|Bancorp|Technologies|Therapeutics|Pharmaceuticals|Partners))\b"
)
_TICKER_IN_PARENS = re.compile(r"\(([A-Z]{1,5})\)")


def _cache_path() -> Path:
    return CACHE_DIR / "company_tickers.json"


async def _download_tickers() -> dict:
    """Download company_tickers.json from SEC."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache = _cache_path()
    if cache.exists():
        logger.info("Loading company tickers from cache: %s", cache)
        return json.loads(cache.read_text())

    logger.info("Downloading company tickers from SEC...")
    async with httpx.AsyncClient(
        headers={"User-Agent": settings.edgar_user_agent}, timeout=60.0
    ) as client:
        resp = await client.get(SEC_TICKERS_URL)
        resp.raise_for_status()
        data = resp.json()

    cache.write_text(json.dumps(data))
    logger.info("Cached %d company entries to %s", len(data), cache)
    return data


def _download_tickers_sync() -> dict:
    """Synchronous version for non-async contexts."""
    cache = _cache_path()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if cache.exists():
        return json.loads(cache.read_text())

    resp = httpx.get(
        SEC_TICKERS_URL,
        headers={"User-Agent": settings.edgar_user_agent},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    cache.write_text(json.dumps(data))
    return data


def load_company_lookup(data: dict | None = None) -> dict[str, Entity]:
    """Load SEC company tickers into lookup tables.

    Args:
        data: Pre-loaded company_tickers.json dict. If None, loads from
              cache or downloads from SEC.

    Returns:
        Dict mapping lowercase company name → Entity. Also populates
        module-level _ticker_to_entity and _cik_to_entity lookups.
    """
    global _name_to_entity, _ticker_to_entity, _cik_to_entity, _all_names, _loaded

    if _loaded and not data:
        return _name_to_entity

    if data is None:
        data = _download_tickers_sync()

    _name_to_entity = {}
    _ticker_to_entity = {}
    _cik_to_entity = {}

    for _key, entry in data.items():
        ticker = str(entry.get("ticker", "")).upper()
        cik = str(entry.get("cik_str", ""))
        name = str(entry.get("title", ""))

        if not ticker or not name:
            continue

        entity = Entity(ticker=ticker, cik=cik, name=name)
        name_lower = name.lower()

        _name_to_entity[name_lower] = entity
        _ticker_to_entity[ticker.upper()] = entity
        if cik:
            _cik_to_entity[cik] = entity

    _all_names = list(_name_to_entity.keys())
    _loaded = True
    logger.info("Loaded %d companies into entity resolver", len(_name_to_entity))
    return _name_to_entity


def resolve_by_ticker(ticker: str) -> Entity | None:
    """Exact ticker lookup."""
    if not _loaded:
        load_company_lookup()
    return _ticker_to_entity.get(ticker.upper())


def resolve_by_cik(cik: str) -> Entity | None:
    """Exact CIK lookup."""
    if not _loaded:
        load_company_lookup()
    return _cik_to_entity.get(cik.lstrip("0"))


def resolve_by_name(name: str, cutoff: float = 0.6) -> Entity | None:
    """Resolve a company name to an entity using exact + fuzzy matching.

    Args:
        name: Company name to resolve.
        cutoff: Minimum similarity for fuzzy matching (0-1).

    Returns:
        Best matching Entity or None.
    """
    if not _loaded:
        load_company_lookup()

    name_lower = name.lower().strip()

    # 1. Exact match
    if name_lower in _name_to_entity:
        return _name_to_entity[name_lower]

    # 2. Fuzzy match
    matches = get_close_matches(name_lower, _all_names, n=1, cutoff=cutoff)
    if matches:
        return _name_to_entity[matches[0]]

    return None


def resolve_entities(text: str) -> list[Entity]:
    """Extract and resolve company mentions from text to canonical entities.

    Strategy:
    1. Extract tickers in parentheses: "(AAPL)", "(MSFT)"
    2. Extract company names with corporate suffixes: "Apple Inc.", "Microsoft Corp."
    3. Resolve each candidate via exact/fuzzy lookup
    4. Deduplicate by ticker

    Args:
        text: Free text (filing content, news article, etc.)

    Returns:
        List of resolved Entity objects, deduplicated by ticker.
    """
    if not _loaded:
        load_company_lookup()

    resolved: dict[str, Entity] = {}  # ticker → Entity

    # 1. Tickers in parentheses — highest confidence
    for match in _TICKER_IN_PARENS.finditer(text):
        ticker = match.group(1)
        if ticker in _AMBIGUOUS_TICKERS:
            continue
        entity = resolve_by_ticker(ticker)
        if entity and entity.ticker not in resolved:
            resolved[entity.ticker] = entity

    # 2. Company names with corporate suffixes
    for match in _COMPANY_SUFFIXES.finditer(text):
        name = match.group(1).strip()
        entity = resolve_by_name(name, cutoff=0.7)
        if entity and entity.ticker not in resolved:
            resolved[entity.ticker] = entity

    return list(resolved.values())
