from __future__ import annotations

from typing import Any

from backtest.strategy_catalog import (
    BREAK_EMA_CONFIRMATION_MODES,
    BREAK_EMA_EXIT_MODES,
    BREAK_MA_CONFIRMATION_MODES,
    BREAK_MA_EXIT_MODES,
    MACD_ENTRY_MODES,
    MACD_EXIT_MODES,
    POSITION_SIZING_MODES,
    RSI_ENTRY_MODES,
    RSI_EXIT_MODES,
)
from backtest.strategy_defaults import (
    get_default_backtest_general_params,
    get_default_break_ema_params,
    get_default_break_ma_params,
    get_default_macd_params,
    get_default_parabolic_sar_params,
    get_default_rsi_params,
    get_default_volume_breakout_params,
)


def _coerce_float(value: Any, fallback: float, minimum: float = 0.0) -> float:
    """Convert a raw value into a safe bounded float."""
    try:
        normalized_value = float(value)
    except (TypeError, ValueError):
        normalized_value = float(fallback)
    return max(normalized_value, minimum)



def _coerce_int(value: Any, fallback: int, minimum: int = 0) -> int:
    """Convert a raw value into a safe bounded integer."""
    try:
        normalized_value = int(value)
    except (TypeError, ValueError):
        normalized_value = int(fallback)
    return max(normalized_value, minimum)



def _coerce_bool(value: Any, fallback: bool) -> bool:
    """Convert one raw value into a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return bool(fallback)



def normalize_general_backtest_params(raw_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize the general backtest settings into safe runtime values."""
    defaults = get_default_backtest_general_params()
    raw_params = raw_params or {}

    position_mode = str(
        raw_params.get("position_sizing_mode", defaults["position_sizing_mode"])
    ).strip()
    if position_mode not in POSITION_SIZING_MODES:
        position_mode = defaults["position_sizing_mode"]

    position_size_value = _coerce_float(
        raw_params.get("position_size_value"),
        float(defaults["position_size_value"]),
        minimum=0.01,
    )
    if position_mode == "fixed_percent_of_equity":
        position_size_value = min(position_size_value, 100.0)

    return {
        "initial_capital": _coerce_float(
            raw_params.get("initial_capital"),
            float(defaults["initial_capital"]),
            minimum=1.0,
        ),
        "position_sizing_mode": position_mode,
        "position_size_value": position_size_value,
        "buy_fee_pct": _coerce_float(raw_params.get("buy_fee_pct"), defaults["buy_fee_pct"]),
        "sell_fee_pct": _coerce_float(raw_params.get("sell_fee_pct"), defaults["sell_fee_pct"]),
        "slippage_pct": _coerce_float(raw_params.get("slippage_pct"), defaults["slippage_pct"]),
        "stop_loss_pct": _coerce_float(raw_params.get("stop_loss_pct"), defaults["stop_loss_pct"]),
        "take_profit_pct": _coerce_float(raw_params.get("take_profit_pct"), defaults["take_profit_pct"]),
        "trailing_stop_pct": _coerce_float(
            raw_params.get("trailing_stop_pct"),
            defaults["trailing_stop_pct"],
        ),
        "max_holding_bars": _coerce_int(
            raw_params.get("max_holding_bars"),
            defaults["max_holding_bars"],
        ),
        "cooldown_bars": _coerce_int(
            raw_params.get("cooldown_bars"),
            defaults["cooldown_bars"],
        ),
        "show_indicator_preview": _coerce_bool(
            raw_params.get("show_indicator_preview"),
            bool(defaults["show_indicator_preview"]),
        ),
    }



