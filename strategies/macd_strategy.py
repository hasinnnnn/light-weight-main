from __future__ import annotations

import pandas as pd

from indicators.macd import calculate_macd
from indicators.sma import calculate_sma
from strategies.base_strategy import StrategyPreparation


def prepare_macd_strategy(frame: pd.DataFrame, params: dict[str, object]) -> StrategyPreparation:
    """Prepare one OHLCV dataframe for the MACD strategy."""
    prepared = frame.copy()
    fast_period = int(params["macd_fast_period"])
    slow_period = int(params["macd_slow_period"])
    signal_period = int(params["macd_signal_period"])
    trend_filter_enabled = bool(params["trend_filter_enabled"])
    trend_ma_period = int(params["trend_ma_period"])
    entry_mode = str(params["entry_mode"])
    exit_mode = str(params["exit_mode"])

    macd_frame = calculate_macd(
        prepared["close"],
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
    )
    for column in macd_frame.columns:
        prepared[column] = macd_frame[column]
    prepared["trend_ma"] = calculate_sma(prepared["close"], trend_ma_period)

    previous_macd = prepared["macd"].shift(1)
    previous_signal = prepared["macd_signal"].shift(1)
    previous_histogram = prepared["macd_histogram"].shift(1)

    if entry_mode == "macd_cross_up_zero":
        entry_signal = previous_macd.le(0) & prepared["macd"].gt(0)
        entry_rule_summary = "Buy saat MACD cross naik di atas garis nol."
    elif entry_mode == "histogram_turn_positive":
        entry_signal = previous_histogram.le(0) & prepared["macd_histogram"].gt(0)
        entry_rule_summary = "Buy saat histogram MACD berbalik positif."
    else:
        entry_signal = previous_macd.le(previous_signal) & prepared["macd"].gt(prepared["macd_signal"])
        entry_rule_summary = "Buy saat MACD cross naik di atas signal line."

    trend_ok = prepared["close"].gt(prepared["trend_ma"]) & prepared["macd"].gt(0)
    if trend_filter_enabled:
        entry_signal = entry_signal & trend_ok
        entry_rule_summary += f" Filter trend: close di atas SMA {trend_ma_period} dan MACD > 0."

    if exit_mode == "macd_cross_down_zero":
        exit_signal = previous_macd.ge(0) & prepared["macd"].lt(0)
        exit_rule_summary = "Exit saat MACD turun di bawah garis nol."
    elif exit_mode == "fixed_tp_sl":
        exit_signal = pd.Series(False, index=prepared.index)
        exit_rule_summary = "Exit hanya lewat stop loss, take profit, trailing stop, atau batas holding."
    else:
        exit_signal = previous_macd.ge(previous_signal) & prepared["macd"].lt(prepared["macd_signal"])
        exit_rule_summary = "Exit saat MACD cross turun di bawah signal line."

    required_columns = ["macd", "macd_signal", "macd_histogram"]
    if trend_filter_enabled:
        required_columns.append("trend_ma")
    indicator_ready = (
        prepared[required_columns].notna().all(axis=1)
        & previous_macd.notna()
        & previous_signal.notna()
    )
    if entry_mode == "histogram_turn_positive":
        indicator_ready = indicator_ready & previous_histogram.notna()

    prepared["entry_signal"] = entry_signal.fillna(False) & indicator_ready
    prepared["exit_signal"] = exit_signal.fillna(False) & indicator_ready
    prepared["indicator_ready"] = indicator_ready.fillna(False)

    warmup_bars = max(
        slow_period + signal_period,
        trend_ma_period if trend_filter_enabled else 0,
    )
    return StrategyPreparation(
        frame=prepared,
        warmup_bars=warmup_bars,
        entry_rule_summary=entry_rule_summary,
        exit_rule_summary=exit_rule_summary,
    )
