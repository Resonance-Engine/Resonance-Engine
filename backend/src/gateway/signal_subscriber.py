"""Signal subscriber — listens for new signals from PostgreSQL (Phase 2).

Uses PG LISTEN/NOTIFY or polling to detect new signals.
Pushes to broadcaster for fan-out to WS clients.
"""

# TODO: Phase 2 deliverable
