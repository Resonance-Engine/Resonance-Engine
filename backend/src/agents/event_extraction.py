"""Event Extraction Agent — assigns event type, sentiment, and summary.

Agent 3 in the pipeline. Uses FinBERT for deep sentiment classification
and Loughran-McDonald lexicon for fast keyword-based scoring.
"""

import logging

from src.agents.state import PipelineState
from src.nlp.loughran_mcdonald import score_text

logger = logging.getLogger(__name__)

# Event type classification rules based on keywords in text
EVENT_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("earnings", ["earnings", "quarterly results", "revenue", "eps", "net income"]),
    ("guidance", ["guidance", "outlook", "forecast", "expects", "anticipates"]),
    ("fda_approval", ["fda", "approval", "drug", "clinical trial", "phase"]),
    ("merger_acquisition", ["merger", "acquisition", "acquire", "takeover", "deal"]),
    ("executive_change", ["ceo", "cfo", "cto", "resignation", "appointed", "executive"]),
    ("restructuring", ["restructuring", "layoff", "cost-cutting", "workforce reduction"]),
    ("dividend", ["dividend", "distribution", "payout", "yield"]),
    ("stock_buyback", ["buyback", "repurchase", "share repurchase"]),
    ("lawsuit", ["lawsuit", "litigation", "settlement", "class action", "sued"]),
    ("bankruptcy", ["bankruptcy", "chapter 11", "chapter 7", "insolvency", "default"]),
    ("insider_transaction", ["form 4", "insider", "beneficial ownership"]),
]


async def event_extraction_agent(state: PipelineState) -> dict:
    """Agent 3: Event with entities → Event with type, sentiment, confidence.

    Reads: raw_text, event_type, summary
    Writes: sentiment_label, sentiment_score, lm_scores, event_type_refined,
            summary (enriched), raw_confidence
    """
    errors = list(state.get("errors", []))
    agent_chain = list(state.get("agent_chain", []))
    agent_chain.append("event_extraction")

    try:
        raw_text = state.get("raw_text", "")
        current_event_type = state.get("event_type")

        # 1. Loughran-McDonald lexicon scoring (fast, no GPU)
        lm_result = score_text(raw_text[:5000])
        lm_scores = {
            "positive_count": lm_result["positive_count"],
            "negative_count": lm_result["negative_count"],
            "uncertainty_count": lm_result["uncertainty_count"],
            "litigious_count": lm_result["litigious_count"],
            "constraining_count": lm_result["constraining_count"],
            "net_sentiment": lm_result["net_sentiment"],
            "total_words": lm_result["total_words"],
        }

        # 2. Derive sentiment from LM scores
        net = lm_result["net_sentiment"]
        if net > 0.02:
            sentiment_label = "positive"
        elif net < -0.02:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        sentiment_score = abs(net)

        # 3. Try FinBERT for deeper classification (if available).
        # Runs in a worker thread — a synchronous forward pass here would
        # block the event loop for every concurrent pipeline run.
        try:
            from src.nlp.finbert import classify_sentiment_async
            finbert_result = await classify_sentiment_async(raw_text[:2000])
            sentiment_label = finbert_result.label
            sentiment_score = finbert_result.score
        except Exception:
            # FinBERT not available (no torch) — LM scores are sufficient
            pass

        # 4. Refine event type using keyword rules
        event_type_refined = current_event_type
        if not event_type_refined or event_type_refined.startswith("8k_item_"):
            text_lower = raw_text.lower()
            for etype, keywords in EVENT_TYPE_RULES:
                if any(kw in text_lower for kw in keywords):
                    event_type_refined = etype
                    break

        # 5. Generate enriched summary
        summary = state.get("summary", "")
        primary_ticker = state.get("primary_ticker", "")
        if event_type_refined and primary_ticker:
            summary = (
                f"{primary_ticker}: {event_type_refined.replace('_', ' ').title()} — "
                f"Sentiment: {sentiment_label} ({sentiment_score:.2f}). "
                f"{summary[:150]}"
            )

        # 6. Initial confidence based on sentiment strength
        raw_confidence = min(0.5 + sentiment_score * 0.5, 0.95)

        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "lm_scores": lm_scores,
            "event_type_refined": event_type_refined,
            "summary": summary,
            "raw_confidence": raw_confidence,
            "errors": errors,
            "agent_chain": agent_chain,
        }

    except Exception as e:
        logger.exception("Event extraction agent error")
        errors.append(f"event_extraction_agent: {e}")
        return {"errors": errors, "agent_chain": agent_chain}
