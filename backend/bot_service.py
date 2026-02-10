# Bot Service - Interface layer between API routes and TradingBot
import logging
from typing import Optional
from config import bot_state, config
from indices import get_index_config, get_available_indices
from database import save_config, load_config

logger = logging.getLogger(__name__)


def _sanitize_portfolio_strategy_ids(raw) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    if isinstance(raw, str):
        try:
            import json
            raw = json.loads(raw)
        except Exception:
            raw = []
    if not isinstance(raw, list):
        return ids
    for v in raw:
        try:
            i = int(v)
        except Exception:
            continue
        if i <= 0:
            continue
        if i in seen:
            continue
        seen.add(i)
        ids.append(i)
    return ids


def _sanitize_portfolio_instances(raw) -> dict:
    """Normalize portfolio_instances mapping.

    Expected shape: {"<strategy_id>": {"active": bool, "mode": "paper"|"live", ...}}
    Strategy IDs are returned as strings.
    """
    if isinstance(raw, str):
        try:
            import json
            raw = json.loads(raw)
        except Exception:
            raw = {}
    if not isinstance(raw, dict):
        return {}

    cleaned: dict[str, dict] = {}
    allowed_timeframes = {int(x.get('value')) for x in (get_available_timeframes() or []) if isinstance(x, dict) and x.get('value') is not None}
    for k, v in raw.items():
        try:
            sid = int(k)
        except Exception:
            continue
        if sid <= 0:
            continue
        if not isinstance(v, dict):
            v = {}

        active = v.get('active')
        if active is None:
            active = True
        active = bool(active)

        mode = str(v.get('mode') or 'paper').strip().lower()
        if mode not in {'paper', 'live'}:
            mode = 'paper'

        def _num(x, cast, default=None):
            if x is None:
                return default
            try:
                return cast(x)
            except Exception:
                return default

        order_qty = _num(v.get('order_qty'), int, None)
        if order_qty is not None:
            order_qty = max(0, min(10, int(order_qty)))

        target_points = _num(v.get('target_points'), float, None)
        initial_stoploss = _num(v.get('initial_stoploss'), float, None)
        trail_start_profit = _num(v.get('trail_start_profit'), float, None)
        trail_step = _num(v.get('trail_step'), float, None)
        max_loss_per_trade = _num(v.get('max_loss_per_trade'), float, None)

        selected_index = v.get('selected_index')
        if selected_index is not None:
            try:
                selected_index = str(selected_index).strip().upper()
            except Exception:
                selected_index = None
            if selected_index and selected_index not in set(get_available_indices() or []):
                selected_index = None

        candle_interval = _num(v.get('candle_interval'), int, None)
        if candle_interval is not None:
            candle_interval = int(candle_interval)
            if candle_interval not in allowed_timeframes:
                candle_interval = None

        inst = {
            'active': active,
            'mode': mode,
        }
        if selected_index is not None:
            inst['selected_index'] = str(selected_index)
        if candle_interval is not None:
            inst['candle_interval'] = int(candle_interval)
        if order_qty is not None:
            inst['order_qty'] = int(order_qty)
        if target_points is not None:
            inst['target_points'] = float(target_points)
        if initial_stoploss is not None:
            inst['initial_stoploss'] = float(initial_stoploss)
        if trail_start_profit is not None:
            inst['trail_start_profit'] = float(trail_start_profit)
        if trail_step is not None:
            inst['trail_step'] = float(trail_step)
        if max_loss_per_trade is not None:
            inst['max_loss_per_trade'] = float(max_loss_per_trade)

        cleaned[str(sid)] = inst

    return cleaned

# Lazy import to avoid circular imports
_trading_bot = None

def get_trading_bot():
    """Get or create the trading bot instance"""
    global _trading_bot
    if _trading_bot is None:
        from trading_bot import TradingBot
        _trading_bot = TradingBot()
    return _trading_bot


