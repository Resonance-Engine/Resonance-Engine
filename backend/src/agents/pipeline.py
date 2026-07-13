"""LangGraph workflow orchestration — the 6-agent signal generation pipeline.

Pipeline: Ingestion → Entity Resolution → Event Extraction → Impact Hypothesis → Risk Gate

Each agent reads from and writes to a shared PipelineState (TypedDict).
LangGraph manages state transitions, conditional routing, and error handling.
"""

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from src.agents.entity_resolution import entity_resolution_agent
from src.agents.event_extraction import event_extraction_agent
from src.agents.impact_hypothesis import impact_hypothesis_agent
from src.agents.ingestion_agent import ingestion_agent
from src.agents.risk_gate import risk_gate_agent
from src.agents.state import PipelineState

logger = logging.getLogger(__name__)


def _should_continue_after_ingestion(state: PipelineState) -> Literal["entity_resolution", "__end__"]:
    """Route after ingestion: continue if no rejection, end if rejected."""
    if state.get("rejected"):
        return END
    return "entity_resolution"


def _should_continue_after_risk_gate(state: PipelineState) -> Literal["store_signal", "__end__"]:
    """Route after risk gate: store if approved, end if rejected."""
    if state.get("rejected"):
        return END
    return "store_signal"


async def _store_signal_node(state: PipelineState) -> dict:
    """Terminal node: persist the approved signal to PostgreSQL and vector store.

    This node runs after risk gate approval. It:
    1. Builds a Signal Pydantic model from state
    2. Inserts into signals table via signal_repo
    3. Embeds and upserts to vector store for future retrieval
    """
    errors = list(state.get("errors", []))
    agent_chain = list(state.get("agent_chain", []))
    agent_chain.append("store_signal")

    # Persist to PostgreSQL
    try:
        from datetime import datetime, timezone

        from src.models.signal import Citation, Signal, SignalType
        from src.storage.signal_repo import insert_signal

        # Map event type to signal type
        sentiment = state.get("sentiment_label", "neutral")
        predicted_move = state.get("predicted_move")

        if predicted_move is not None and predicted_move > 0:
            signal_type = SignalType.POSITIVE_DRIFT
        elif predicted_move is not None and predicted_move < 0:
            signal_type = SignalType.NEGATIVE_DRIFT
        else:
            signal_type = SignalType.WATCH

        # Build citations from state
        citations = [Citation(**c) for c in state.get("citations", [])]

        # Build evidence items from state
        from src.models.evidence import EvidenceItem
        evidence = [EvidenceItem(**e) for e in state.get("evidence", [])]

        signal = Signal(
            signal_id=state.get("signal_id", ""),
            event_id=state.get("event_id", ""),
            timestamp=datetime.now(timezone.utc),
            ticker=state.get("primary_ticker", "UNKNOWN"),
            signal_type=signal_type,
            signal_text=state.get("signal_text", ""),
            confidence=state.get("confidence", 0.5),
            rationale=state.get("rationale", ""),
            uncertainty=state.get("uncertainty", ""),
            impact_window=state.get("impact_window", "24h"),
            predicted_move=predicted_move,
            evidence=evidence,
            citations=citations,
            metadata={
                "agent_chain": agent_chain,
                "sentiment_label": sentiment,
                "sentiment_score": state.get("sentiment_score"),
                "lm_scores": state.get("lm_scores"),
                "evidence_count": len(evidence),
                "major_move_probability": state.get("major_move_probability"),
                "disclaimer": state.get("disclaimer", ""),
            },
        )

        await insert_signal(signal)
        logger.info("Stored signal %s for %s", signal.signal_id, signal.ticker)

        # Broadcast to WebSocket clients
        try:
            from src.gateway.signal_subscriber import notify_new_signal
            await notify_new_signal(signal.model_dump(mode="json"))
        except Exception as ws_err:
            logger.debug("WS broadcast skipped: %s", ws_err)

    except Exception as e:
        logger.warning("Failed to persist signal to DB (expected without PostgreSQL): %s", e)
        errors.append(f"store_signal: {e}")

    # Embed event to vector store for future retrieval
    try:
        from src.rag.embedder import embed_text, prepare_event_text
        from src.rag.vector_store import upsert_event

        event_text = prepare_event_text({
            "event_type": state.get("event_type_refined") or state.get("event_type"),
            "ticker": state.get("primary_ticker"),
            "summary": state.get("summary"),
            "raw_text": state.get("raw_text", "")[:2000],
        })

        if event_text:
            embedding = await embed_text(event_text)
            await upsert_event(
                event_id=state.get("event_id", ""),
                embedding=embedding,
                metadata={
                    "ticker": state.get("primary_ticker", ""),
                    "event_type": state.get("event_type_refined") or state.get("event_type", ""),
                    "timestamp": state.get("timestamp", ""),
                    "summary": state.get("summary", "")[:500],
                    "source": state.get("source", ""),
                    # NOTE: deliberately NOT stored as "actual_move" — that key is
                    # read by evidence_builder as the observed historical outcome.
                    # Real outcomes live in Postgres (signals.actual_move, written
                    # by the feedback loop) and are found via the signal-repo
                    # fallback in evidence_builder._get_outcome.
                    "predicted_move": state.get("predicted_move"),
                },
                namespace=_source_to_namespace(state.get("source", "")),
            )

    except Exception as e:
        logger.warning("Failed to embed to vector store (expected without OpenAI/Pinecone): %s", e)
        errors.append(f"store_signal_embed: {e}")

    return {"errors": errors, "agent_chain": agent_chain}


