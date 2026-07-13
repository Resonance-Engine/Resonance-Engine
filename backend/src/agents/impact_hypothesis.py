"""Impact Hypothesis Agent (RAG-Powered) — generates evidence-backed market hypotheses.

Agent 4 in the pipeline. Combines:
1. Vector store retrieval (semantic similarity — cross-sector analogues)
2. Market outcome data from evidence builder
3. Statistical reasoning to produce confidence scores grounded in evidence

Output: evidence[], confidence, predicted_move, rationale, uncertainty.
"""

import logging
import uuid

from src.agents.magnitude import (
    MAGNITUDE_THRESHOLD_PCT,
    MAJOR_ALERT_LINE,
    MAJOR_THRESHOLD_PCT,
    extract_item_codes,
    magnitude_probability,
    major_move_probability,
)
from src.agents.state import PipelineState

logger = logging.getLogger(__name__)

# Disclaimer appended to all rationale text
EVIDENCE_DISCLAIMER = (
    "This analysis is based on historical patterns which may not repeat. "
    "Past performance does not guarantee future results."
)


async def impact_hypothesis_agent(state: PipelineState) -> dict:
    """Agent 4: Event (typed + entities) → Signal with evidence-backed hypothesis.

    RAG Flow:
    1. Build event representation for embedding
    2. Retrieve top-K similar historical events from vector store
    3. Build evidence array from retrieval results
    4. Compute predicted move from evidence outcomes
    5. Generate rationale grounded in retrieved evidence
    6. Calibrate confidence score
    7. Determine impact window

    Reads: event_id, raw_text, event_type_refined, entities, primary_ticker,
           sentiment_label, sentiment_score, raw_confidence
    Writes: evidence, predicted_move, impact_window, confidence, rationale, uncertainty
    """
    errors = list(state.get("errors", []))
    agent_chain = list(state.get("agent_chain", []))
    agent_chain.append("impact_hypothesis")

    try:
        primary_ticker = state.get("primary_ticker", "")
        event_type = state.get("event_type_refined") or state.get("event_type", "unknown")
        sentiment_label = state.get("sentiment_label", "neutral")
        sentiment_score = state.get("sentiment_score", 0.5)
        raw_confidence = state.get("raw_confidence", 0.5)

        # 1. Try RAG retrieval
        evidence_items: list[dict] = []
        try:
            from src.models.event import Event, EventSource
            from src.rag.evidence_builder import build_evidence
            from src.rag.retriever import retrieve_similar_events_multi

            # Build a minimal Event for the retriever
            event = Event(
                event_id=state.get("event_id", str(uuid.uuid4())),
                timestamp=state.get("timestamp"),
                source=EventSource(state.get("source", "SEC_EDGAR")),
                url=state.get("source_url", ""),
                raw_text=state.get("raw_text", ""),
                content_hash=state.get("content_hash", ""),
                entities=[],
                event_type=event_type,
                summary=state.get("summary"),
                metadata={"ticker": primary_ticker},
            )

            # Search ALL namespaces for evidence — a NEWSAPI article about AMZN
            # should find similar AMZN events in sec_edgar, gdelt, etc.
            # Embeds once, merges by vector id, returns top 5 by score.
            similar = await retrieve_similar_events_multi(
                event=event,
                namespaces=["sec_edgar", "gdelt", "newsapi"],
                top_k=5,
                min_similarity=0.70,
            )

            if similar:
                evidence_objs = await build_evidence(similar, max_items=5)
                evidence_items = [e.model_dump() for e in evidence_objs]

        except Exception as e:
            logger.warning("RAG retrieval failed (expected if Pinecone/OpenAI not configured): %s", e)

        # 2. Compute predicted move from evidence
        predicted_move = _compute_predicted_move(evidence_items, sentiment_label)

        # 3. Determine impact window
        impact_window = _determine_impact_window(event_type)

        # 4. Calibrate confidence
        n_evidence = len(evidence_items)

        # For SEC 8-K filings with item codes, confidence is a MEASURED
        # probability: P(|SPY-adjusted move| >= 2%) in the first session,
        # calibrated on 1,022 real filings (see src/agents/magnitude.py).
        # Per CRUCIBLE Finding 003, this refers to magnitude only — filing
        # sentiment carries no validated directional signal.
        item_codes = list(
            state.get("filing_metadata", {}).get("item_codes") or []
        ) or extract_item_codes(state.get("raw_text", ""))
        magnitude_calibrated = (
            state.get("source", "SEC_EDGAR") == "SEC_EDGAR" and bool(item_codes)
        )

        sentiment_bonus = abs(sentiment_score) * 0.05  # 0-0.05 from sentiment strength

        major_probability: float | None = None
        if magnitude_calibrated:
            confidence = magnitude_probability(item_codes)
            sic_code = next(
                (e.get("sic_code") for e in state.get("entities", []) if e.get("sic_code")),
                None,
            )
            major_probability = round(
                major_move_probability(item_codes, sic_code=sic_code), 4
            )
        elif n_evidence >= 3:
            avg_similarity = sum(e.get("similarity_score", 0) for e in evidence_items) / n_evidence
            evidence_depth = min(n_evidence / 5, 1.0) * 0.03  # up to 0.03 for 5+ evidence
            # 5 evidence at 0.85 sim → 0.45 + 0.35*0.85 + 0.03 + ~0.01 = 0.787
            # 3 evidence at 0.70 sim → 0.45 + 0.35*0.70 + 0.02 + ~0.01 = 0.725
            confidence = min(0.45 + 0.35 * avg_similarity + evidence_depth + sentiment_bonus, 0.85)
        elif n_evidence > 0:
            avg_similarity = sum(e.get("similarity_score", 0) for e in evidence_items) / n_evidence
            # Reward high-similarity matches even with few evidence items
            # 1 evidence at 0.89 sim → 0.42 + 0.33*0.89 + ~0.01 = 0.724
            # 2 evidence at 0.80 sim → 0.42 + 0.33*0.80 + ~0.01 = 0.694
            # 1 evidence at 0.70 sim → 0.42 + 0.33*0.70 + ~0.01 = 0.661
            confidence = min(0.42 + 0.33 * avg_similarity + sentiment_bonus, 0.75)
        else:
            # No evidence: anchor at 0.42 for a typical extraction
            # (raw_confidence=0.5) scaling to the 0.55 cap, but let weak
            # extractions fall BELOW the risk gate's 0.40 rejection line.
            # The old hard floor of 0.42 made the gate's low-confidence
            # rejection unreachable from the production pipeline.
            # raw 0.5 → 0.42 | raw 1.0 → 0.55 | raw 0.3 → 0.368 (rejected)
            confidence = min(0.42 + (raw_confidence - 0.5) * 0.26, 0.55)
            confidence = max(confidence, 0.0)

        confidence = round(confidence, 4)

        # 5. Generate rationale
        rationale = _build_rationale(
            primary_ticker, event_type, sentiment_label, sentiment_score,
            predicted_move, evidence_items, n_evidence,
            magnitude_calibrated=magnitude_calibrated,
            item_codes=item_codes,
            confidence=confidence,
            major_probability=major_probability,
        )

        # 6. Generate uncertainty statement
        uncertainty = _build_uncertainty(
            event_type, n_evidence, sentiment_label,
            magnitude_calibrated=magnitude_calibrated,
        )

        return {
            "evidence": evidence_items,
            "predicted_move": predicted_move,
            "impact_window": impact_window,
            "confidence": confidence,
            "major_move_probability": major_probability,
            "rationale": rationale,
            "uncertainty": uncertainty,
            "errors": errors,
            "agent_chain": agent_chain,
        }

    except Exception as e:
        logger.exception("Impact hypothesis agent error")
        errors.append(f"impact_hypothesis_agent: {e}")
        return {"errors": errors, "agent_chain": agent_chain}


