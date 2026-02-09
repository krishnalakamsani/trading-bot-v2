from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExitDecision:
    should_exit: bool
    reason: str = ""


@dataclass(frozen=True)
class EntryDecision:
    should_enter: bool
    reason: str = ""


def decide_exit_on_supertrend_reversal(*, position_type: str, st_direction: int, min_hold_active: bool) -> ExitDecision:
    """Primary exit for ST-based strategies: exit on SuperTrend reversal."""
    if min_hold_active:
        return ExitDecision(False, "min_hold_active")

    if position_type == "CE" and st_direction == -1:
        return ExitDecision(True, "SuperTrend Reversal")
    if position_type == "PE" and st_direction == 1:
        return ExitDecision(True, "SuperTrend Reversal")

    return ExitDecision(False, "")


def decide_entry_supertrend_macd(
    *,
    signal: Optional[str],
    flipped: bool,
    trade_only_on_flip: bool,
    macd_confirmation_enabled: bool,
    macd_last: Optional[float],
    macd_signal_line: Optional[float],
    htf_filter_enabled: bool,
    candle_interval_seconds: int,
    htf_direction: int,
) -> EntryDecision:
    """Entry rules for ST + optional MACD confirmation + optional HTF filter.

    This mirrors the existing gating in `TradingBot.process_signal_on_close`.
    """
    if not signal:
        return EntryDecision(False, "no_signal")

    if trade_only_on_flip and not flipped:
        return EntryDecision(False, "no_flip")

    if macd_confirmation_enabled:
        if macd_last is None or macd_signal_line is None:
            return EntryDecision(False, "macd_not_ready")

        eps = 1e-9
        diff = float(macd_last) - float(macd_signal_line)
        bullish = diff >= -eps

        if signal == "GREEN" and not bullish:
            return EntryDecision(False, "macd_not_confirming_buy")
        if signal == "RED" and bullish:
            return EntryDecision(False, "macd_not_confirming_sell")

    # If trading below 1m, only take entries aligned with 1m SuperTrend.
    if htf_filter_enabled and int(candle_interval_seconds) < 60:
        required = 1 if signal == "GREEN" else -1
        if htf_direction == 0:
            return EntryDecision(False, "htf_not_ready")
        if htf_direction != required:
            return EntryDecision(False, "htf_mismatch")

    return EntryDecision(True, "")