def _source_to_namespace(source: str) -> str:
    """Map event source to vector store namespace."""
    mapping = {
        "SEC_EDGAR": "sec_edgar",
        "GDELT": "gdelt",
        "NEWSAPI": "newsapi",
    }
    return mapping.get(source, "sec_edgar")


def build_pipeline() -> StateGraph:
    """Build and return the LangGraph agent pipeline.

    Graph structure:
        ingestion → [continue?] → entity_resolution → event_extraction
        → impact_hypothesis → risk_gate → [approved?] → store_signal → END

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("ingestion", ingestion_agent)
    workflow.add_node("entity_resolution", entity_resolution_agent)
    workflow.add_node("event_extraction", event_extraction_agent)
    workflow.add_node("impact_hypothesis", impact_hypothesis_agent)
    workflow.add_node("risk_gate", risk_gate_agent)
    workflow.add_node("store_signal", _store_signal_node)

    # Set entry point
    workflow.set_entry_point("ingestion")

    # Wire edges
    workflow.add_conditional_edges(
        "ingestion",
        _should_continue_after_ingestion,
    )
    workflow.add_edge("entity_resolution", "event_extraction")
    workflow.add_edge("event_extraction", "impact_hypothesis")
    workflow.add_edge("impact_hypothesis", "risk_gate")
    workflow.add_conditional_edges(
        "risk_gate",
        _should_continue_after_risk_gate,
    )
    workflow.add_edge("store_signal", END)

    return workflow.compile()


async def run_pipeline(raw_event: dict) -> dict:
    """Run an event through the full agent pipeline.

    Args:
        raw_event: Dict with keys:
            - raw_text: str (required)
            - source_url: str
            - source: str ("SEC_EDGAR", "GDELT", "NEWSAPI")
            - form_type: str ("8-K", "10-K", "4")
            - filing_metadata: dict

    Returns:
        Final pipeline state dict with signal data or rejection.
    """
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "raw_text": raw_event.get("raw_text", ""),
        "source_url": raw_event.get("source_url", ""),
        "source": raw_event.get("source", "SEC_EDGAR"),
        "form_type": raw_event.get("form_type", "8-K"),
        "filing_metadata": raw_event.get("filing_metadata", {}),
        "errors": [],
        "agent_chain": [],
        "rejected": False,
    }

    result = await pipeline.ainvoke(initial_state)
    logger.info(
        "Pipeline complete: signal_id=%s, rejected=%s, agents=%s",
        result.get("signal_id"),
        result.get("rejected"),
        result.get("agent_chain"),
    )
    return result
