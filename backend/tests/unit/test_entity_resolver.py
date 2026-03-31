"""Tests for entity resolver — uses mock SEC data."""

import pytest

from src.models.entity import Entity
import src.nlp.entity_resolver as er
from src.nlp.entity_resolver import (
    load_company_lookup,
    resolve_by_cik,
    resolve_by_name,
    resolve_by_ticker,
    resolve_entities,
)

# Mock SEC company_tickers.json data
MOCK_TICKERS = {
    "0": {"cik_str": "320193", "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": "789019", "ticker": "MSFT", "title": "Microsoft Corp"},
    "2": {"cik_str": "1318605", "ticker": "TSLA", "title": "Tesla, Inc."},
    "3": {"cik_str": "1045810", "ticker": "NVDA", "title": "NVIDIA Corp"},
    "4": {"cik_str": "1511737", "ticker": "APLE", "title": "Apple Hospitality REIT Inc."},
    "5": {"cik_str": "1652044", "ticker": "GOOGL", "title": "Alphabet Inc."},
}


@pytest.fixture(autouse=True)
def _load_mock_data():
    """Load mock data before each test."""
    load_company_lookup(data=MOCK_TICKERS)


class TestLoadCompanyLookup:
    def test_loads_all_entries(self):
        assert len(er._ticker_to_entity) == 6
        assert len(er._name_to_entity) == 6

    def test_ticker_lookup_populated(self):
        assert "AAPL" in er._ticker_to_entity
        assert "MSFT" in er._ticker_to_entity

    def test_entity_has_correct_fields(self):
        entity = er._ticker_to_entity["AAPL"]
        assert entity.ticker == "AAPL"
        assert entity.cik == "320193"
        assert entity.name == "Apple Inc."


class TestResolveByTicker:
    def test_exact_match(self):
        entity = resolve_by_ticker("AAPL")
        assert entity is not None
        assert entity.name == "Apple Inc."

    def test_case_insensitive(self):
        entity = resolve_by_ticker("aapl")
        assert entity is not None
        assert entity.ticker == "AAPL"

    def test_not_found(self):
        assert resolve_by_ticker("ZZZZ") is None


class TestResolveByCik:
    def test_exact_match(self):
        entity = resolve_by_cik("320193")
        assert entity is not None
        assert entity.ticker == "AAPL"

    def test_strips_leading_zeros(self):
        entity = resolve_by_cik("0000320193")
        assert entity is not None
        assert entity.ticker == "AAPL"


class TestResolveByName:
    def test_exact_match(self):
        entity = resolve_by_name("Apple Inc.")
        assert entity is not None
        assert entity.ticker == "AAPL"

    def test_case_insensitive(self):
        entity = resolve_by_name("apple inc.")
        assert entity is not None
        assert entity.ticker == "AAPL"

    def test_fuzzy_match(self):
        entity = resolve_by_name("Apple Inc", cutoff=0.7)
        assert entity is not None
        assert entity.ticker == "AAPL"

    def test_no_match(self):
        assert resolve_by_name("Completely Unknown Corp", cutoff=0.9) is None


class TestResolveEntities:
    def test_extracts_ticker_in_parens(self):
        text = "Revenue at Apple Inc. (AAPL) grew 9% year-over-year."
        entities = resolve_entities(text)
        tickers = {e.ticker for e in entities}
        assert "AAPL" in tickers

    def test_extracts_corporate_suffix_name(self):
        text = "Microsoft Corp announced new cloud partnerships."
        entities = resolve_entities(text)
        tickers = {e.ticker for e in entities}
        assert "MSFT" in tickers

    def test_deduplicates(self):
        text = "Apple Inc. (AAPL) reported earnings. Apple Inc. beat estimates."
        entities = resolve_entities(text)
        aapl_count = sum(1 for e in entities if e.ticker == "AAPL")
        assert aapl_count == 1

    def test_multiple_entities(self):
        text = "Both Apple Inc. (AAPL) and Microsoft Corp (MSFT) reported strong earnings."
        entities = resolve_entities(text)
        tickers = {e.ticker for e in entities}
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_empty_text(self):
        entities = resolve_entities("")
        assert entities == []
