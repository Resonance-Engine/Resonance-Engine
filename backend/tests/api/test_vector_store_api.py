"""API connectivity test: live Pinecone/Qdrant vector store."""

import pytest


@pytest.mark.api
def test_pinecone_connection():
    """Verify Pinecone is reachable and index exists.

    TODO: Phase 1 — requires PINECONE_API_KEY
    """
    pytest.skip("Pinecone API test — Phase 1 deliverable")