async def start_bot() -> dict:
    """Start the trading bot"""
    bot = get_trading_bot()
    result = await bot.start()
    logger.info(f"[BOT] Start requested: {result}")
    return result


async def stop_bot() -> dict:
    """Stop the trading bot"""
    bot = get_trading_bot()
    result = await bot.stop()
    logger.info(f"[BOT] Stop requested: {result}")
    return result


async def squareoff_position() -> dict:
    """Force square off current position"""
    bot = get_trading_bot()
    result = await bot.squareoff()
    logger.info(f"[BOT] Squareoff requested: {result}")
    return result


async def squareoff_portfolio_strategy(strategy_id: int) -> dict:
    """Square off only one strategy in portfolio mode."""
    bot = get_trading_bot()
    try:
        result = await bot._portfolio_squareoff_strategy(strategy_id, reason="Manual Square-off")
    except Exception as e:
        logger.error(f"[BOT] Strategy squareoff failed: {e}")
        return {"status": "error", "message": "Squareoff failed"}
    logger.info(f"[BOT] Strategy squareoff requested: {result}")
    return result


def get_bot_status() -> dict:
    """Get current bot status with market hour validation"""
    from utils import is_market_open, get_ist_time
    
    ist = get_ist_time()
    market_is_open = is_market_open()
    is_weekday = ist.weekday() < 5  # 0-4 = Mon-Fri, 5-6 = Sat-Sun
    
    logger.debug(f"[STATUS] Market check: Weekday={is_weekday}, Time={ist.strftime('%H:%M')}, Open={market_is_open}")
    
    # Provide portfolio-aware status: include whether portfolio mode is enabled and per-strategy modes summary
    portfolio_enabled = bool(config.get('portfolio_enabled'))
    portfolio_instances = config.get('portfolio_instances') or {}
    modes_summary = {"live": 0, "paper": 0}
    try:
        for v in (portfolio_instances or {}).values():
            try:
                m = str(v.get('mode') or 'paper').strip().lower()
            except Exception:
                m = 'paper'
            if m == 'live':
                modes_summary['live'] += 1
            else:
                modes_summary['paper'] += 1
    except Exception:
        modes_summary = {"live": 0, "paper": 0}

    return {
        "is_running": bot_state['is_running'],
        "mode": bot_state['mode'],
        "portfolio_enabled": portfolio_enabled,
        "portfolio_modes": modes_summary,
        "market_status": "open" if market_is_open else "closed",
        "market_details": {
            "is_weekday": is_weekday,
            "current_time_ist": ist.strftime('%H:%M:%S'),
            "trading_hours": "09:15 - 15:30 IST"
        },
        "connection_status": "connected" if config['dhan_access_token'] else "disconnected",
        "daily_max_loss_triggered": bot_state['daily_max_loss_triggered'],
        "trading_enabled": bool(config.get('trading_enabled', True)),
        "selected_index": config['selected_index'],
        "candle_interval": config['candle_interval']
    }
    



