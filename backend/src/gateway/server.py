"""WebSocket gateway — real-time signal push to browser clients (Phase 2).

Separate service from the REST API. Subscribes to new signals
and fans out to connected browser clients.

Pattern borrowed from AgentPredict's gateway design.
"""

# TODO: Phase 2 deliverable
# - FastAPI with /ws and /health endpoints
# - On startup: start signal_subscriber as async task
# - WS messages: {"type": "signal"|"event", "data": {...}}