def _compute_predicted_move(evidence: list[dict], sentiment: str) -> float | None:
    """Compute predicted market move from evidence outcomes."""
    # Parse numeric moves from evidence outcomes
    moves = []
    for e in evidence:
        outcome = e.get("outcome", "")
        try:
            # Try to extract percentage from strings like "+3.2% move"
            for part in outcome.replace(",", "").split():
                part = part.strip("%").strip("+")
                if part.replace(".", "").replace("-", "").isdigit():
                    moves.append(float(part) / 100)
                    break
        except (ValueError, AttributeError):
            continue

    if moves:
        avg_move = sum(moves) / len(moves)
        # Adjust direction based on sentiment
        if sentiment == "negative" and avg_move > 0:
            avg_move = -abs(avg_move)
        elif sentiment == "positive" and avg_move < 0:
            avg_move = abs(avg_move)
        return round(avg_move, 6)

    # Fallback: sentiment-based estimate
    if sentiment == "positive":
        return 0.02
    elif sentiment == "negative":
        return -0.02
    return None


def _determine_impact_window(event_type: str) -> str:
    """Determine expected impact window based on event type."""
    long_impact = {"restructuring", "merger_acquisition", "bankruptcy", "annual_report"}
    short_impact = {"earnings", "insider_transaction", "stock_buyback", "dividend"}

    if event_type in long_impact:
        return "1w"
    if event_type in short_impact:
        return "4h"
    return "24h"


