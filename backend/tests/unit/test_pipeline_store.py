"""Tests for the pipeline store node's vector-store metadata contract.

Regression coverage for the RAG self-contamination bug: the store node used to
write the model's own predicted_move into vector metadata under "actual_move",
which evidence_builder then served back as the observed historical outcome for
future predictions.
"""

from unittest.mock import AsyncMock

import pytest

import src.rag.embedder as embedder_mod
import src.rag.vector_store as vector_store_mod
import src.storage.signal_repo as signal_repo_mod
from src.agents.pipeline import _source_to_namespace, _store_signal_node


def _approved_state() -> dict:
    return {
        "event_id": "evt_123",
        "signal_id": "sig_123",
        "raw_text": "Apple announces record quarterly earnings",
        "source": "SEC_EDGAR",
        "source_url": "https://example.com",
        "primary_ticker": "AAPL",
        "event_type": "earnings",
        "event_type_refined": "earnings",
        "sentiment_label": "positive",
        "sentiment_score": 0.8,
        "confidence": 0.72,
        "predicted_move": 0.02,
        "impact_window": "4h",
        "rationale": "Strong earnings beat.",
        "uncertainty": "Reaction depends on expectations.",
        "signal_text": "AAPL positive drift expected",
        "summary": "AAPL Q3 earnings beat",
        "timestamp": "2026-07-10T14:00:00+00:00",
        "evidence": [],
        "citations": [],
        "errors": [],
        "agent_chain": ["ingestion", "entity_resolution", "event_extraction",
                        "impact_hypothesis", "risk_gate"],
        "rejected": False,
    }


@pytest.fixture
def store_mocks(monkeypatch):
    """Mock all I/O the store node performs (DB insert, embed, upsert, WS)."""
    insert_mock = AsyncMock()
    embed_mock = AsyncMock(return_value=[0.1] * 8)
    upsert_mock = AsyncMock()
    monkeypatch.setattr(signal_repo_mod, "insert_signal", insert_mock)
    monkeypatch.setattr(embedder_mod, "embed_text", embed_mock)
    monkeypatch.setattr(vector_store_mod, "upsert_event", upsert_mock)
    return {"insert": insert_mock, "embed": embed_mock, "upsert": upsert_mock}


async def test_vector_metadata_never_contains_actual_move(store_mocks):
    """Predictions must not be stored under "actual_move" — that key is read
    by evidence_builder as the observed historical outcome."""
    await _store_signal_node(_approved_state())

    store_mocks["upsert"].assert_awaited_once()
    metadata = store_mocks["upsert"].await_args.kwargs["metadata"]
    assert "actual_move" not in metadata
    assert metadata["predicted_move"] == 0.02


async def test_vector_metadata_core_fields(store_mocks):
    await _store_signal_node(_approved_state())

    kwargs = store_mocks["upsert"].await_args.kwargs
    assert kwargs["event_id"] == "evt_123"
    assert kwargs["namespace"] == "sec_edgar"
    metadata = kwargs["metadata"]
    assert metadata["ticker"] == "AAPL"
    assert metadata["event_type"] == "earnings"
    assert metadata["source"] == "SEC_EDGAR"


async def test_db_failure_still_embeds_event(store_mocks):
    """A Postgres failure must not prevent the event becoming evidence."""
    store_mocks["insert"].side_effect = RuntimeError("db down")
    result = await _store_signal_node(_approved_state())

    store_mocks["upsert"].assert_awaited_once()
    assert any("store_signal:" in e for e in result["errors"])


def test_source_to_namespace_mapping():
    assert _source_to_namespace("SEC_EDGAR") == "sec_edgar"
    assert _source_to_namespace("GDELT") == "gdelt"
    assert _source_to_namespace("NEWSAPI") == "newsapi"
    assert _source_to_namespace("unknown") == "sec_edgar"
