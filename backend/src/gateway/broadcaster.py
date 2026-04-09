"""Broadcaster — fan-out to all connected WebSocket clients.

asyncio.Lock-protected set of WS connections.
Silent removal on send failure (disconnected clients).
Buffers last 50 signals for late-joining clients via SignalBuffer.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from src.gateway.buffer import signal_buffer

logger = logging.getLogger(__name__)


class SignalBroadcaster:
    """Manages WebSocket connections and fans out new signals."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        """Register a new client and send catch-up buffer."""
        async with self._lock:
            self._clients.add(ws)
        logger.info("WS client connected (%d total)", len(self._clients))

        # Send buffered signals so late-joiners see recent history
        recent = signal_buffer.get_recent()
        if recent:
            try:
                await ws.send_json({"type": "catch_up", "data": recent})
            except Exception:
                await self.disconnect(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove a client from the broadcast set."""
        async with self._lock:
            self._clients.discard(ws)
        logger.info("WS client disconnected (%d remaining)", len(self._clients))

    async def broadcast(self, signal_data: dict[str, Any]) -> None:
        """Push a new signal to the buffer and all connected clients."""
        signal_buffer.add(signal_data)

        message = json.dumps({"type": "signal", "data": signal_data})

        async with self._lock:
            dead: list[WebSocket] = []
            for ws in self._clients:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._clients.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._clients)


# Module-level singleton
broadcaster = SignalBroadcaster()
