"""Re-embed all existing Pinecone vectors with the active embedding backend.

Use case: after switching the embedder backend (e.g., Gemini → OpenAI), the
existing Pinecone vectors are in the old model's space and become functionally
orphaned for retrieval. This script pulls each event's stored text from
PostgreSQL, re-embeds with the now-active backend, and upserts back to Pinecone
using the same event_id — overwriting the old vectors cleanly. Idempotent.

Usage:
    # Inspect what would happen — no API calls, no Pinecone writes:
    python scripts/reembed_pinecone.py --dry-run

    # Actually run it (consumes embedding API credits):
    python scripts/reembed_pinecone.py
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Make `src` importable when invoked as `python scripts/reembed_pinecone.py`
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select

from src.agents.pipeline import _source_to_namespace
from src.rag.embedder import _get_backend, embed_batch, prepare_event_text
from src.rag.vector_store import get_stats, upsert_batch
from src.storage.database import async_session
from src.storage.models import EventModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("reembed")

EMBED_BATCH_SIZE = 100  # OpenAI's per-request input limit


def _primary_ticker(entities: list | None) -> str:
    """Extract a representative ticker from the event's entities JSONB."""
    if not entities:
        return ""
    first = entities[0]
    if isinstance(first, dict):
        return str(first.get("ticker", "") or "")
    return ""


async def reembed_all(dry_run: bool = False) -> dict:
    backend = _get_backend()
    if backend == "none":
        raise RuntimeError(
            "No embedding backend configured. Set OPENAI_API_KEY or GEMINI_API_KEY "
            "in .env, or set EMBEDDING_BACKEND explicitly."
        )

    logger.info("Active embedding backend: %s", backend)

    if not dry_run:
        try:
            stats_before = await get_stats()
            logger.info(
                "Pinecone before: %d total vectors across namespaces %s",
                stats_before.get("total_vector_count", 0),
                list(stats_before.get("namespaces", {}).keys()),
            )
        except Exception:
            logger.exception("Could not read Pinecone stats (continuing anyway)")

    async with async_session() as sess:
        result = await sess.execute(select(EventModel))
        events = result.scalars().all()

    logger.info("Found %d events in PostgreSQL", len(events))
    if not events:
        return {"events": 0, "embedded": 0, "errors": 0, "by_namespace": {}}

    # Group counts by namespace for the dry-run report
    namespace_counts: dict[str, int] = {}
    for ev in events:
        ns = _source_to_namespace(ev.source or "")
        namespace_counts[ns] = namespace_counts.get(ns, 0) + 1

    logger.info("Namespace breakdown: %s", namespace_counts)

    if dry_run:
        # Estimate token cost: ~prepare_event_text() output averages ~500 tokens
        approx_tokens = len(events) * 500
        approx_cost = approx_tokens * 0.13 / 1_000_000  # text-embedding-3-large
        logger.info(
            "DRY RUN — would embed %d events in %d API call(s), ~%d tokens, ~$%.4f",
            len(events),
            (len(events) + EMBED_BATCH_SIZE - 1) // EMBED_BATCH_SIZE,
            approx_tokens,
            approx_cost,
        )
        return {
            "events": len(events),
            "embedded": 0,
            "errors": 0,
            "by_namespace": namespace_counts,
            "dry_run": True,
        }

    stats = {
        "events": len(events),
        "embedded": 0,
        "errors": 0,
        "by_namespace": dict.fromkeys(namespace_counts, 0),
    }

    for i in range(0, len(events), EMBED_BATCH_SIZE):
        batch = events[i:i + EMBED_BATCH_SIZE]
        batch_idx = i // EMBED_BATCH_SIZE + 1
        logger.info("Embedding batch %d (%d events)…", batch_idx, len(batch))

        texts = [
            prepare_event_text({
                "event_type": ev.event_type or "",
                "ticker": _primary_ticker(ev.entities),
                "summary": ev.summary or "",
                "raw_text": ev.raw_text or "",
            })
            for ev in batch
        ]

        try:
            vectors = await embed_batch(texts)
        except Exception:
            logger.exception("Batch %d: embedding failed", batch_idx)
            stats["errors"] += len(batch)
            continue

        if len(vectors) != len(batch):
            logger.error(
                "Batch %d: embedder returned %d vectors for %d inputs — skipping",
                batch_idx, len(vectors), len(batch),
            )
            stats["errors"] += len(batch)
            continue

        # Group items by namespace before upserting
        per_namespace: dict[str, list[dict]] = {}
        for ev, vec in zip(batch, vectors):
            ns = _source_to_namespace(ev.source or "")
            metadata = {
                "event_type": ev.event_type or "",
                "ticker": _primary_ticker(ev.entities),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
                "source": ev.source or "",
                "summary": (ev.summary or "")[:500],
            }
            per_namespace.setdefault(ns, []).append({
                "id": ev.event_id,
                "values": vec,
                "metadata": metadata,
            })

        for ns, items in per_namespace.items():
            try:
                upserted = await upsert_batch(items, namespace=ns)
                stats["embedded"] += upserted
                stats["by_namespace"][ns] = stats["by_namespace"].get(ns, 0) + upserted
                logger.info("Batch %d: upserted %d → '%s'", batch_idx, upserted, ns)
            except Exception:
                logger.exception("Batch %d: upsert to '%s' failed", batch_idx, ns)
                stats["errors"] += len(items)

    try:
        stats_after = await get_stats()
        logger.info(
            "Pinecone after: %d total vectors across namespaces %s",
            stats_after.get("total_vector_count", 0),
            stats_after.get("namespaces", {}),
        )
    except Exception:
        logger.exception("Could not read Pinecone stats post-run")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-embed Pinecone vectors")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen without calling the embedding API or writing to Pinecone",
    )
    args = parser.parse_args()

    try:
        result = asyncio.run(reembed_all(dry_run=args.dry_run))
    except Exception:
        logger.exception("Re-embed run failed")
        return 1

    print()
    print("=" * 60)
    if result.get("dry_run"):
        print("DRY RUN — no API calls or writes occurred.")
    else:
        print("RE-EMBED COMPLETE")
    print(f"  Events scanned:  {result['events']}")
    print(f"  Vectors written: {result['embedded']}")
    print(f"  Errors:          {result['errors']}")
    print(f"  By namespace:    {result['by_namespace']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
