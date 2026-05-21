"""Signal subscriber — publish new signals to the WebSocket broadcaster.

Called directly from the pipeline's store_signal node after a signal
is persisted to PostgreSQL. No polling or PG LISTEN/NOTIFY needed
since we push in-process.
"""

import logging
from typing import Any

from src.gateway.broadcaster import broadcaster

logger = logging.getLogger(__name__)


async def notify_new_signal(signal_data: dict[str, Any]) -> None:
    """Broadcast a newly stored signal to all connected WS clients.

    Args:
        signal_data: Serialized signal dict (JSON-safe).
    """
    await broadcaster.broadcast(signal_data)
    logger.info(
        "Broadcast signal %s to %d WS clients",
        signal_data.get("signal_id", "?"),
        broadcaster.client_count,
    )
