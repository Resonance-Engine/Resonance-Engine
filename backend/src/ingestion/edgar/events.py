"""EDGAR filing → Event conversion (Celery-free).

Lives in its own module so the live async scheduler can import it without
transitively importing src.celery_app — the Celery task registry is dead
code (replaced by the async scheduler on Python 3.14), and coupling the
live EDGAR path to it meant removing Celery would silently break polling.
"""

import logging
from datetime import datetime, timezone

from src.ingestion.normalizer import normalize_event
from src.models.entity import Entity
from src.models.event import Event, EventSource
from src.nlp.entity_resolver import resolve_by_cik, resolve_entities

logger = logging.getLogger(__name__)


def filing_to_event(parsed: dict, file_url: str) -> Event:
    """Convert a parsed filing dict into a normalized Event.

    Args:
        parsed: Output of parse_8k_filing (form_type, cik, company_name,
            items, item_codes, filed_date, is_boilerplate, ...).
        file_url: URL of the source filing document.

    Returns:
        Normalized Event with resolved entities in metadata.
    """
    # Build entity from parsed filing data, resolving ticker via entity resolver
    entities = []
    cik = parsed.get("cik", "")
    company_name = parsed.get("company_name", "")

    # Try CIK-based resolution first (most reliable for SEC filings)
    if cik:
        resolved = resolve_by_cik(cik)
        if resolved:
            entities.append(Entity(
                ticker=resolved.ticker,
                cik=cik,
                name=resolved.name,
                sic_code=parsed.get("sic_code") or resolved.sic_code,
            ))

    # Fallback: resolve from filing text (catches additional mentioned entities)
    if not entities and company_name:
        text_entities = resolve_entities(company_name)
        if text_entities:
            entities.append(Entity(
                ticker=text_entities[0].ticker,
                cik=cik or text_entities[0].cik,
                name=text_entities[0].name,
                sic_code=parsed.get("sic_code") or text_entities[0].sic_code,
            ))

    # Last resort: use raw parsed data with empty ticker
    if not entities and company_name:
        entities.append(Entity(
            ticker="",
            cik=cik,
            name=company_name,
            sic_code=parsed.get("sic_code"),
        ))

    # Also extract any additional entities mentioned in the filing text
    raw_text_for_resolution = ""
    for item in parsed.get("items", []):
        raw_text_for_resolution += item.get("text", "") + " "
    if raw_text_for_resolution.strip():
        additional = resolve_entities(raw_text_for_resolution)
        existing_tickers = {e.ticker for e in entities}
        for ent in additional:
            if ent.ticker and ent.ticker not in existing_tickers:
                entities.append(ent)
                existing_tickers.add(ent.ticker)

    # Determine event type from 8-K item codes
    event_type = None
    item_codes = parsed.get("item_codes", [])
    if item_codes:
        # Map primary item code to a human-readable event type
        primary = item_codes[0]
        event_type = f"8k_item_{primary.replace('.', '_')}"

    # Parse filed date
    filed_str = parsed.get("filed_date", "")
    timestamp = None
    if filed_str and len(filed_str) == 8:
        try:
            timestamp = datetime.strptime(filed_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if filed_str and len(filed_str) == 10:
        try:
            timestamp = datetime.strptime(filed_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # Build the raw text: item texts joined, fallback to full_text
    raw_text = ""
    for item in parsed.get("items", []):
        raw_text += f"[Item {item['item_code']}] {item['text']}\n\n"
    if not raw_text:
        raw_text = parsed.get("full_text", "")[:10000]

    return normalize_event(
        source=EventSource.SEC_EDGAR,
        url=file_url,
        raw_text=raw_text,
        timestamp=timestamp,
        event_type=event_type,
        entities=entities,
        metadata={
            "form_type": parsed.get("form_type", "8-K"),
            "accession_number": parsed.get("accession_number", ""),
            "item_codes": item_codes,
            "is_boilerplate": parsed.get("is_boilerplate", False),
            "entities_raw": [e.model_dump() for e in entities],
        },
    )
