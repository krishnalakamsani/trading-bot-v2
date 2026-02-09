from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EntryDecision:
    should_enter: bool
    reason: str = ""


def decide_entry_supertrend_adx(
    *,
    signal: Optional[str],
    flipped: bool,
    trade_only_on_flip: bool,
    htf_filter_enabled: bool,
    candle_interval_seconds: int,
    htf_direction: int,
    adx_value: Optional[float],
    adx_threshold: float,
) -> EntryDecision:
    """Entry rules for SuperTrend + ADX.

    - Signal comes from SuperTrend (GREEN/RED)
    - ADX gates entries: require ADX >= threshold
    - Optional: trade only on flip, optional HTF filter
    """

    if not signal:
        return EntryDecision(False, "no_signal")

    if trade_only_on_flip and not flipped:
        return EntryDecision(False, "no_flip")

    if adx_value is None:
        return EntryDecision(False, "adx_not_ready")

    try:
        adx_v = float(adx_value)
    except Exception:
        return EntryDecision(False, "adx_not_ready")

    if adx_v < float(adx_threshold or 0.0):
        return EntryDecision(False, "adx_below_threshold")

    if htf_filter_enabled and int(candle_interval_seconds) < 60:
        required = 1 if signal == "GREEN" else -1
        if int(htf_direction or 0) == 0:
            return EntryDecision(False, "htf_not_ready")
        if int(htf_direction or 0) != required:
            return EntryDecision(False, "htf_mismatch")

    return EntryDecision(True, "")
