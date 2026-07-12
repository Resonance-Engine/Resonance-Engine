"""Tests for vector store retriever — single and multi-namespace retrieval.

Regression coverage for the cross-namespace merge bug where dedup keyed on
"event_id"/"similarity_score" (keys that don't exist in retrieval results)
instead of "id"/"score", silently dropping all but one evidence item.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

import src.rag.retriever as retriever_mod
from src.models.event import Event, EventSource
from src.rag.retriever import retrieve_similar_events, retrieve_similar_events_multi


def _make_event(raw_text: str = "Apple reports record Q3 earnings beat") -> Event:
    return Event(
        event_id="evt_query",
        timestamp=datetime.now(timezone.utc),
        source=EventSource.SEC_EDGAR,
        url="https://example.com/filing",
        raw_text=raw_text,
        content_hash="abc123",
        entities=[],
        event_type="earnings",
        summary="AAPL Q3 earnings",
        metadata={"ticker": "AAPL"},
    )


def _match(vec_id: str, score: float) -> dict:
    return {"id": vec_id, "score": score, "metadata": {"ticker": "AAPL"}}


@pytest.fixture
def fake_embed(monkeypatch):
    mock = AsyncMock(return_value=[0.1] * 8)
    monkeypatch.setattr(retriever_mod, "embed_text", mock)
    return mock


# --- retrieve_similar_events ---


async def test_min_similarity_filter(fake_embed, monkeypatch):
    """Results below min_similarity must be dropped."""
    monkeypatch.setattr(
        retriever_mod, "query_similar",
        AsyncMock(return_value=[_match("a", 0.95), _match("b", 0.65)]),
    )
    results = await retrieve_similar_events(_make_event(), min_similarity=0.70)
    assert [r["id"] for r in results] == ["a"]


async def test_self_match_excluded(fake_embed, monkeypatch):
    """The query event itself must not be returned as evidence."""
    monkeypatch.setattr(
        retriever_mod, "query_similar",
        AsyncMock(return_value=[_match("evt_query", 0.99), _match("other", 0.90)]),
    )
    results = await retrieve_similar_events(_make_event(), min_similarity=0.70)
    assert [r["id"] for r in results] == ["other"]


async def test_empty_store_returns_empty(fake_embed, monkeypatch):
    monkeypatch.setattr(retriever_mod, "query_similar", AsyncMock(return_value=[]))
    assert await retrieve_similar_events(_make_event()) == []


async def test_top_k_cap(fake_embed, monkeypatch):
    matches = [_match(f"m{i}", 0.95 - i * 0.01) for i in range(10)]
    monkeypatch.setattr(retriever_mod, "query_similar", AsyncMock(return_value=matches))
    results = await retrieve_similar_events(_make_event(), top_k=3, min_similarity=0.70)
    assert len(results) == 3


async def test_precomputed_embedding_skips_embed_call(fake_embed, monkeypatch):
    """Passing query_embedding must not trigger an embedding API call."""
    monkeypatch.setattr(
        retriever_mod, "query_similar", AsyncMock(return_value=[_match("a", 0.9)]),
    )
    results = await retrieve_similar_events(
        _make_event(), query_embedding=[0.5] * 8,
    )
    assert [r["id"] for r in results] == ["a"]
    fake_embed.assert_not_awaited()


async def test_namespace_passed_through(fake_embed, monkeypatch):
    query_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(retriever_mod, "query_similar", query_mock)
    await retrieve_similar_events(_make_event(), namespace="gdelt")
    assert query_mock.await_args.kwargs["namespace"] == "gdelt"


# --- retrieve_similar_events_multi (cross-namespace merge) ---


async def test_multi_embeds_exactly_once(fake_embed, monkeypatch):
    """Three namespaces must not mean three embedding API calls."""
    monkeypatch.setattr(
        retriever_mod, "query_similar", AsyncMock(return_value=[_match("a", 0.9)]),
    )
    await retrieve_similar_events_multi(
        _make_event(), namespaces=["sec_edgar", "gdelt", "newsapi"],
    )
    assert fake_embed.await_count == 1


async def test_multi_merge_keeps_distinct_ids_across_namespaces(fake_embed, monkeypatch):
    """Regression: distinct results from different namespaces must ALL survive.

    The old merge read r.get("event_id") — always "" — so every result after
    the first was treated as a duplicate and dropped.
    """
    per_namespace = {
        "sec_edgar": [_match("sec_1", 0.91)],
        "gdelt": [_match("gdelt_1", 0.88)],
        "newsapi": [_match("news_1", 0.85)],
    }

    async def fake_query(embedding, top_k, namespace=None, filter_dict=None):
        return per_namespace.get(namespace, [])

    monkeypatch.setattr(retriever_mod, "query_similar", fake_query)
    results = await retrieve_similar_events_multi(
        _make_event(), namespaces=["sec_edgar", "gdelt", "newsapi"],
    )
    assert {r["id"] for r in results} == {"sec_1", "gdelt_1", "news_1"}


async def test_multi_dedupes_same_id_across_namespaces(fake_embed, monkeypatch):
    """The same vector id appearing in two namespaces is returned once."""
    async def fake_query(embedding, top_k, namespace=None, filter_dict=None):
        return [_match("shared", 0.9)]

    monkeypatch.setattr(retriever_mod, "query_similar", fake_query)
    results = await retrieve_similar_events_multi(
        _make_event(), namespaces=["sec_edgar", "gdelt"],
    )
    assert [r["id"] for r in results] == ["shared"]


async def test_multi_sorted_by_score_descending(fake_embed, monkeypatch):
    """Regression: merged results must sort on "score", not a nonexistent key."""
    per_namespace = {
        "sec_edgar": [_match("low", 0.72), _match("high", 0.95)],
        "gdelt": [_match("mid", 0.83)],
    }

    async def fake_query(embedding, top_k, namespace=None, filter_dict=None):
        return per_namespace.get(namespace, [])

    monkeypatch.setattr(retriever_mod, "query_similar", fake_query)
    results = await retrieve_similar_events_multi(
        _make_event(), namespaces=["sec_edgar", "gdelt"],
    )
    assert [r["id"] for r in results] == ["high", "mid", "low"]


async def test_multi_caps_merged_results_at_top_k(fake_embed, monkeypatch):
    per_namespace = {
        "sec_edgar": [_match(f"s{i}", 0.90 - i * 0.01) for i in range(4)],
        "gdelt": [_match(f"g{i}", 0.89 - i * 0.01) for i in range(4)],
    }

    async def fake_query(embedding, top_k, namespace=None, filter_dict=None):
        return per_namespace.get(namespace, [])

    monkeypatch.setattr(retriever_mod, "query_similar", fake_query)
    results = await retrieve_similar_events_multi(
        _make_event(), namespaces=["sec_edgar", "gdelt"], top_k=5,
    )
    assert len(results) == 5
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


async def test_multi_namespace_failure_is_skipped(fake_embed, monkeypatch):
    """One failing namespace must not kill retrieval from the others."""
    async def fake_query(embedding, top_k, namespace=None, filter_dict=None):
        if namespace == "gdelt":
            raise RuntimeError("namespace does not exist")
        return [_match("ok", 0.9)]

    monkeypatch.setattr(retriever_mod, "query_similar", fake_query)
    results = await retrieve_similar_events_multi(
        _make_event(), namespaces=["gdelt", "sec_edgar"],
    )
    assert [r["id"] for r in results] == ["ok"]


async def test_multi_empty_event_text_returns_empty(fake_embed, monkeypatch):
    query_mock = AsyncMock(return_value=[_match("a", 0.9)])
    monkeypatch.setattr(retriever_mod, "query_similar", query_mock)
    event = _make_event(raw_text="")
    event.summary = None
    event.event_type = None
    event.metadata = {}
    results = await retrieve_similar_events_multi(event, namespaces=["sec_edgar"])
    assert results == []
    fake_embed.assert_not_awaited()