def get_market_data() -> dict:
    """Get current market data"""
    from datetime import datetime, timezone
    
    return {
        "ltp": bot_state['index_ltp'],
        "supertrend_signal": bot_state['last_supertrend_signal'],
        "supertrend_value": bot_state['supertrend_value'],
        "htf_supertrend_signal": bot_state.get('htf_supertrend_signal'),
        "htf_supertrend_value": bot_state.get('htf_supertrend_value', 0.0),
        "macd_value": bot_state['macd_value'],
        "signal_status": bot_state['signal_status'],
        "htf_signal_status": bot_state.get('htf_signal_status', 'waiting'),
        "selected_index": config['selected_index'],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_position() -> dict:
    """Get current position info"""
    if not bot_state['current_position']:
        return {"has_position": False}
    
    index_config = get_index_config(config['selected_index'])
    qty = int(bot_state['current_position'].get('qty') or 0)
    if qty <= 0:
        qty = config['order_qty'] * index_config['lot_size']
    unrealized_pnl = (bot_state['current_option_ltp'] - bot_state['entry_price']) * qty
    
    return {
        "has_position": True,
        "option_type": bot_state['current_position'].get('option_type'),
        "strike": bot_state['current_position'].get('strike'),
        "expiry": bot_state['current_position'].get('expiry'),
        "index_name": bot_state['current_position'].get('index_name', config['selected_index']),
        "entry_price": bot_state['entry_price'],
        "current_ltp": bot_state['current_option_ltp'],
        "unrealized_pnl": unrealized_pnl,
        "trailing_sl": bot_state['trailing_sl'],
        "qty": qty
    }


def get_daily_summary() -> dict:
    """Get daily trading summary"""
    return {
        "total_trades": bot_state['daily_trades'],
        "total_pnl": bot_state['daily_pnl'],
        "max_drawdown": bot_state['max_drawdown'],
        "daily_stop_triggered": bot_state['daily_max_loss_triggered']
    }


def get_config() -> dict:
    """Get current configuration"""
    index_config = get_index_config(config['selected_index'])
    
    return {
        # API Settings
        "has_credentials": bool(config['dhan_access_token'] and config['dhan_client_id']),
        "mode": bot_state['mode'],
        # Index & Timeframe
        "selected_index": config['selected_index'],
        "candle_interval": config['candle_interval'],
        "lot_size": index_config['lot_size'],
        "strike_interval": index_config['strike_interval'],
        "expiry_type": index_config.get('expiry_type', 'weekly'),
        # Risk Parameters
        "order_qty": config['order_qty'],
        "max_trades_per_day": config['max_trades_per_day'],
        "daily_max_loss": config['daily_max_loss'],
        "max_loss_per_trade": config.get('max_loss_per_trade', 0),
        "initial_stoploss": config.get('initial_stoploss', 50),
        "trail_start_profit": config['trail_start_profit'],
        "trail_step": config['trail_step'],
        "target_points": config['target_points'],
        "risk_per_trade": config.get('risk_per_trade', 0),
        # Indicator / Strategy Settings
        "indicator_type": config.get('indicator_type', 'supertrend'),
        "supertrend_period": config.get('supertrend_period', 7),
        "supertrend_multiplier": config.get('supertrend_multiplier', 4),
        "macd_fast": int(config.get('macd_fast', 12)),
        "macd_slow": int(config.get('macd_slow', 26)),
        "macd_signal": int(config.get('macd_signal', 9)),
        "macd_confirmation_enabled": bool(config.get('macd_confirmation_enabled', True)),

        # Testing
        "bypass_market_hours": bool(config.get('bypass_market_hours', False)),

        # Market data persistence
        "store_tick_data": bool(config.get("store_tick_data", True)),
        "market_data_poll_seconds": float(config.get("market_data_poll_seconds", 1.0) or 1.0),
        "tick_persist_interval_seconds": float(config.get("tick_persist_interval_seconds", 1.0) or 1.0),
        "pause_market_data_when_closed": bool(config.get("pause_market_data_when_closed", False)),

        # Paper replay
        "paper_replay_enabled": bool(config.get("paper_replay_enabled", False)),
        "paper_replay_date_ist": str(config.get("paper_replay_date_ist", "") or ""),
        "paper_replay_speed": float(config.get("paper_replay_speed", 10.0) or 10.0),

        # MTF filter
        "htf_filter_enabled": bool(config.get('htf_filter_enabled', True)),
        "htf_filter_timeframe": int(config.get('htf_filter_timeframe', 60)),

        # Exit protection
        "min_hold_seconds": int(config.get('min_hold_seconds', 15)),

        # Order pacing
        "min_order_cooldown_seconds": int(config.get('min_order_cooldown_seconds', 15)),

        # Trading control
        "trading_enabled": bool(config.get('trading_enabled', True)),
        # ADX
        "adx_period": int(config.get('adx_period', 14) or 14),
        "adx_threshold": float(config.get('adx_threshold', 25.0) or 25.0),

        # Portfolio (multi-strategy)
        "portfolio_enabled": bool(config.get('portfolio_enabled', False)),
        "portfolio_strategy_ids": _sanitize_portfolio_strategy_ids(config.get('portfolio_strategy_ids', []) or []),
        "portfolio_instances": _sanitize_portfolio_instances(config.get('portfolio_instances', {}) or {}),
    }


async def patch_portfolio_instance(strategy_id: int, patch: dict) -> dict:
    """Patch a single strategy instance override in portfolio_instances."""
    try:
        sid = int(strategy_id)
    except Exception:
        return {"status": "error", "message": "Invalid strategy_id"}
    if sid <= 0:
        return {"status": "error", "message": "Invalid strategy_id"}

    if not isinstance(patch, dict):
        return {"status": "error", "message": "Patch must be an object"}

    instances = _sanitize_portfolio_instances(config.get('portfolio_instances', {}) or {})
    current = dict(instances.get(str(sid), {}) or {})
    merged = dict(current)
    merged.update(patch)

    sanitized_one = _sanitize_portfolio_instances({str(sid): merged})
    if str(sid) not in sanitized_one:
        return {"status": "error", "message": "Invalid instance payload"}

    instances[str(sid)] = sanitized_one[str(sid)]
    config['portfolio_instances'] = instances
    await save_config()
    return {"status": "success", "strategy_id": sid, "instance": instances[str(sid)]}


async def update_config_values(updates: dict) -> dict:
    """Update configuration values"""
    logger.info(f"[CONFIG] Received updates: {list(updates.keys())}")
    updated_fields = []
    
    creds_changed = False

    if updates.get('dhan_access_token') is not None:
        config['dhan_access_token'] = str(updates['dhan_access_token'] or '').strip()
        updated_fields.append('dhan_access_token')
        creds_changed = True

    if updates.get('dhan_client_id') is not None:
        config['dhan_client_id'] = str(updates['dhan_client_id'] or '').strip()
        updated_fields.append('dhan_client_id')
        creds_changed = True
        
    if updates.get('order_qty') is not None:
        qty = int(updates['order_qty'])
        # Limit to 1-10 lots for safety
        config['order_qty'] = max(1, min(10, qty))
        updated_fields.append('order_qty')
        if qty != config['order_qty']:
            logger.warning(f"[CONFIG] order_qty capped from {qty} to {config['order_qty']} (max 10 lots)")
        
    if updates.get('max_trades_per_day') is not None:
        config['max_trades_per_day'] = int(updates['max_trades_per_day'])
        updated_fields.append('max_trades_per_day')
        
    if updates.get('daily_max_loss') is not None:
        config['daily_max_loss'] = float(updates['daily_max_loss'])
        updated_fields.append('daily_max_loss')
        
    if updates.get('initial_stoploss') is not None:
        config['initial_stoploss'] = float(updates['initial_stoploss'])
        updated_fields.append('initial_stoploss')
        logger.info(f"[CONFIG] Initial stoploss changed to: {config['initial_stoploss']} pts")
        
    if updates.get('max_loss_per_trade') is not None:
        config['max_loss_per_trade'] = float(updates['max_loss_per_trade'])
        updated_fields.append('max_loss_per_trade')
        logger.info(f"[CONFIG] Max loss per trade changed to: ₹{config['max_loss_per_trade']}")
        
    if updates.get('trail_start_profit') is not None:
        config['trail_start_profit'] = float(updates['trail_start_profit'])
        updated_fields.append('trail_start_profit')
        logger.info(f"[CONFIG] Trail start profit changed to: {config['trail_start_profit']} pts")
        
    if updates.get('trail_step') is not None:
        config['trail_step'] = float(updates['trail_step'])
        updated_fields.append('trail_step')
        logger.info(f"[CONFIG] Trail step changed to: {config['trail_step']} pts")
    
    if updates.get('target_points') is not None:
        config['target_points'] = float(updates['target_points'])
        updated_fields.append('target_points')
        logger.info(f"[CONFIG] Target points changed to: {config['target_points']}")
        
    if updates.get('risk_per_trade') is not None:
        config['risk_per_trade'] = float(updates['risk_per_trade'])
        updated_fields.append('risk_per_trade')
        logger.info(f"[CONFIG] Risk per trade changed to: ₹{config['risk_per_trade']}")

    if updates.get('enable_risk_based_lots') is not None:
        config['enable_risk_based_lots'] = bool(updates['enable_risk_based_lots'])
        updated_fields.append('enable_risk_based_lots')
        logger.info(f"[CONFIG] Enable risk-based lots set to: {config['enable_risk_based_lots']}")

    if updates.get('trading_enabled') is not None:
        config['trading_enabled'] = bool(updates['trading_enabled'])
        updated_fields.append('trading_enabled')
        logger.info(f"[CONFIG] Trading enabled set to: {config['trading_enabled']}")

    if updates.get('htf_filter_enabled') is not None:
        config['htf_filter_enabled'] = bool(updates['htf_filter_enabled'])
        updated_fields.append('htf_filter_enabled')
        logger.info(f"[CONFIG] HTF filter enabled set to: {config['htf_filter_enabled']}")

    if updates.get('htf_filter_timeframe') is not None:
        tf = int(updates['htf_filter_timeframe'])
        # Current implementation supports 60s HTF cleanly; keep it constrained for safety.
        if tf != 60:
            logger.warning(f"[CONFIG] Unsupported HTF timeframe: {tf}s. Using 60s")
            tf = 60
        config['htf_filter_timeframe'] = tf
        updated_fields.append('htf_filter_timeframe')
        logger.info(f"[CONFIG] HTF filter timeframe set to: {config['htf_filter_timeframe']}s")

    if updates.get('min_hold_seconds') is not None:
        mhs = max(0, int(updates['min_hold_seconds']))
        config['min_hold_seconds'] = mhs
        updated_fields.append('min_hold_seconds')
        logger.info(f"[CONFIG] Min hold seconds set to: {config['min_hold_seconds']}s")

    if updates.get('min_order_cooldown_seconds') is not None:
        cooldown = max(0, int(updates['min_order_cooldown_seconds']))
        config['min_order_cooldown_seconds'] = cooldown
        updated_fields.append('min_order_cooldown_seconds')
        logger.info(f"[CONFIG] Min order cooldown set to: {config['min_order_cooldown_seconds']}s")

    if updates.get('bypass_market_hours') is not None:
        config['bypass_market_hours'] = str(updates['bypass_market_hours']).lower() in ('true', '1', 'yes')
        updated_fields.append('bypass_market_hours')
        logger.warning(f"[CONFIG] Bypass market hours: {config['bypass_market_hours']}")

    if updates.get("store_tick_data") is not None:
        config["store_tick_data"] = bool(updates["store_tick_data"])
        updated_fields.append("store_tick_data")
        logger.info(f"[CONFIG] Store tick data: {config['store_tick_data']}")

    if updates.get("market_data_poll_seconds") is not None:
        v = float(updates["market_data_poll_seconds"])
        config["market_data_poll_seconds"] = max(0.25, min(5.0, v))
        updated_fields.append("market_data_poll_seconds")
        logger.info(f"[CONFIG] Market data poll seconds: {config['market_data_poll_seconds']}")

    if updates.get("tick_persist_interval_seconds") is not None:
        v = float(updates["tick_persist_interval_seconds"])
        config["tick_persist_interval_seconds"] = max(0.25, min(10.0, v))
        updated_fields.append("tick_persist_interval_seconds")
        logger.info(f"[CONFIG] Tick persist interval seconds: {config['tick_persist_interval_seconds']}")

    if updates.get("pause_market_data_when_closed") is not None:
        config["pause_market_data_when_closed"] = bool(updates["pause_market_data_when_closed"])
        updated_fields.append("pause_market_data_when_closed")
        logger.info(f"[CONFIG] Pause market data when closed: {config['pause_market_data_when_closed']}")

    if updates.get("paper_replay_enabled") is not None:
        config["paper_replay_enabled"] = bool(updates["paper_replay_enabled"])
        updated_fields.append("paper_replay_enabled")
        logger.warning(f"[CONFIG] Paper replay enabled: {config['paper_replay_enabled']}")

    if updates.get("paper_replay_date_ist") is not None:
        config["paper_replay_date_ist"] = str(updates["paper_replay_date_ist"] or "")
        updated_fields.append("paper_replay_date_ist")
        logger.info(f"[CONFIG] Paper replay date (IST): {config['paper_replay_date_ist']}")

    if updates.get("paper_replay_speed") is not None:
        v = float(updates["paper_replay_speed"])
        config["paper_replay_speed"] = max(0.1, min(100.0, v))
        updated_fields.append("paper_replay_speed")
        logger.info(f"[CONFIG] Paper replay speed: {config['paper_replay_speed']}x")
        
    if updates.get('selected_index') is not None:
        new_index = updates['selected_index'].upper()
        available = get_available_indices()
        if new_index in available:
            config['selected_index'] = new_index
            bot_state['selected_index'] = new_index
            updated_fields.append('selected_index')
            logger.info(f"[CONFIG] Index changed to: {new_index}")
        else:
            logger.warning(f"[CONFIG] Invalid index: {new_index}. Available: {available}")
            
    if updates.get('candle_interval') is not None:
        valid_intervals = [5, 15, 30, 60, 300, 900]  # 5s, 15s, 30s, 1m, 5m, 15m
        new_interval = int(updates['candle_interval'])
        if new_interval in valid_intervals:
            config['candle_interval'] = new_interval
            updated_fields.append('candle_interval')
            logger.info(f"[CONFIG] Candle interval changed to: {new_interval}s")
            # Reset indicator when interval changes
            bot = get_trading_bot()
            bot.reset_indicator()
        else:
            logger.warning(f"[CONFIG] Invalid interval: {new_interval}. Valid: {valid_intervals}")
    
    if updates.get('indicator_type') is not None:
        new_indicator = str(updates['indicator_type']).lower()
        if new_indicator in ('supertrend', 'supertrend_macd', 'supertrend_adx', 'score_mds'):
            config['indicator_type'] = new_indicator
            updated_fields.append('indicator_type')
            logger.info(f"[CONFIG] Indicator changed to: {new_indicator}")
            # Re-initialize indicators
            bot = get_trading_bot()
            bot._initialize_indicator()
        else:
            logger.warning(f"[CONFIG] Invalid indicator: {new_indicator}. Supported: 'supertrend', 'supertrend_macd', 'supertrend_adx', 'score_mds'")

    if updates.get('portfolio_enabled') is not None:
        config['portfolio_enabled'] = bool(updates.get('portfolio_enabled'))
        updated_fields.append('portfolio_enabled')
        logger.warning(f"[CONFIG] Portfolio enabled: {config['portfolio_enabled']}")

    if updates.get('portfolio_strategy_ids') is not None:
        raw = updates.get('portfolio_strategy_ids')
        ids = _sanitize_portfolio_strategy_ids(raw)
        config['portfolio_strategy_ids'] = ids
        updated_fields.append('portfolio_strategy_ids')
        logger.info(f"[CONFIG] Portfolio strategy IDs: {config['portfolio_strategy_ids']}")

    if updates.get('portfolio_instances') is not None:
        raw = updates.get('portfolio_instances')
        instances = _sanitize_portfolio_instances(raw)
        config['portfolio_instances'] = instances
        updated_fields.append('portfolio_instances')
        logger.info(f"[CONFIG] Portfolio instances updated: {list(instances.keys())}")

    if updates.get('macd_confirmation_enabled') is not None:
        config['macd_confirmation_enabled'] = str(updates['macd_confirmation_enabled']).lower() in ('true', '1', 'yes')
        updated_fields.append('macd_confirmation_enabled')
        logger.info(f"[CONFIG] MACD confirmation enabled: {config['macd_confirmation_enabled']}")
    
    # Update indicator parameters if provided
    indicator_params = {
        'supertrend_period': int,
        'supertrend_multiplier': float,
        'macd_fast': int,
        'macd_slow': int,
        'macd_signal': int,
        'adx_period': int,
        'adx_threshold': float,
    }
    
    for param, param_type in indicator_params.items():
        if updates.get(param) is not None:
            try:
                config[param] = param_type(updates[param])
                updated_fields.append(param)
                logger.info(f"[CONFIG] {param} changed to: {config[param]}")
            except (ValueError, TypeError) as e:
                logger.warning(f"[CONFIG] Invalid value for {param}: {e}")
    
    await save_config()
    logger.info(f"[CONFIG] Updated: {updated_fields}")

    # If credentials changed while bot is running in live mode, re-init Dhan immediately.
    # This prevents the bot from continuing with a stale/None Dhan client.
    if creds_changed and bot_state.get('mode') == 'live' and bot_state.get('is_running'):
        try:
            bot = get_trading_bot()
            ok = bot.initialize_dhan()
            if ok:
                logger.info("[CONFIG] Dhan client re-initialized after credentials update")
            else:
                logger.warning("[CONFIG] Dhan client NOT initialized after credentials update (check creds)")
        except Exception as e:
            logger.warning(f"[CONFIG] Failed to re-initialize Dhan after credentials update: {e}")
    
    return {"status": "success", "message": "Configuration updated", "updated": updated_fields}


async def set_trading_mode(mode: str) -> dict:
    """Set trading mode (paper/live)"""
    if bot_state['current_position']:
        return {"status": "error", "message": "Cannot change mode with open position"}
    
    if mode not in ['paper', 'live']:
        return {"status": "error", "message": "Invalid mode. Use 'paper' or 'live'"}
    
    # When switching to live mode, ensure credentials are present and initialize the client
    # if the bot is already running.
    if mode == 'live':
        if not (str(config.get('dhan_access_token') or '').strip() and str(config.get('dhan_client_id') or '').strip()):
            return {"status": "error", "message": "Dhan credentials not configured. Update credentials first."}

        if bot_state.get('is_running'):
            try:
                bot = get_trading_bot()
                if not bot.initialize_dhan():
                    return {"status": "error", "message": "Failed to initialize Dhan API. Check credentials/SDK."}
            except Exception as e:
                return {"status": "error", "message": f"Failed to initialize Dhan API: {e}"}

    bot_state['mode'] = mode
    logger.info(f"[CONFIG] Trading mode changed to: {mode}")

    # Safety: when switching to paper, drop any existing Dhan client reference.
    if mode == 'paper':
        try:
            bot = get_trading_bot()
            bot.dhan = None
        except Exception:
            pass

    return {"status": "success", "mode": mode}


def get_available_indices_list() -> list:
    """Get list of available indices with their config"""
    from indices import INDICES
    
    result = []
    for name, cfg in INDICES.items():
        result.append({
            "name": name,
            "display_name": cfg['name'],
            "lot_size": cfg['lot_size'],
            "strike_interval": cfg['strike_interval'],
            "expiry_type": cfg.get('expiry_type', 'weekly'),
            "expiry_day": cfg.get('expiry_day', 1)
        })
    return result


def get_available_timeframes() -> list:
    """Get list of available timeframes"""
    return [
        {"value": 5, "label": "5 seconds"},
        {"value": 15, "label": "15 seconds"},
        {"value": 30, "label": "30 seconds"},
        {"value": 60, "label": "1 minute"},
        {"value": 300, "label": "5 minutes"},
        {"value": 900, "label": "15 minutes"}
    ]
