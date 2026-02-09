from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .score_mds import decide_entry_mds, decide_exit_mds
from .supertrend_adx import decide_entry_supertrend_adx
from .supertrend_macd import decide_entry_supertrend_macd, decide_exit_on_supertrend_reversal


@dataclass(frozen=True)
class StrategyEntryDecision:
    should_enter: bool
    option_type: str = ""  # 'CE' | 'PE'
    reason: str = ""
    confirm_count: int = 0
    confirm_needed: int = 0


@dataclass(frozen=True)
class StrategyExitDecision:
    should_exit: bool
    reason: str = ""


class SuperTrendMacdRunner:
    """Decision-only runner for ST + optional MACD + optional HTF filter."""

    def reset(self) -> None:
        return

    def decide_exit(self, *, position_type: str, st_direction: int, min_hold_active: bool) -> StrategyExitDecision:
        d = decide_exit_on_supertrend_reversal(
            position_type=str(position_type or ""),
            st_direction=int(st_direction or 0),
            min_hold_active=bool(min_hold_active),
        )
        return StrategyExitDecision(bool(d.should_exit), str(d.reason or ""))

    def decide_entry(
        self,
        *,
        signal: Optional[str],
        flipped: bool,
        trade_only_on_flip: bool,
        htf_filter_enabled: bool,
        candle_interval_seconds: int,
        htf_direction: int,
        macd_confirmation_enabled: bool,
        macd_last: Optional[float],
        macd_signal_line: Optional[float],
        adx_value: Optional[float],
        adx_threshold: float,
    ) -> StrategyEntryDecision:
        _ = adx_value
        _ = adx_threshold
        d = decide_entry_supertrend_macd(
            signal=signal,
            flipped=bool(flipped),
            trade_only_on_flip=bool(trade_only_on_flip),
            macd_confirmation_enabled=bool(macd_confirmation_enabled),
            macd_last=macd_last,
            macd_signal_line=macd_signal_line,
            htf_filter_enabled=bool(htf_filter_enabled),
            candle_interval_seconds=int(candle_interval_seconds or 0),
            htf_direction=int(htf_direction or 0),
        )
        option_type = ""
        if d.should_enter and signal:
            option_type = "CE" if str(signal).upper() == "GREEN" else "PE"
        return StrategyEntryDecision(bool(d.should_enter), option_type, str(d.reason or ""))


class SuperTrendAdxRunner:
    """Decision-only runner for ST + ADX + optional HTF filter."""

    def reset(self) -> None:
        return

    def decide_exit(self, *, position_type: str, st_direction: int, min_hold_active: bool) -> StrategyExitDecision:
        d = decide_exit_on_supertrend_reversal(
            position_type=str(position_type or ""),
            st_direction=int(st_direction or 0),
            min_hold_active=bool(min_hold_active),
        )
        return StrategyExitDecision(bool(d.should_exit), str(d.reason or ""))

    def decide_entry(
        self,
        *,
        signal: Optional[str],
        flipped: bool,
        trade_only_on_flip: bool,
        htf_filter_enabled: bool,
        candle_interval_seconds: int,
        htf_direction: int,
        macd_confirmation_enabled: bool,
        macd_last: Optional[float],
        macd_signal_line: Optional[float],
        adx_value: Optional[float],
        adx_threshold: float,
    ) -> StrategyEntryDecision:
        _ = macd_confirmation_enabled
        _ = macd_last
        _ = macd_signal_line
        d = decide_entry_supertrend_adx(
            signal=signal,
            flipped=bool(flipped),
            trade_only_on_flip=bool(trade_only_on_flip),
            htf_filter_enabled=bool(htf_filter_enabled),
            candle_interval_seconds=int(candle_interval_seconds or 0),
            htf_direction=int(htf_direction or 0),
            adx_value=adx_value,
            adx_threshold=float(adx_threshold or 0.0),
        )
        option_type = ""
        if d.should_enter and signal:
            option_type = "CE" if str(signal).upper() == "GREEN" else "PE"
        return StrategyEntryDecision(bool(d.should_enter), option_type, str(d.reason or ""))


class ScoreMdsRunner:
    """Decision-only runner for the MDS/ScoreEngine strategy.

    Owns the multi-candle confirmation state.
    """

    def __init__(self) -> None:
        self._last_direction: Optional[str] = None
        self._confirm_count: int = 0

    def reset(self) -> None:
        self._last_direction = None
        self._confirm_count = 0

    def on_entry_attempted(self) -> None:
        """Call after an entry attempt (success or blocked downstream)."""
        self._confirm_count = 0

    def decide_exit(self, *, position_type: str, score: float, slope: float, slow_mom: float) -> StrategyExitDecision:
        d = decide_exit_mds(
            position_type=str(position_type or ""),
            score=float(score or 0.0),
            slope=float(slope or 0.0),
            slow_mom=float(slow_mom or 0.0),
        )
        return StrategyExitDecision(bool(d.should_exit), str(d.reason or ""))

    def decide_entry(
        self,
        *,
        ready: bool,
        is_choppy: bool,
        direction: str,
        score: float,
        slope: float,
        confirm_needed: int,
    ) -> StrategyEntryDecision:
        direction = str(direction or "NONE")

        if not ready:
            return StrategyEntryDecision(False, "", "mds_not_ready")
        if is_choppy:
            return StrategyEntryDecision(False, "", "mds_choppy")

        if direction == "NONE":
            self._last_direction = direction
            self._confirm_count = 0
            return StrategyEntryDecision(False, "", "neutral_band")

        if abs(float(score or 0.0)) < 10.0:
            self._last_direction = direction
            self._confirm_count = 0
            return StrategyEntryDecision(False, "", "score_too_low")

        if abs(float(slope or 0.0)) < 1.0:
            self._last_direction = direction
            self._confirm_count = 0
            return StrategyEntryDecision(False, "", "slope_too_low")

        if self._last_direction == direction:
            self._confirm_count += 1
        else:
            self._last_direction = direction
            self._confirm_count = 1

        d = decide_entry_mds(
            ready=bool(ready),
            is_choppy=bool(is_choppy),
            direction=direction,
            score=float(score or 0.0),
            slope=float(slope or 0.0),
            confirm_count=int(self._confirm_count),
            confirm_needed=int(confirm_needed or 0),
        )

        return StrategyEntryDecision(
            bool(d.should_enter),
            str(d.option_type or ""),
            str(d.reason or ""),
            confirm_count=int(self._confirm_count),
            confirm_needed=int(confirm_needed or 0),
        )
