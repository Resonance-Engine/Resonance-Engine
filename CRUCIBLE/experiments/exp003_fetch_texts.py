"""exp003a — Fetch real earnings-8-K texts for the direction bet (Bet B).

For every item-2.02 event in data/real_labeled_8k_set.json, fetches the full
EDGAR submission (free, rate-limited via the repo's own throttled client),
extracts readable text from the 8-K body and press-release exhibits (EX-99.*),
and caches it as one JSON per accession under data/filing_texts/.

Cost ceiling: $0 (EDGAR is free; ~370 fetches at <6 req/s).
Capture date: 2026-07-13.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from src.ingestion.edgar.client import fetch_filing_document  # noqa: E402
from src.ingestion.edgar.parser import _html_to_text  # noqa: E402

DATA = ROOT / "CRUCIBLE" / "data"
OUT_DIR = DATA / "filing_texts"
MAX_TEXT_PER_DOC = 60_000  # chars; press releases are far smaller than this

DOC_RE = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.DOTALL | re.IGNORECASE)
TYPE_RE = re.compile(r"<TYPE>([^\n<]+)", re.IGNORECASE)


def extract_relevant_text(raw: str) -> dict[str, str]:
    """Pull readable text from the 8-K body + EX-99 exhibits of a full submission."""
    parts: dict[str, str] = {}
    for m in DOC_RE.finditer(raw):
        doc = m.group(1)
        type_m = TYPE_RE.search(doc)
        doc_type = (type_m.group(1).strip().upper() if type_m else "?")
        if not (doc_type == "8-K" or doc_type.startswith("EX-99")):
            continue
        text = _html_to_text(doc)
        text = re.sub(r"\s+", " ", text).strip()[:MAX_TEXT_PER_DOC]
        if len(text) > 200:  # skip empty/graphic exhibits
            parts[doc_type] = text
    return parts


async def fetch_one(event: dict, sem: asyncio.Semaphore) -> str:
    path = OUT_DIR / f"{event['accession']}.json"
    if path.exists():
        return "cached"
    async with sem:
        try:
            raw = await fetch_filing_document(event["accession"], str(event["cik"]))
        except Exception as exc:  # noqa: BLE001 — record and continue the sweep
            path.write_text(json.dumps({"error": str(exc)}))
            return "error"
    parts = extract_relevant_text(raw)
    path.write_text(
        json.dumps(
            {
                "accession": event["accession"],
                "ticker": event["ticker"],
                "filed": event["filed"],
                "parts": parts,
            }
        )
    )
    return "ok" if parts else "empty"


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    events = json.loads((DATA / "real_labeled_8k_set.json").read_text())["events"]
    targets = [e for e in events if "2.02" in e["items"]]
    print(f"fetching {len(targets)} item-2.02 filings")
    sem = asyncio.Semaphore(4)
    results = await asyncio.gather(*(fetch_one(e, sem) for e in targets))
    from collections import Counter

    print(dict(Counter(results)))


if __name__ == "__main__":
    asyncio.run(main())
