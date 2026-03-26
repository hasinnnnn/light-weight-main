from __future__ import annotations

import pandas as pd

from indicators.ema import calculate_ema
from strategies.base_strategy import StrategyPreparation


def prepare_break_ema_strategy(frame: pd.DataFrame, params: dict[str, object]) -> StrategyPreparation:
    """Prepare one OHLCV dataframe for the Break EMA support strategy."""
    prepared = frame.copy()
    ema_period = max(int(params["ema_period"]), 1)
    exit_mode = str(params.get("exit_mode", "ema_breakdown")).strip()

    prepared["ema"] = calculate_ema(prepared["close"], period=ema_period)

    previous_close = prepared["close"].shift(1)
    previous_ema = prepared["ema"].shift(1)
    touch_ema = prepared["low"].le(prepared["ema"])
    hold_above_ema = prepared["close"].ge(prepared["ema"])
    trend_still_above = previous_close.gt(previous_ema)

    entry_signal = trend_still_above & touch_ema & hold_above_ema
    ema_breakdown_exit = prepared["close"].lt(prepared["ema"])
    indicator_ready = prepared["ema"].notna() & previous_close.notna() & previous_ema.notna()

    prepared["entry_signal"] = entry_signal.fillna(False) & indicator_ready
    if exit_mode == "tp_sl_trailing_only":
        prepared["exit_signal"] = False
        exit_rule_summary = (
            "Exit hanya mengikuti stop loss, take profit, trailing stop, "
            "batas holding, atau akhir data dari parameter umum backtest."
        )
    else:
        prepared["exit_signal"] = ema_breakdown_exit.fillna(False) & indicator_ready
        exit_rule_summary = (
            f"Exit saat close jebol di bawah EMA {ema_period}. "
            "Stop loss, take profit, dan trailing stop dari parameter umum tetap aktif."
        )
    prepared["indicator_ready"] = indicator_ready.fillna(False)

    return StrategyPreparation(
        frame=prepared,
        warmup_bars=ema_period + 1,
        entry_rule_summary=(
            f"Buy saat harga pullback ke EMA {ema_period}, low menyentuh EMA dan close tetap di atas EMA."
        ),
        exit_rule_summary=exit_rule_summary,
    )



