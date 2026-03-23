"""API connectivity test: live Alpha Vantage / Finnhub market data."""

import pytest


@pytest.mark.api
def test_alpha_vantage_connection():
    """Verify Alpha Vantage API is reachable.

    TODO: Phase 1 — requires ALPHA_VANTAGE_API_KEY
    """
    pytest.skip("Alpha Vantage API test — Phase 1 deliverable")


@pytest.mark.api
def test_finnhub_connection():
    """Verify Finnhub API is reachable.

    TODO: Phase 1 — requires FINNHUB_API_KEY
    """
    pytest.skip("Finnhub API test — Phase 1 deliverable")
