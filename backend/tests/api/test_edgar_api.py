"""API connectivity test: live SEC EDGAR endpoints."""

import pytest


@pytest.mark.api
def test_edgar_full_text_search_reachable():
    """Verify EDGAR full-text search API is reachable.

    TODO: Phase 0 — verify connectivity + response format
    """
    pytest.skip("EDGAR API test — Phase 0 deliverable")


@pytest.mark.api
def test_edgar_companyfacts_reachable():
    """Verify EDGAR companyfacts API is reachable.

    TODO: Phase 0
    """
    pytest.skip("EDGAR companyfacts test — Phase 0 deliverable")
