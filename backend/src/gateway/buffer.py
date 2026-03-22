"""Signal buffer — cursor-based catch-up for late-joining WS clients (Phase 2).

Stores last N signals so new connections can catch up without
replaying everything from the database.

Pattern borrowed from AgentPredict's EventStore cursor design.
"""

# TODO: Phase 2 deliverable
