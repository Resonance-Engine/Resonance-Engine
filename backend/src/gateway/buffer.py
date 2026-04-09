"""Signal buffer — ring buffer for last N signals, catch-up for late-joining WS clients.

Stores recent signals in memory so new WebSocket connections can receive
a backlog without replaying from the database.
"""

from collections import deque
from typing import Any


class SignalBuffer:
    """Thread-safe ring buffer for recent signals."""

    def __init__(self, maxlen: int = 50) -> None:
        self._buf: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def add(self, signal_data: dict[str, Any]) -> None:
        """Append a signal to the buffer (oldest evicted when full)."""
        self._buf.append(signal_data)

    def get_recent(self, n: int | None = None) -> list[dict[str, Any]]:
        """Return the last *n* signals (default: all buffered)."""
        items = list(self._buf)
        if n is not None:
            return items[-n:]
        return items

    def __len__(self) -> int:
        return len(self._buf)


# Module-level singleton
signal_buffer = SignalBuffer(maxlen=50)
