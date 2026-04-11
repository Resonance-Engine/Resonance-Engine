"""Impact Hypothesis Agent (RAG-Powered) — generates evidence-backed market hypotheses.

Agent 4 in the pipeline. Combines:
1. Vector store retrieval (semantic similarity — cross-sector analogues)
2. Market outcome data from evidence builder
3. Statistical reasoning to produce confidence scores grounded in evidence

Output: evidence[], confidence, predicted_move, rationale, uncertainty.
"""

import logging
import uuid

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
            from src.rag.retriever import retrieve_similar_events

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
            all_namespaces = ["sec_edgar", "gdelt", "newsapi"]
            similar: list[dict] = []
            seen_ids: set[str] = set()

            for ns in all_namespaces:
                try:
                    ns_results = await retrieve_similar_events(
                        event=event,
                        top_k=5,
                        min_similarity=0.70,
                        namespace=ns,
                    )
                    for r in ns_results:
                        eid = r.get("event_id", "")
                        if eid not in seen_ids:
                            seen_ids.add(eid)
                            similar.append(r)
                except Exception:
                    continue  # namespace may not exist yet

            # Keep top 5 by similarity
            similar.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            similar = similar[:5]

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
        # Evidence quality is the primary driver. Sentiment adds a small bonus.
        # Target ranges: 0 evidence → 42-50%, 1-2 → 58-75%, 3+ → 68-85%
        n_evidence = len(evidence_items)
        sentiment_bonus = abs(sentiment_score) * 0.05  # 0-0.05 from sentiment strength

        if n_evidence >= 3:
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
            confidence = max(min(raw_confidence * 0.6, 0.55), 0.42)

        confidence = round(confidence, 4)

        # 5. Generate rationale
        rationale = _build_rationale(
            primary_ticker, event_type, sentiment_label, sentiment_score,
            predicted_move, evidence_items, n_evidence,
        )

        # 6. Generate uncertainty statement
        uncertainty = _build_uncertainty(
            event_type, n_evidence, sentiment_label,
        )

        return {
            "evidence": evidence_items,
            "predicted_move": predicted_move,
            "impact_window": impact_window,
            "confidence": confidence,
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
) -> str:
    """Build human-readable rationale grounded in evidence."""
    parts = []

    ticker_str = ticker or "the affected company"
    event_str = (event_type or "unknown").replace("_", " ")

    parts.append(
        f"A {event_str} event was detected for {ticker_str} with "
        f"{sentiment} sentiment (score: {sentiment_score:.2f})."
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
    else:
        parts.append("Insufficient data to predict specific market impact magnitude.")

    # Note: disclaimer is appended separately by the risk gate agent
    return " ".join(parts)


def _build_uncertainty(event_type: str, n_evidence: int, sentiment: str) -> str:
    """Build uncertainty statement highlighting known unknowns."""
    parts = []

    if n_evidence < 3:
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
