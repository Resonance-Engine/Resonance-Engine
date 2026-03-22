"""Risk/Policy Gate Agent — enforces compliance rules on every signal.

Rules:
1. Block investment advice language ("buy", "sell", "guaranteed", "you should")
2. Enforce disclaimers on every signal
3. Validate citations (event exists, historical data query valid)
4. Validate evidence (similarity scores reasonable, outcomes present)
5. Check confidence bounds (reject <0.4, flag >0.9)
6. Require non-empty uncertainty statement

Target: 100% block rate for non-compliant outputs.
"""

import re

from src.agents.state import PipelineState

BLOCKED_PHRASES = [
    r"\bbuy\b", r"\bsell\b", r"\bhold\b",
    r"\bguaranteed?\b", r"\bsure thing\b", r"\bcan'?t lose\b",
    r"\byou should\b", r"\byou must\b", r"\brecommended? action\b",
]

DISCLAIMER = (
    "This is not investment advice. Signals are educational and based on "
    "historical patterns which may not repeat. Past performance does not "
    "guarantee future results. You are solely responsible for your trading decisions."
)


def contains_blocked_language(text: str) -> bool:
    """Check if text contains investment advice language."""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in BLOCKED_PHRASES)


async def risk_gate_agent(state: PipelineState) -> PipelineState:
    """Agent 5: Draft signal → Approved signal OR rejection.

    TODO: Phase 1 deliverable
    - Check signal_text and rationale for blocked language
    - Validate citations exist and reference valid events
    - Validate evidence[] items have proper fields
    - Check confidence bounds
    - Verify uncertainty field is non-empty and specific
    - Append disclaimer
    - Log approved/rejected with reason
    """
    raise NotImplementedError("Risk gate agent — Phase 1 deliverable")
