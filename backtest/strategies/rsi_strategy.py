from __future__ import annotations

import pandas as pd

from indicators.rsi import calculate_rsi
from indicators.sma import calculate_sma
from .base_strategy import StrategyPreparation


def prepare_rsi_strategy(frame: pd.DataFrame, params: dict[str, object]) -> StrategyPreparation:
    """Prepare one OHLCV dataframe for the RSI strategy."""
    prepared = frame.copy()
    rsi_period = int(params["rsi_period"])
    oversold_level = float(params["oversold_level"])
    overbought_level = float(params["overbought_level"])
    exit_rsi_level = float(params["exit_rsi_level"])
    trend_filter_enabled = bool(params["trend_filter_enabled"])
    trend_ma_period = int(params["trend_ma_period"])
    exit_mode = str(params["exit_mode"])

    prepared["rsi"] = calculate_rsi(prepared["close"], period=rsi_period)
    prepared["trend_ma"] = calculate_sma(prepared["close"], trend_ma_period)

    previous_rsi = prepared["rsi"].shift(1)
    cross_up_oversold = previous_rsi.lt(oversold_level) & prepared["rsi"].ge(oversold_level)
    trend_ok = prepared["close"].gt(prepared["trend_ma"]) if trend_filter_enabled else True
    entry_signal = cross_up_oversold & trend_ok

    rsi_above_level_exit = prepared["rsi"].gt(exit_rsi_level)
    cross_down_overbought_exit = previous_rsi.gt(overbought_level) & prepared["rsi"].le(overbought_level)

    if exit_mode == "cross_down_overbought":
        exit_signal = cross_down_overbought_exit
        exit_rule_summary = (
            f"Exit saat RSI cross turun dari area overbought {overbought_level:.0f}. "
            "Stop loss, take profit, dan trailing stop dari parameter umum tidak aktif di mode ini."
        )
        risk_management_enabled = False
    elif exit_mode == "fixed_tp_sl":
        exit_signal = rsi_above_level_exit
        exit_rule_summary = (
            f"Exit saat RSI di atas {exit_rsi_level:.0f} atau saat stop loss, take profit, "
            "trailing stop, batas holding, atau akhir data dari parameter umum backtest kena."
        )
        risk_management_enabled = True
    else:
        exit_signal = rsi_above_level_exit
        exit_rule_summary = (
            f"Exit saat RSI di atas {exit_rsi_level:.0f}. "
            "Stop loss, take profit, dan trailing stop dari parameter umum tidak aktif di mode ini."
        )
        risk_management_enabled = False

    required_columns = ["rsi"]
    if trend_filter_enabled:
        required_columns.append("trend_ma")
    indicator_ready = prepared[required_columns].notna().all(axis=1) & previous_rsi.notna()

    prepared["entry_signal"] = entry_signal.fillna(False) & indicator_ready
    prepared["exit_signal"] = exit_signal.fillna(False) & indicator_ready
    prepared["indicator_ready"] = indicator_ready.fillna(False)

    entry_rule_summary = (
        f"Buy saat RSI cross naik di atas {oversold_level:.0f}"
        + (
            f" dan close di atas SMA {trend_ma_period}."
            if trend_filter_enabled
            else "."
        )
    )
    warmup_bars = max(rsi_period + 1, trend_ma_period if trend_filter_enabled else 0)

    return StrategyPreparation(
        frame=prepared,
        warmup_bars=warmup_bars,
        entry_rule_summary=entry_rule_summary,
        exit_rule_summary=exit_rule_summary,
        risk_management_enabled=risk_management_enabled,
    )
