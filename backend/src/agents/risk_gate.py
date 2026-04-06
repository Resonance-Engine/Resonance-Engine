"""Risk/Policy Gate Agent — enforces compliance rules on every signal.

Agent 5 in the pipeline. Every signal must pass these checks or get rejected:
1. No investment advice language ("buy", "sell", "guaranteed", "you should")
2. Confidence bounds (reject < 0.4, flag > 0.95)
3. Non-empty rationale (min 50 chars) and uncertainty statement (min 20 chars)
4. Evidence present (at least warn if empty)
5. Disclaimer appended

Target: 100% block rate for non-compliant outputs.
"""

import logging
import re
import uuid

from src.agents.state import PipelineState

logger = logging.getLogger(__name__)

BLOCKED_PHRASES = [
    r"\bbuy\b", r"\bsell\b", r"\bhold\b",
    r"\bguaranteed?\b", r"\bsure thing\b", r"\bcan'?t lose\b",
    r"\byou should\b", r"\byou must\b", r"\brecommended? action\b",
]

DISCLAIMER = (
    "This is not investment advice. Signals are educational and based on "
    "historical patterns which may not repeat. Past performance does not "
    "guarantee future results. You are solely responsible for your trading decisions."
)


def contains_blocked_language(text: str) -> bool:
    """Check if text contains investment advice language."""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in BLOCKED_PHRASES)


def risk_gate_agent(state: PipelineState) -> dict:
    """Agent 5: Draft signal → Approved signal with disclaimer OR rejection.

    Checks:
    1. Blocked language in rationale and signal text
    2. Confidence bounds (reject < 0.4, cap at 0.95)
    3. Rationale quality (min length, specificity)
    4. Uncertainty statement present
    5. Evidence warning (not blocking — signals can exist without evidence)

    Reads: confidence, rationale, uncertainty, evidence, primary_ticker,
           event_type_refined, predicted_move, impact_window
    Writes: signal_id, signal_text, citations, rejected, rejection_reason, disclaimer
    """
    errors = list(state.get("errors", []))
    agent_chain = list(state.get("agent_chain", []))
    agent_chain.append("risk_gate")

    rationale = state.get("rationale", "")
    uncertainty = state.get("uncertainty", "")
    confidence = state.get("confidence", 0.5)
    evidence = state.get("evidence", [])

    # Check 1: Blocked language
    if rationale and contains_blocked_language(rationale):
        logger.warning("Risk gate REJECTED: blocked language in rationale")
        return {
            "rejected": True,
            "rejection_reason": "Rationale contains investment advice language",
            "errors": errors,
            "agent_chain": agent_chain,
        }

    # Check 2: Confidence bounds
    if confidence is not None and confidence < 0.4:
        logger.info("Risk gate REJECTED: confidence %.2f below threshold", confidence)
        return {
            "rejected": True,
            "rejection_reason": f"Confidence {confidence:.2f} below minimum threshold (0.40)",
            "errors": errors,
            "agent_chain": agent_chain,
        }

    # Cap overconfident predictions
    if confidence is not None and confidence > 0.95:
        confidence = 0.95
        errors.append("risk_gate: capped confidence from >0.95 to 0.95")

    # Check 3: Rationale quality
    if not rationale or len(rationale) < 50:
        logger.warning("Risk gate REJECTED: rationale too short (%d chars)", len(rationale or ""))
        return {
            "rejected": True,
            "rejection_reason": "Rationale is missing or too short (minimum 50 characters)",
            "errors": errors,
            "agent_chain": agent_chain,
        }

    # Check 4: Uncertainty statement
    if not uncertainty or len(uncertainty) < 20:
        logger.warning("Risk gate REJECTED: uncertainty statement missing/short")
        return {
            "rejected": True,
            "rejection_reason": "Uncertainty statement is missing or too short (minimum 20 characters)",
            "errors": errors,
            "agent_chain": agent_chain,
        }

    # Check 5: Evidence warning (non-blocking)
    if not evidence:
        errors.append("risk_gate: no evidence items — signal approved but lower confidence")

    # All checks passed — generate signal
    primary_ticker = state.get("primary_ticker", "UNKNOWN")
    event_type = state.get("event_type_refined") or state.get("event_type", "event")
    predicted_move = state.get("predicted_move")
    impact_window = state.get("impact_window", "24h")

    # Build signal text
    signal_text = _build_signal_text(
        primary_ticker, event_type, confidence, predicted_move, impact_window,
    )

    # Check signal text for blocked language too
    if contains_blocked_language(signal_text):
        logger.warning("Risk gate REJECTED: blocked language in generated signal text")
        return {
            "rejected": True,
            "rejection_reason": "Generated signal text contains investment advice language",
            "errors": errors,
            "agent_chain": agent_chain,
        }

    # Build citations
    citations = []
    event_id = state.get("event_id")
    if event_id:
        citations.append({
            "type": "event",
            "id": event_id,
            "url": state.get("source_url"),
            "description": f"Triggering {event_type} event",
        })
    if evidence:
        citations.append({
            "type": "vector_retrieval",
            "id": None,
            "url": None,
            "description": f"Top-{len(evidence)} similar historical events",
        })

    signal_id = f"sig_{uuid.uuid4().hex[:12]}"

    logger.info(
        "Risk gate APPROVED signal %s for %s (confidence=%.2f)",
        signal_id, primary_ticker, confidence,
    )

    return {
        "signal_id": signal_id,
        "signal_text": signal_text,
        "confidence": confidence,
        "citations": citations,
        "disclaimer": DISCLAIMER,
        "rejected": False,
        "rejection_reason": None,
        "errors": errors,
        "agent_chain": agent_chain,
    }


def _build_signal_text(
    ticker: str, event_type: str, confidence: float,
    predicted_move: float | None, impact_window: str,
) -> str:
    """Build the signal text — a concise, testable statement."""
    event_str = event_type.replace("_", " ")
    parts = [f"Signal for {ticker}: {event_str} detected."]

    if predicted_move is not None:
        direction = "upward" if predicted_move >= 0 else "downward"
        parts.append(
            f"Historical patterns suggest {direction} price movement "
            f"(est. {abs(predicted_move):.1%}) within {impact_window}."
        )
    else:
        parts.append(f"Monitoring for price impact within {impact_window}.")

    parts.append(f"Confidence: {confidence:.0%}.")

    return " ".join(parts)
