from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Optional

from config import bot_state, config
from indicators import SuperTrend, MACD, ADX
from indices import get_index_config, round_to_strike
from score_engine import ScoreEngine, Candle
from strategies.runner import ScoreMdsRunner, SuperTrendAdxRunner, SuperTrendMacdRunner
from utils import can_take_new_trade

logger = logging.getLogger(__name__)


def synthetic_option_ltp(*, index_ltp: float, strike: int, option_type: str) -> float:
    """Synthetic option premium for paper testing.

    Mirrors the existing SIM_* pricing logic in trading_bot.
    """
    try:
        index_ltp = float(index_ltp or 0.0)
        strike = int(strike or 0)
        option_type = str(option_type or '').upper()
    except Exception:
        return 0.05

    if index_ltp <= 0 or strike <= 0 or option_type not in {'CE', 'PE'}:
        return 0.05

    distance_from_atm = abs(index_ltp - strike)
    if option_type == 'CE':
        intrinsic = max(0.0, index_ltp - strike)
    else:
        intrinsic = max(0.0, strike - index_ltp)

    atm_time_value = 150.0
    time_decay_factor = max(0.0, 1.0 - (distance_from_atm / 500.0))
    time_value = atm_time_value * time_decay_factor

    ltp = intrinsic + time_value
    ltp = round(float(ltp) / 0.05) * 0.05
    ltp = max(0.05, round(float(ltp), 2))
    return float(ltp)


@dataclass
class PortfolioPosition:
    strategy_id: str
    strategy_name: str
    trade_id: str
    index_name: str
    option_type: str
    strike: int
    expiry: str
    security_id: str
    qty: int
    mode: str
    entry_time: str
    entry_price: float
    current_ltp: float
    target_points: float = 0.0
    initial_stoploss: float = 0.0
    trail_start_profit: float = 0.0
    trail_step: float = 0.0
    max_loss_per_trade: float = 0.0
    trailing_sl: Optional[float] = None
    highest_profit: float = 0.0
    entry_time_utc: Optional[datetime] = None


