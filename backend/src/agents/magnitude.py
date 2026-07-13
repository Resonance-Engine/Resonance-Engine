"""Calibrated magnitude model — P(|market-adjusted move| >= 2%) for an 8-K.

Replaces the hand-set confidence formula for SEC 8-K events with a measured
probability. Logistic regression fit on 1,022 real 8-K filings (46 large-caps,
2024-07 → 2026-07) labeled with real SPY-adjusted next-session returns.
Held-out 2026 performance: Brier 0.210, AUC 0.727, ECE 8.5% — beats both the
item-code base-rate table (0.216 / 0.692) and an uninformed prior (0.247).

Provenance: CRUCIBLE/findings/004-calibrated-magnitude-confidence-works.md,
weights in CRUCIBLE/data/exp004_results.json, reproducible via
CRUCIBLE/experiments/exp004_calibrated_magnitude.py. Refit whenever the
labeled set grows ~20% (always time-split; report Brier/ECE vs the table).

IMPORTANT SEMANTICS (Finding 003): this probability is about MAGNITUDE — will
the filing move the stock materially — not direction. Filing-text sentiment
carries no directional signal (held-out AUC ≈ 0.5), so direction must be
presented as unvalidated context, never as the thing the confidence refers to.
"""

import math
import re

# Logistic weights from exp004 (fit 2026-07-13, train <= 2025-12-31, n=684)
_BIAS = -1.167
_ITEM_WEIGHTS = {
    "2.02": 1.7975,  # earnings results — dominates
    "7.01": 0.0992,  # Reg FD disclosure
    "8.01": -0.6371,  # other events (routine)
    "1.01": -0.079,  # material agreement
    "5.02": -0.4126,  # officer/director change (routine)
    "5.07": -0.1059,  # shareholder vote (noise)
    "9.01": 0.1998,  # exhibits attached
}
_VOL_WEIGHT = 0.3963  # per z-unit of trailing 20-session realized vol
_AFTER_HOURS_WEIGHT = 0.0167
# Train-set standardization for trailing vol (daily-return stdev over the
# 20 sessions before the event, in %)
_VOL_MEAN = 2.0636
_VOL_SD = 1.3078

# Matches "[Item 2.02]" markers produced by filing_to_event, and bare
# "Item 2.02" mentions in raw filing text.
_ITEM_CODE_RE = re.compile(r"\bitem\s+(\d\.\d\d)\b", re.IGNORECASE)

MAGNITUDE_THRESHOLD_PCT = 2.0  # the "material move" this probability refers to


def extract_item_codes(text: str) -> list[str]:
    """Pull 8-K item codes (e.g. "2.02") from event raw text.

    Fallback for events whose metadata lacks item_codes — filing_to_event
    prefixes each section with "[Item X.XX]".
    """
    seen: list[str] = []
    for code in _ITEM_CODE_RE.findall(text):
        if code not in seen:
            seen.append(code)
    return seen


def magnitude_probability(
    item_codes: list[str],
    trailing_vol: float | None = None,
    after_hours: bool = False,
) -> float:
    """Calibrated P(|SPY-adjusted move| >= 2%) over the filing's first session.

    Args:
        item_codes: 8-K item codes present on the filing (e.g. ["2.02", "9.01"]).
        trailing_vol: Stdev of the ticker's daily returns (%) over the prior
            20 sessions. None → assume train-average volatility (z = 0).
        after_hours: True if the filing was accepted at/after 16:00 ET.

    Returns:
        Probability in (0, 1).
    """
    z = _BIAS
    for code in item_codes:
        z += _ITEM_WEIGHTS.get(code, 0.0)
    vol_z = 0.0 if trailing_vol is None else (trailing_vol - _VOL_MEAN) / _VOL_SD
    z += _VOL_WEIGHT * vol_z
    if after_hours:
        z += _AFTER_HOURS_WEIGHT
    return 1.0 / (1.0 + math.exp(-z))
