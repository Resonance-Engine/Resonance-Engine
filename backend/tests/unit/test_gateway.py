"""Tests for the WebSocket gateway — handshake auth and broadcaster fan-out.

First coverage for src/gateway/. Regression tests for:
1. Unauthenticated /ws handshake (previously accepted anyone and immediately
   served the catch-up buffer of recent signals).
2. Broadcast head-of-line blocking (lock was held across every client send).
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.api.app import app
from src.config import settings
from src.gateway.broadcaster import SignalBroadcaster


# ── WS handshake auth ──────────────────────────────────────────


@pytest.fixture
def http_client():
    return TestClient(app)


class TestWebSocketAuth:
    def test_missing_token_rejected(self, http_client):
        with pytest.raises(WebSocketDisconnect):
            with http_client.websocket_connect("/api/ws"):
                pass

    def test_invalid_token_rejected(self, http_client):
        with pytest.raises(WebSocketDisconnect):
            with http_client.websocket_connect("/api/ws?token=wrong-token"):
                pass

    def test_valid_token_accepted_and_ping_pong(self, http_client):
        with http_client.websocket_connect(
            f"/api/ws?token={settings.auth_token}"
        ) as ws:
            ws.send_json({"type": "ping"})
            assert ws.receive_json() == {"type": "pong"}


# ── Broadcaster ────────────────────────────────────────────────


class FakeWS:
    """Minimal WebSocket stand-in recording sent messages."""

    def __init__(self, fail: bool = False, delay: float = 0.0) -> None:
        self.fail = fail
        self.delay = delay
        self.sent: list[str] = []

    async def send_text(self, message: str) -> None:
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise RuntimeError("client gone")
        self.sent.append(message)

    async def send_json(self, data: dict) -> None:
        if self.fail:
            raise RuntimeError("client gone")
        self.sent.append(str(data))


@pytest.fixture(autouse=True)
def fresh_buffer(monkeypatch):
    """Isolate the module-level signal buffer so catch-up messages from one
    test don't leak into another's sent-message counts."""
    # NOTE: `import src.gateway.broadcaster as m` resolves the package
    # attribute `broadcaster` (the singleton) instead of the submodule,
    # because src/gateway/__init__.py re-exports it. Go via sys.modules.
    import sys

    from src.gateway.buffer import SignalBuffer

    broadcaster_mod = sys.modules["src.gateway.broadcaster"]
    buffer = SignalBuffer()
    monkeypatch.setattr(broadcaster_mod, "signal_buffer", buffer)
    return buffer


class TestBroadcaster:
    async def test_broadcast_reaches_all_clients(self):
        b = SignalBroadcaster()
        ws1, ws2 = FakeWS(), FakeWS()
        await b.connect(ws1)
        await b.connect(ws2)

        await b.broadcast({"ticker": "AAPL"})

        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1
        assert "AAPL" in ws1.sent[0]

    async def test_dead_client_removed_others_still_served(self):
        b = SignalBroadcaster()
        dead, alive = FakeWS(fail=True), FakeWS()
        await b.connect(dead)
        await b.connect(alive)

        await b.broadcast({"ticker": "MSFT"})

        assert len(alive.sent) == 1
        assert b.client_count == 1

    async def test_slow_client_does_not_block_others(self):
        """Regression: one stalled client must not stall the whole fan-out."""
        b = SignalBroadcaster()
        b.SEND_TIMEOUT = 0.2
        stuck = FakeWS(delay=10.0)  # far beyond timeout
        fast = FakeWS()
        await b.connect(stuck)
        await b.connect(fast)

        await asyncio.wait_for(b.broadcast({"ticker": "NVDA"}), timeout=2.0)

        assert len(fast.sent) == 1
        # stuck client timed out → treated as dead and removed
        assert b.client_count == 1

    async def test_broadcast_with_no_clients_is_noop(self):
        b = SignalBroadcaster()
        await b.broadcast({"ticker": "TSLA"})  # must not raise

    async def test_disconnect_removes_client(self):
        b = SignalBroadcaster()
        ws = FakeWS()
        await b.connect(ws)
        assert b.client_count == 1
        await b.disconnect(ws)
        assert b.client_count == 0
