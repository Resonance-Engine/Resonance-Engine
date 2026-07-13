"""Calibrated magnitude model — P(|market-adjusted move| >= 2%) for an 8-K.

Replaces the hand-set confidence formula for SEC 8-K events with a measured
probability. Logistic regression fit on 12,334 real S&P 500 8-K filings
(502 tickers, 2024-07 → 2026-07) labeled with real SPY-adjusted next-session
returns. Held-out 2026 performance (n=3,616): Brier 0.218, AUC 0.715,
ECE 8.1% — beats the item-code base-rate table and the v1 46-ticker fit.
v1 (exp004) was validated out-of-universe before this refit: on 11,329
events from 456 never-seen tickers it still beat the base-rate table
(exp007), so the refit is an upgrade, not a fix.

Provenance: CRUCIBLE/findings/004 (v1 model + wiring) and 007 (out-of-
universe validation + this v2 refit); weights in
CRUCIBLE/data/exp007_results.json ("refit_sp500_time_split"), reproducible
via CRUCIBLE/experiments/exp007_f004_out_of_universe.py. Refit whenever the
labeled set grows ~20% (always time-split; report Brier/ECE vs the table).

IMPORTANT SEMANTICS (Finding 003): this probability is about MAGNITUDE — will
the filing move the stock materially — not direction. Filing-text sentiment
carries no directional signal (held-out AUC ≈ 0.5), so direction must be
presented as unvalidated context, never as the thing the confidence refers to.
"""

import math
import re

# Logistic weights v2 from exp007 (fit 2026-07-13, S&P 500 universe,
# train <= 2025-12-31, n=8,718)
_BIAS = -1.2436
_ITEM_WEIGHTS = {
    "2.02": 1.8769,  # earnings results — dominates
    "7.01": 0.2398,  # Reg FD disclosure
    "8.01": -0.2518,  # other events (routine)
    "1.01": -0.1111,  # material agreement
    "5.02": -0.0598,  # officer/director change
    "5.07": -0.4124,  # shareholder vote (noise)
    "9.01": 0.0735,  # exhibits attached
}
_VOL_WEIGHT = 0.2884  # per z-unit of trailing 20-session realized vol
# after-hours acceptance added nothing at either universe scale (v1: 0.0167)
_AFTER_HOURS_WEIGHT = 0.0
# Train-set standardization for trailing vol (daily-return stdev over the
# 20 sessions before the event, in %)
_VOL_MEAN = 1.9043
_VOL_SD = 1.1465

# Matches "[Item 2.02]" markers produced by filing_to_event, and bare
# "Item 2.02" mentions in raw filing text.
_ITEM_CODE_RE = re.compile(r"\bitem\s+(\d\.\d\d)\b", re.IGNORECASE)

MAGNITUDE_THRESHOLD_PCT = 2.0  # the "material move" this probability refers to

# --- Major-move tier (Bet G / Finding 009) -------------------------------
# Second calibrated head: P(|SPY-adjusted move| >= 5%). Logistic over item
# codes + trailing vol + 2-digit-SIC sector, fit on the same S&P 500 train
# split as v2. Held-out 2026: Brier 0.108, AUC 0.824, ECE 2.4%; at the
# alert line P >= 0.40, precision 0.503 vs a 16.2% base rate (3.1x).
# Weights: CRUCIBLE/data/exp009_results.json + finding 009.
MAJOR_THRESHOLD_PCT = 5.0
MAJOR_ALERT_LINE = 0.40  # rationale calls out the tier at/above this

_MAJOR_BIAS = -2.4142
_MAJOR_ITEM_WEIGHTS = {
    "2.02": 2.0024,
    "7.01": -0.0035,
    "8.01": -0.3167,
    "1.01": -0.3882,
    "5.02": -0.6683,
    "5.07": -0.7603,
    "9.01": -0.1342,
}
_MAJOR_VOL_WEIGHT = 0.2134
# 2-digit SIC major groups (top-10 by train frequency); others contribute 0.
_MAJOR_SIC_WEIGHTS = {
    "49": -0.6874,  # utilities — big moves are rare
    "73": 0.4693,  # business services / software
    "27": -0.644,  # printing & publishing
    "38": 0.1822,  # instruments
    "67": -0.4424,  # holding/investment offices
    "28": -0.091,  # chemicals & pharma
    "36": 0.2389,  # electronics
    "35": 0.2876,  # industrial machinery (incl. computers)
    "63": -0.332,  # insurance
    "60": -0.6066,  # depository institutions (banks)
}


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


def major_move_probability(
    item_codes: list[str],
    trailing_vol: float | None = None,
    sic_code: str | None = None,
) -> float:
    """Calibrated P(|SPY-adjusted move| >= 5%) over the filing's first session.

    Args:
        item_codes: 8-K item codes present on the filing.
        trailing_vol: Stdev of daily returns (%) over the prior 20 sessions.
            None → train-average assumption (z = 0).
        sic_code: The filer's SIC code (e.g. "3674"); only the 2-digit major
            group is used. None/unknown groups contribute 0 (graceful
            degradation toward the items+vol model).

    Returns:
        Probability in (0, 1).
    """
    z = _MAJOR_BIAS
    for code in item_codes:
        z += _MAJOR_ITEM_WEIGHTS.get(code, 0.0)
    vol_z = 0.0 if trailing_vol is None else (trailing_vol - _VOL_MEAN) / _VOL_SD
    z += _MAJOR_VOL_WEIGHT * vol_z
    if sic_code:
        z += _MAJOR_SIC_WEIGHTS.get(str(sic_code)[:2], 0.0)
    return 1.0 / (1.0 + math.exp(-z))
