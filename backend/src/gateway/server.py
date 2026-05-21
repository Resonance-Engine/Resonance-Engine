"""WebSocket gateway — real-time signal push to browser clients.

Provides a /ws endpoint that browser clients connect to for
live signal updates. Runs inside the same FastAPI process.

Message formats:
    Server → Client: {"type": "signal", "data": {...}}
    Server → Client: {"type": "catch_up", "data": [{...}, ...]}
    Client → Server: {"type": "ping"} → {"type": "pong"}
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.gateway.broadcaster import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gateway"])


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Accept a WebSocket connection and stream signals in real-time."""
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
