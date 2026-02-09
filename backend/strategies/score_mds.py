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
    option_type: str = ""  # 'CE' | 'PE'
    reason: str = ""


def decide_exit_mds(*, position_type: str, score: float, slope: float, slow_mom: float) -> ExitDecision:
    """Deterministic exits for the ScoreEngine strategy.

    Mirrors the existing rules in `TradingBot._handle_mds_signal`.
    """
    neutral = abs(score) <= 6.0

    should_exit = False
    reason = ""

    if position_type == "CE":
        if score <= -10.0:
            if slow_mom <= -1.0:
                should_exit = True
                reason = "MDS Reversal (slow confirm)"
        elif neutral:
            if abs(slow_mom) <= 1.0:
                should_exit = True
                reason = "MDS Neutral (slow confirm)"
        elif slope <= -2.0 and score < 12.0:
            if slow_mom <= 0.0:
                should_exit = True
                reason = "MDS Momentum Loss (slow confirm)"

    elif position_type == "PE":
        if score >= 10.0:
            if slow_mom >= 1.0:
                should_exit = True
                reason = "MDS Reversal (slow confirm)"
        elif neutral:
            if abs(slow_mom) <= 1.0:
                should_exit = True
                reason = "MDS Neutral (slow confirm)"
        elif slope >= 2.0 and score > -12.0:
            if slow_mom >= 0.0:
                should_exit = True
                reason = "MDS Momentum Loss (slow confirm)"

    return ExitDecision(should_exit, reason)


def decide_entry_mds(
    *,
    ready: bool,
    is_choppy: bool,
    direction: str,
    score: float,
    slope: float,
    confirm_count: int,
    confirm_needed: int,
) -> EntryDecision:
    if not ready:
        return EntryDecision(False, "", "mds_not_ready")

    if is_choppy:
        return EntryDecision(False, "", "mds_choppy")

    if direction == "NONE":
        return EntryDecision(False, "", "neutral_band")

    if abs(score) < 10.0:
        return EntryDecision(False, "", "score_too_low")

    if abs(slope) < 1.0:
        return EntryDecision(False, "", "slope_too_low")

    if confirm_count < confirm_needed:
        return EntryDecision(False, "", "arming")

    option_type = "CE" if direction == "CE" else "PE"
    return EntryDecision(True, option_type, "")
