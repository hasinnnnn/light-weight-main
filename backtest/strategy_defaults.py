from __future__ import annotations

from typing import Any

def get_default_backtest_general_params() -> dict[str, Any]:
    """Return the default general backtest settings."""
    return {
        "initial_capital": 10_000_000.0,
        "position_sizing_mode": "fixed_nominal",
        "position_size_value": 1_000_000.0,
        "buy_fee_pct": 0.15,
        "sell_fee_pct": 0.25,
        "slippage_pct": 0.10,
        "stop_loss_pct": 3.0,
        "take_profit_pct": 6.0,
        "trailing_stop_pct": 0.0,
        "max_holding_bars": 0,
        "cooldown_bars": 0,
        "show_indicator_preview": True,
    }


def get_default_rsi_params() -> dict[str, Any]:
    """Return the default RSI strategy settings."""
    return {
        "rsi_period": 14,
        "oversold_level": 30.0,
        "overbought_level": 70.0,
        "exit_rsi_level": 60.0,
        "trend_filter_enabled": True,
        "trend_ma_period": 50,
        "entry_mode": "cross_up_oversold",
        "exit_mode": "rsi_above_level",
    }


def get_default_macd_params() -> dict[str, Any]:
    """Return the default MACD strategy settings."""
    return {
        "macd_fast_period": 12,
        "macd_slow_period": 26,
        "macd_signal_period": 9,
        "trend_filter_enabled": True,
        "trend_ma_period": 50,
        "entry_mode": "macd_cross_up_signal",
        "exit_mode": "macd_cross_down_signal",
    }


def get_default_break_ema_params() -> dict[str, Any]:
    """Return the default Break EMA strategy settings."""
    return {
        "ema_period": 10,
        "exit_mode": "ema_breakdown",
        "breakdown_confirm_mode": "body_breakdown",
    }


def get_default_break_ma_params() -> dict[str, Any]:
    """Return the default Break MA strategy settings."""
    return {
        "ma_period": 200,
        "exit_mode": "ma_breakdown",
        "breakdown_confirm_mode": "body_breakdown",
    }


def get_default_parabolic_sar_params() -> dict[str, Any]:
    """Return the default Parabolic SAR strategy settings."""
    return {
        "psar_acceleration_pct": 2.0,
        "psar_max_acceleration_pct": 20.0,
    }


def get_default_volume_breakout_params() -> dict[str, Any]:
    """Return the default Volume Breakout strategy settings."""
    return {
        "consolidation_bars": 10,
        "max_consolidation_range_pct": 6.0,
        "volume_ma_period": 20,
        "consolidation_volume_ratio_max": 0.80,
        "breakout_volume_ratio_min": 1.80,
        "breakout_buffer_pct": 0.20,
        "exit_after_bars": 1,
    }


def get_default_strategy_params(strategy_key: str) -> dict[str, Any]:
    """Return the default settings for one strategy."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if normalized_key == "RSI":
        return get_default_rsi_params()
    if normalized_key == "MACD":
        return get_default_macd_params()
    if normalized_key == "BREAK_EMA":
        return get_default_break_ema_params()
    if normalized_key == "BREAK_MA":
        return get_default_break_ma_params()
    if normalized_key == "PARABOLIC_SAR":
        return get_default_parabolic_sar_params()
    if normalized_key == "VOLUME_BREAKOUT":
        return get_default_volume_breakout_params()
    raise ValueError(f"Unsupported backtest strategy: {strategy_key}")