def normalize_strategy_backtest_params(
    strategy_key: str,
    raw_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one strategy parameter dictionary."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    raw_params = raw_params or {}

    if normalized_key == "RSI":
        defaults = get_default_rsi_params()
        oversold_level = min(
            _coerce_float(raw_params.get("oversold_level"), defaults["oversold_level"], minimum=1.0),
            49.0,
        )
        overbought_level = max(
            _coerce_float(
                raw_params.get("overbought_level"),
                defaults["overbought_level"],
                minimum=oversold_level + 5.0,
            ),
            oversold_level + 5.0,
        )
        overbought_level = min(overbought_level, 99.0)
        exit_rsi_level = _coerce_float(
            raw_params.get("exit_rsi_level"),
            defaults["exit_rsi_level"],
            minimum=oversold_level + 1.0,
        )
        exit_rsi_level = min(exit_rsi_level, 99.0)
        entry_mode = str(raw_params.get("entry_mode", defaults["entry_mode"])).strip()
        if entry_mode not in RSI_ENTRY_MODES:
            entry_mode = defaults["entry_mode"]
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in RSI_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        return {
            "rsi_period": _coerce_int(raw_params.get("rsi_period"), defaults["rsi_period"], minimum=2),
            "oversold_level": oversold_level,
            "overbought_level": overbought_level,
            "exit_rsi_level": exit_rsi_level,
            "trend_filter_enabled": _coerce_bool(
                raw_params.get("trend_filter_enabled"),
                defaults["trend_filter_enabled"],
            ),
            "trend_ma_period": _coerce_int(
                raw_params.get("trend_ma_period"),
                defaults["trend_ma_period"],
                minimum=2,
            ),
            "entry_mode": entry_mode,
            "exit_mode": exit_mode,
        }

    if normalized_key == "MACD":
        defaults = get_default_macd_params()
        fast_period = _coerce_int(
            raw_params.get("macd_fast_period"),
            defaults["macd_fast_period"],
            minimum=1,
        )
        slow_period = _coerce_int(
            raw_params.get("macd_slow_period"),
            defaults["macd_slow_period"],
            minimum=fast_period + 1,
        )
        signal_period = _coerce_int(
            raw_params.get("macd_signal_period"),
            defaults["macd_signal_period"],
            minimum=1,
        )
        entry_mode = str(raw_params.get("entry_mode", defaults["entry_mode"])).strip()
        if entry_mode not in MACD_ENTRY_MODES:
            entry_mode = defaults["entry_mode"]
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in MACD_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        return {
            "macd_fast_period": fast_period,
            "macd_slow_period": slow_period,
            "macd_signal_period": signal_period,
            "trend_filter_enabled": _coerce_bool(
                raw_params.get("trend_filter_enabled"),
                defaults["trend_filter_enabled"],
            ),
            "trend_ma_period": _coerce_int(
                raw_params.get("trend_ma_period"),
                defaults["trend_ma_period"],
                minimum=2,
            ),
            "entry_mode": entry_mode,
            "exit_mode": exit_mode,
        }

    if normalized_key == "BREAK_EMA":
        defaults = get_default_break_ema_params()
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in BREAK_EMA_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        confirm_mode = str(
            raw_params.get("breakdown_confirm_mode", defaults["breakdown_confirm_mode"])
        ).strip()
        if confirm_mode not in BREAK_EMA_CONFIRMATION_MODES:
            confirm_mode = defaults["breakdown_confirm_mode"]
        return {
            "ema_period": _coerce_int(
                raw_params.get("ema_period"),
                defaults["ema_period"],
                minimum=1,
            ),
            "exit_mode": exit_mode,
            "breakdown_confirm_mode": confirm_mode,
        }

    if normalized_key == "BREAK_MA":
        defaults = get_default_break_ma_params()
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in BREAK_MA_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        confirm_mode = str(
            raw_params.get("breakdown_confirm_mode", defaults["breakdown_confirm_mode"])
        ).strip()
        if confirm_mode not in BREAK_MA_CONFIRMATION_MODES:
            confirm_mode = defaults["breakdown_confirm_mode"]
        return {
            "ma_period": _coerce_int(
                raw_params.get("ma_period"),
                defaults["ma_period"],
                minimum=1,
            ),
            "exit_mode": exit_mode,
            "breakdown_confirm_mode": confirm_mode,
        }

    if normalized_key == "PARABOLIC_SAR":
        defaults = get_default_parabolic_sar_params()
        acceleration_pct = _coerce_float(
            raw_params.get("psar_acceleration_pct"),
            defaults["psar_acceleration_pct"],
            minimum=0.1,
        )
        return {
            "psar_acceleration_pct": acceleration_pct,
            "psar_max_acceleration_pct": _coerce_float(
                raw_params.get("psar_max_acceleration_pct"),
                defaults["psar_max_acceleration_pct"],
                minimum=acceleration_pct,
            ),
        }

    if normalized_key == "VOLUME_BREAKOUT":
        defaults = get_default_volume_breakout_params()
        return {
            "consolidation_bars": _coerce_int(
                raw_params.get("consolidation_bars"),
                defaults["consolidation_bars"],
                minimum=3,
            ),
            "max_consolidation_range_pct": _coerce_float(
                raw_params.get("max_consolidation_range_pct"),
                defaults["max_consolidation_range_pct"],
                minimum=0.1,
            ),
            "volume_ma_period": _coerce_int(
                raw_params.get("volume_ma_period"),
                defaults["volume_ma_period"],
                minimum=3,
            ),
            "consolidation_volume_ratio_max": _coerce_float(
                raw_params.get("consolidation_volume_ratio_max"),
                defaults["consolidation_volume_ratio_max"],
                minimum=0.1,
            ),
            "breakout_volume_ratio_min": _coerce_float(
                raw_params.get("breakout_volume_ratio_min"),
                defaults["breakout_volume_ratio_min"],
                minimum=1.0,
            ),
            "breakout_buffer_pct": _coerce_float(
                raw_params.get("breakout_buffer_pct"),
                defaults["breakout_buffer_pct"],
                minimum=0.0,
            ),
            "exit_after_bars": _coerce_int(
                raw_params.get("exit_after_bars"),
                defaults["exit_after_bars"],
                minimum=1,
            ),
        }

    raise ValueError(f"Unsupported backtest strategy: {strategy_key}")



