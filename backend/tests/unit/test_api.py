"""Tests for the FastAPI REST API layer.

Tests that require a database connection are marked with skip_no_db.
Auth and route registration tests work without a database.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import app


@pytest.fixture
def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


AUTH_HEADERS = {"Authorization": "Bearer resonance-dev-token-2026"}


# ── Auth ───────────────────────────────────────────────────────

class TestAuth:
    async def test_login_valid_credentials(self, client):
        resp = await client.post("/api/auth/login", json={
            "username": "operator",
            "password": "resonance2026",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["operator"] == "operator"

    async def test_login_fairoz(self, client):
        resp = await client.post("/api/auth/login", json={
            "username": "fairoz",
            "password": "alpha",
        })
        assert resp.status_code == 200
        assert resp.json()["operator"] == "fairoz"

    async def test_login_invalid_credentials(self, client):
        resp = await client.post("/api/auth/login", json={
            "username": "hacker",
            "password": "wrong",
        })
        assert resp.status_code == 401

    async def test_login_missing_fields(self, client):
        resp = await client.post("/api/auth/login", json={})
        assert resp.status_code == 422

    async def test_me_with_token(self, client):
        resp = await client.get("/api/auth/me", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["operator"] == "operator"
        assert resp.json()["role"] == "analyst"

    async def test_me_without_token(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client):
        resp = await client.get("/api/auth/me", headers={
            "Authorization": "Bearer bad-token",
        })
        assert resp.status_code == 401


# ── Auth Guards on Protected Endpoints ─────────────────────────

class TestAuthGuards:
    async def test_signals_requires_auth(self, client):
        resp = await client.get("/api/signals")
        assert resp.status_code == 401

    async def test_events_requires_auth(self, client):
        resp = await client.get("/api/events")
        assert resp.status_code == 401

    async def test_entities_requires_auth(self, client):
        resp = await client.get("/api/entities")
        assert resp.status_code == 401

    async def test_pipeline_requires_auth(self, client):
        resp = await client.post("/api/pipeline/run", json={"raw_text": "test"})
        assert resp.status_code == 401


# ── Route Registration ─────────────────────────────────────────

class TestRoutes:
    def test_all_expected_routes_registered(self):
        routes = {r.path for r in app.routes}
        expected = {
            "/api/health",
            "/api/auth/login",
            "/api/auth/me",
            "/api/signals",
            "/api/signals/{signal_id}",
            "/api/events",
            "/api/events/{event_id}",
            "/api/entities",
            "/api/entities/{ticker}",
            "/api/pipeline/run",
        }
        assert expected.issubset(routes), f"Missing routes: {expected - routes}"

    def test_app_metadata(self):
        assert app.title == "Resonance Engine API"
        assert app.version == "4.0.1"