class PortfolioStrategy:
    def __init__(self, *, strategy_id: str, strategy_name: str, strategy_config: dict, instance_config: Optional[dict] = None):
        self.strategy_id = str(strategy_id)
        self.strategy_name = str(strategy_name)
        self.cfg = dict(strategy_config or {})
        self.instance = dict(instance_config or {})

        self.indicator_type = str(self.cfg.get('indicator_type', 'supertrend_macd') or 'supertrend_macd').strip().lower()

        st_period = int(self.cfg.get('supertrend_period', config.get('supertrend_period', 7)) or 7)
        st_mult = float(self.cfg.get('supertrend_multiplier', config.get('supertrend_multiplier', 4)) or 4)
        self.st = SuperTrend(period=st_period, multiplier=st_mult)

        self.macd = MACD(
            fast=int(self.cfg.get('macd_fast', config.get('macd_fast', 12)) or 12),
            slow=int(self.cfg.get('macd_slow', config.get('macd_slow', 26)) or 26),
            signal=int(self.cfg.get('macd_signal', config.get('macd_signal', 9)) or 9),
        )

        self.adx = ADX(period=int(self.cfg.get('adx_period', config.get('adx_period', 14)) or 14))

        base_tf = int(self.effective('candle_interval', config.get('candle_interval', 5) or 5) or 5)
        self.score_engine = ScoreEngine(
            st_period=st_period,
            st_multiplier=st_mult,
            macd_fast=int(self.cfg.get('macd_fast', config.get('macd_fast', 12)) or 12),
            macd_slow=int(self.cfg.get('macd_slow', config.get('macd_slow', 26)) or 26),
            macd_signal=int(self.cfg.get('macd_signal', config.get('macd_signal', 9)) or 9),
            base_timeframe_seconds=int(base_tf),
            bonus_macd_triple=float(self.cfg.get('mds_bonus_macd_triple', config.get('mds_bonus_macd_triple', 1.0)) or 0.0),
            bonus_macd_momentum=float(self.cfg.get('mds_bonus_macd_momentum', config.get('mds_bonus_macd_momentum', 0.5)) or 0.0),
            bonus_macd_cross=float(self.cfg.get('mds_bonus_macd_cross', config.get('mds_bonus_macd_cross', 0.5)) or 0.0),
        )

        self._st_runner = SuperTrendAdxRunner() if self.indicator_type == 'supertrend_adx' else SuperTrendMacdRunner()
        self._mds_runner = ScoreMdsRunner()

        self.last_supertrend_signal: Optional[str] = None
        self.last_trade_time: Optional[datetime] = None
        self.position: Optional[PortfolioPosition] = None

        # Activity / observability
        self.last_eval_time_utc: Optional[str] = None
        self.last_decision: Optional[str] = None
        self.last_action: Optional[str] = None  # ENTER/EXIT
        self.last_action_time_utc: Optional[str] = None
        self.last_action_reason: Optional[str] = None
        self.last_snapshot: dict = {}

    def to_state(self) -> dict:
        return {
            'strategy_id': str(self.strategy_id),
            'strategy_name': str(self.strategy_name),
            'active': bool(self.is_active()),
            'mode': str(self.instance_mode()),
            'indicator_type': str(self.indicator_type),
            'has_position': bool(self.position is not None),
            'last_eval_time_utc': self.last_eval_time_utc,
            'last_decision': self.last_decision,
            'last_action': self.last_action,
            'last_action_time_utc': self.last_action_time_utc,
            'last_action_reason': self.last_action_reason,
            'snapshot': dict(self.last_snapshot or {}),
        }

    def is_active(self) -> bool:
        v = self.instance.get('active')
        if v is None:
            return True
        return bool(v)

    def instance_mode(self) -> str:
        mode = str(self.instance.get('mode') or 'paper').strip().lower()
        return mode if mode in {'paper', 'live'} else 'paper'

    def index_name(self) -> str:
        idx = self.effective('selected_index', None)
        if idx is None:
            idx = config.get('selected_index', 'NIFTY')
        idx = str(idx or 'NIFTY').strip().upper()
        return idx or 'NIFTY'

    def candle_interval(self) -> int:
        try:
            v = int(self.effective('candle_interval', config.get('candle_interval', 5) or 5) or 5)
        except Exception:
            v = int(config.get('candle_interval', 5) or 5)
        return int(v) if int(v) > 0 else 5

    def effective(self, key: str, default=None):
        if key in self.instance and self.instance.get(key) is not None:
            return self.instance.get(key)
        if key in self.cfg and self.cfg.get(key) is not None:
            return self.cfg.get(key)
        if key in config and config.get(key) is not None:
            return config.get(key)
        return default

    def reset(self) -> None:
        self.st.reset()
        self.macd.reset()
        self.adx.reset()
        self.score_engine.reset()
        try:
            self._st_runner.reset()
        except Exception:
            pass
        try:
            self._mds_runner.reset()
        except Exception:
            pass
        self.last_supertrend_signal = None
        self.last_trade_time = None
        self.position = None
        self.last_eval_time_utc = None
        self.last_decision = None
        self.last_action = None
        self.last_action_time_utc = None
        self.last_action_reason = None
        self.last_snapshot = {}

    def _min_hold_active(self) -> bool:
        if not self.position or not self.position.entry_time_utc:
            return False
        min_hold = int(self.cfg.get('min_hold_seconds', config.get('min_hold_seconds', 0)) or 0)
        if min_hold <= 0:
            return False
        held = (datetime.now(timezone.utc) - self.position.entry_time_utc).total_seconds()
        return held < min_hold

    async def on_candle_close(self, *, index_name: str, candle_interval: int, high: float, low: float, close: float, bot) -> None:
        """Update indicators and manage entry/exit for this strategy."""
        now_utc = datetime.now(timezone.utc)
        self.last_eval_time_utc = now_utc.isoformat()
        self.last_decision = None

        index_name = str(index_name or self.index_name() or 'NIFTY').strip().upper()
        try:
            candle_interval = int(candle_interval or self.candle_interval() or 5)
        except Exception:
            candle_interval = int(self.candle_interval() or 5)

        st_value, st_signal = self.st.add_candle(float(high), float(low), float(close))
        if self.macd:
            self.macd.add_candle(float(high), float(low), float(close))
        adx_value = None
        try:
            adx_val, _adx_sig = self.adx.add_candle(float(high), float(low), float(close))
            if adx_val is not None:
                adx_value = float(adx_val)
        except Exception:
            adx_value = None

        mds_snapshot = None
        if self.indicator_type == 'score_mds':
            try:
                mds_snapshot = self.score_engine.on_base_candle(Candle(high=float(high), low=float(low), close=float(close)))
            except Exception:
                mds_snapshot = None

        # Keep a compact snapshot for UI/debug.
        try:
            st_dir = int(getattr(self.st, 'direction', 0) or 0)
        except Exception:
            st_dir = 0
        snap = {
            'index': str(index_name),
            'tf': int(candle_interval),
            'close': float(close),
            'st_signal': str(st_signal) if st_signal is not None else None,
            'st_direction': int(st_dir),
            'adx': float(adx_value) if adx_value is not None else None,
        }
        if self.indicator_type == 'score_mds' and mds_snapshot is not None:
            try:
                snap.update({
                    'mds_ready': bool(getattr(mds_snapshot, 'ready', False)),
                    'mds_choppy': bool(getattr(mds_snapshot, 'is_choppy', False)),
                    'mds_direction': str(getattr(mds_snapshot, 'direction', 'NONE') or 'NONE'),
                    'mds_score': float(getattr(mds_snapshot, 'score', 0.0) or 0.0),
                    'mds_slope': float(getattr(mds_snapshot, 'slope', 0.0) or 0.0),
                })
            except Exception:
                pass
        self.last_snapshot = snap

        # Update portfolio position LTP (synthetic)
        if self.position:
            try:
                self.position.current_ltp = float(await bot._portfolio_get_position_ltp(self.position, float(close)))
            except Exception:
                self.position.current_ltp = synthetic_option_ltp(
                    index_ltp=float(close),
                    strike=int(self.position.strike),
                    option_type=str(self.position.option_type),
                )

        # Exit logic
        if self.position:
            if self.indicator_type == 'score_mds' and mds_snapshot is not None:
                try:
                    score = float(getattr(mds_snapshot, 'score', 0.0) or 0.0)
                    slope = float(getattr(mds_snapshot, 'slope', 0.0) or 0.0)
                    slow_mom = 0.0
                    try:
                        tf_scores = getattr(mds_snapshot, 'tf_scores', {}) or {}
                        if isinstance(tf_scores, dict) and tf_scores:
                            slow_tf = max(int(k) for k in tf_scores.keys())
                            slow = tf_scores.get(slow_tf)
                            slow_mom = float(getattr(slow, 'macd_score', 0.0) or 0.0) + float(getattr(slow, 'hist_score', 0.0) or 0.0)
                    except Exception:
                        slow_mom = 0.0

                    exit_d = self._mds_runner.decide_exit(
                        position_type=str(self.position.option_type),
                        score=float(score),
                        slope=float(slope),
                        slow_mom=float(slow_mom),
                    )
                    if exit_d.should_exit and not self._min_hold_active():
                        await bot._portfolio_close_position(self, float(self.position.current_ltp), exit_d.reason)
                        self.last_decision = 'exit'
                        return
                except Exception:
                    pass
            else:
                st_direction = int(getattr(self.st, 'direction', 0) or 0)
                exit_d = self._st_runner.decide_exit(
                    position_type=str(self.position.option_type),
                    st_direction=st_direction,
                    min_hold_active=bool(self._min_hold_active()),
                )
                if exit_d.should_exit:
                    await bot._portfolio_close_position(self, float(self.position.current_ltp), exit_d.reason)
                    self.last_decision = 'exit'
                    return

        # Entry logic
        if self.position:
            self.last_decision = 'holding'
            return

        if not self.is_active():
            self.last_decision = 'inactive'
            return

        if not bot._can_place_new_entry_order():
            self.last_decision = 'entry_blocked'
            return
        if not can_take_new_trade():
            self.last_decision = 'outside_hours'
            return
        max_trades = int(config.get('max_trades_per_day', 0) or 0)
        if max_trades > 0 and int(bot_state.get('daily_trades', 0) or 0) >= max_trades:
            self.last_decision = 'max_trades'
            return

        # Optional per-strategy min_trade_gap
        min_gap = int(self.cfg.get('min_trade_gap', config.get('min_trade_gap', 0)) or 0)
        if min_gap > 0 and self.last_trade_time:
            if (datetime.now() - self.last_trade_time).total_seconds() < min_gap:
                self.last_decision = 'min_gap'
                return

        # Decide entry
        if self.indicator_type == 'score_mds' and mds_snapshot is not None:
            if not bool(getattr(mds_snapshot, 'ready', False)):
                self.last_decision = 'not_ready'
                return
            if bool(getattr(mds_snapshot, 'is_choppy', False)):
                self.last_decision = 'choppy'
                return
            direction = str(getattr(mds_snapshot, 'direction', 'NONE') or 'NONE')
            score = float(getattr(mds_snapshot, 'score', 0.0) or 0.0)
            slope = float(getattr(mds_snapshot, 'slope', 0.0) or 0.0)

            confirm_needed = 1 if self.instance_mode() == 'paper' else 2
            entry_d = self._mds_runner.decide_entry(
                ready=True,
                is_choppy=False,
                direction=direction,
                score=score,
                slope=slope,
                confirm_needed=int(confirm_needed),
            )
            if not entry_d.should_enter:
                return
            option_type = str(entry_d.option_type or '')
        else:
            signal = str(st_signal or '')
            flipped = bool(signal) and (self.last_supertrend_signal is None or signal != self.last_supertrend_signal)
            if signal:
                self.last_supertrend_signal = signal

            adx_last = adx_value
            entry_d = self._st_runner.decide_entry(
                signal=signal,
                flipped=bool(flipped),
                trade_only_on_flip=bool(self.cfg.get('trade_only_on_flip', config.get('trade_only_on_flip', False))),
                htf_filter_enabled=False,
                candle_interval_seconds=int(candle_interval),
                htf_direction=0,
                macd_confirmation_enabled=bool(self.cfg.get('macd_confirmation_enabled', config.get('macd_confirmation_enabled', True))),
                macd_last=(float(self.macd.last_macd) if (self.macd and self.macd.last_macd is not None) else None),
                macd_signal_line=(float(self.macd.last_signal_line) if (self.macd and self.macd.last_signal_line is not None) else None),
                adx_value=adx_last,
                adx_threshold=float(self.cfg.get('adx_threshold', config.get('adx_threshold', 25.0)) or 25.0),
            )
            if not entry_d.should_enter:
                return
            option_type = str(entry_d.option_type or ('CE' if signal == 'GREEN' else 'PE'))

        atm_strike = round_to_strike(float(close), index_name)
        await bot._portfolio_enter_position(self, option_type, int(atm_strike), float(close))
        self.last_trade_time = datetime.now()
