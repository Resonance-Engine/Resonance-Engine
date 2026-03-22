"""Evidence builder — converts retrieved vector matches into EvidenceItem objects.

Enriches raw retrieval results with actual market outcomes from PostgreSQL.
"""

from src.models.evidence import EvidenceItem


async def build_evidence(
    retrieval_results: list[dict],
    max_items: int = 5,
) -> list[EvidenceItem]:
    """Convert raw vector store matches into structured EvidenceItem objects.

    Flow:
    1. For each match, look up the full event in PostgreSQL
    2. Look up actual market outcome (if available)
    3. Compute time_delta (human-readable)
    4. Build EvidenceItem with all fields populated
    5. Return top max_items sorted by similarity_score

    TODO: Phase 1 deliverable
    - Wire up event_repo for full event lookup
    - Wire up signal_repo for actual_move outcome data
    - Format time_delta as human-readable string
    """
    raise NotImplementedError("Evidence builder — Phase 1 deliverable")
