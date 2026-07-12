"""WebSocket gateway — real-time signal push to browser clients.

Provides a /ws endpoint that browser clients connect to for
live signal updates. Runs inside the same FastAPI process.

Authentication: the same bearer token the REST API uses, passed as a
query parameter (browsers cannot set WS handshake headers):
    wss://host/api/ws?token=<AUTH_TOKEN>
Connections without a valid token are rejected with close code 1008.

Message formats:
    Server → Client: {"type": "signal", "data": {...}}
    Server → Client: {"type": "catch_up", "data": [{...}, ...]}
    Client → Server: {"type": "ping"} → {"type": "pong"}
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.deps import validate_token
from src.gateway.broadcaster import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gateway"])

WS_POLICY_VIOLATION = 1008


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Accept an authenticated WebSocket connection and stream signals.

    The signal stream carries the same proprietary data the REST API
    gates behind bearer auth — the handshake must be gated identically.
    """
    token = ws.query_params.get("token")
    if not validate_token(token):
        # Closing before accept() rejects the handshake (403).
        await ws.close(code=WS_POLICY_VIOLATION)
        logger.info("WS connection rejected: invalid or missing token")
        return

    await ws.accept()
    await broadcaster.connect(ws)

    try:
        while True:
            data = await ws.receive_json()
            # Handle client messages (ping/pong keepalive)
            if data.get("type") == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WS connection closed: %s", e)
    finally:
        await broadcaster.disconnect(ws)