def _build_rationale(
    ticker: str, event_type: str, sentiment: str, sentiment_score: float,
    predicted_move: float | None, evidence: list[dict], n_evidence: int,
    magnitude_calibrated: bool = False,
    item_codes: list[str] | None = None,
    confidence: float = 0.0,
    major_probability: float | None = None,
) -> str:
    """Build human-readable rationale grounded in evidence."""
    parts = []

    ticker_str = ticker or "the affected company"
    event_str = (event_type or "unknown").replace("_", " ")

    parts.append(
        f"A {event_str} event was detected for {ticker_str} with "
        f"{sentiment} sentiment (score: {sentiment_score:.2f})."
    )

    if magnitude_calibrated:
        codes = ", ".join(item_codes or [])
        parts.append(
            f"8-K item codes [{codes}] imply a {confidence:.0%} probability of a "
            f"market-adjusted move of at least {MAGNITUDE_THRESHOLD_PCT:.0f}% in the "
            "first trading session, based on historical frequencies across "
            "1,000+ comparable filings."
        )
        if major_probability is not None and major_probability >= MAJOR_ALERT_LINE:
            parts.append(
                f"MAJOR IMPACT TIER: {major_probability:.0%} probability of a move of "
                f"at least {MAJOR_THRESHOLD_PCT:.0f}% — filings at this level proved "
                "major roughly half the time historically, ~3x the base rate."
            )

    if n_evidence > 0:
        parts.append(
            f"Based on {n_evidence} similar historical events retrieved from our knowledge base:"
        )
        for i, e in enumerate(evidence[:3], 1):
            summary = e.get("event_summary", "similar event")
            outcome = e.get("outcome", "outcome pending")
            sim = e.get("similarity_score", 0)
            parts.append(f"  {i}. {summary} — {outcome} (similarity: {sim:.2f})")

    if predicted_move is not None:
        direction = "+" if predicted_move >= 0 else ""
        parts.append(
            f"Predicted market impact: {direction}{predicted_move:.2%} based on "
            f"{'historical evidence' if n_evidence > 0 else 'sentiment analysis'}."
        )
    elif not magnitude_calibrated:
        # When magnitude is calibrated, the probability statement above IS the
        # impact estimate — don't contradict it.
        parts.append("Insufficient data to predict specific market impact magnitude.")

    # Note: disclaimer is appended separately by the risk gate agent
    return " ".join(parts)


def _build_uncertainty(
    event_type: str, n_evidence: int, sentiment: str,
    magnitude_calibrated: bool = False,
) -> str:
    """Build uncertainty statement highlighting known unknowns."""
    parts = []

    if magnitude_calibrated:
        parts.append(
            "Confidence refers to the probability of a material move (magnitude), "
            "not its direction — direction estimates from filing sentiment are "
            "not validated by historical evidence and should be treated as context only."
        )

    if n_evidence < 3 and not magnitude_calibrated:
        # Calibrated magnitude confidence doesn't depend on retrieved evidence,
        # so low evidence count doesn't make it "lower than reported".
        parts.append(
            f"Limited historical evidence ({n_evidence} similar events found). "
            "Confidence may be lower than reported."
        )

    if sentiment == "neutral":
        parts.append(
            "Market direction is uncertain — sentiment analysis shows mixed signals."
        )

    # Event-specific uncertainty
    uncertainty_map = {
        "earnings": "Actual market reaction depends on results vs. expectations, not absolute values.",
        "guidance": "Forward guidance impact depends on broader macroeconomic context.",
        "fda_approval": "Regulatory outcomes are binary — the move could be much larger than predicted.",
        "merger_acquisition": "Deal completion risk, regulatory approval, and terms changes could alter impact.",
        "insider_transaction": "Insider trades have many motivations beyond market outlook (tax, diversification).",
    }

    if event_type in uncertainty_map:
        parts.append(uncertainty_map[event_type])
    else:
        parts.append("Market conditions and sector sentiment may override historical patterns.")

    return " ".join(parts) if parts else "Standard model uncertainty applies to this prediction."
