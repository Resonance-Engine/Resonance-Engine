"""Broadcaster — fan-out to all connected WebSocket clients (Phase 2).

asyncio.Lock-protected set of WS connections.
Silent removal on send failure (disconnected clients).

TODO: Buffer last 50 signals for late-joining clients (cursor-based catch-up).
"""

# TODO: Phase 2 deliverable
