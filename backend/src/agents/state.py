"""Pipeline state — shared typed state passed between agents."""

from dataclasses import dataclass, field

from src.models.event import Event
from src.models.signal import Signal


@dataclass
class PipelineState:
    """Shared state object flowing through the LangGraph agent pipeline."""

    event: Event
    signal: Signal | None = None
    errors: list[str] = field(default_factory=list)
    rejected: bool = False
    rejection_reason: str | None = None
