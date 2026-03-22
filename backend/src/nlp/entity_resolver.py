"""Entity resolver — maps company mentions to canonical tickers/CIKs.

Uses SEC companyfacts.zip for authoritative ticker → CIK mapping,
plus fuzzy string matching for typos and abbreviations.
"""

from src.models.entity import Entity


def load_company_lookup() -> dict:
    """Load SEC companyfacts.zip into a lookup table.

    Returns: {company_name_lower: Entity, ticker_lower: Entity, ...}

    TODO: Phase 0 deliverable
    - Download companyfacts.zip from SEC
    - Parse into company name → (ticker, CIK, name, SIC) mapping
    - Build reverse lookup (ticker → entity, name → entity)
    - Cache after first load
    """
    raise NotImplementedError("Company lookup loader — Phase 0 deliverable")


def resolve_entities(text: str) -> list[Entity]:
    """Extract and resolve company mentions from text to canonical entities.

    Flow:
    1. Extract candidate company names (NER or pattern matching)
    2. Exact match against SEC lookup
    3. Fuzzy match for near-misses (Levenshtein distance ≤ 2)
    4. Disambiguate ("Apple" → AAPL vs APLE, using context)
    5. Return list of resolved Entity objects

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("Entity resolution — Phase 0 deliverable")
