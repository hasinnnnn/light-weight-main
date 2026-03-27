from __future__ import annotations

import pandas as pd

from indicators.ema import calculate_ema
from .base_strategy import StrategyPreparation


MARUBOZU_BODY_RATIO_MIN = 0.8
MARUBOZU_SHADOW_RATIO_MAX = 0.1


def prepare_break_ema_strategy(frame: pd.DataFrame, params: dict[str, object]) -> StrategyPreparation:
    """Prepare one OHLCV dataframe for the Break EMA support strategy."""
    prepared = frame.copy()
    ema_period = max(int(params["ema_period"]), 1)
    exit_mode = str(params.get("exit_mode", "ema_breakdown")).strip()
    breakdown_confirm_mode = str(params.get("breakdown_confirm_mode", "body_breakdown")).strip()

    prepared["ema"] = calculate_ema(prepared["close"], period=ema_period)

    previous_close = prepared["close"].shift(1)
    previous_ema = prepared["ema"].shift(1)
    touch_ema = prepared["low"].le(prepared["ema"])
    hold_above_ema = prepared["close"].ge(prepared["ema"])
    trend_still_above = previous_close.gt(previous_ema)

    bearish_candle = prepared["close"].lt(prepared["open"])
    body_breakdown = bearish_candle & prepared["close"].lt(prepared["ema"])

    candle_range = prepared["high"].sub(prepared["low"])
    body_size = prepared["open"].sub(prepared["close"]).abs()
    upper_shadow = prepared["high"].sub(prepared[["open", "close"]].max(axis=1))
    lower_shadow = prepared[["open", "close"]].min(axis=1).sub(prepared["low"])
    safe_candle_range = candle_range.where(candle_range.gt(0))
    marubozu_breakdown = (
        body_breakdown
        & safe_candle_range.notna()
        & body_size.div(safe_candle_range).ge(MARUBOZU_BODY_RATIO_MIN)
        & upper_shadow.div(safe_candle_range).le(MARUBOZU_SHADOW_RATIO_MAX)
        & lower_shadow.div(safe_candle_range).le(MARUBOZU_SHADOW_RATIO_MAX)
    )

    if breakdown_confirm_mode == "marubozu_breakdown":
        ema_breakdown_exit = marubozu_breakdown
        confirm_summary = "marubozu bearish yang breakdown di bawah EMA"
    else:
        ema_breakdown_exit = body_breakdown
        confirm_summary = "body candle bearish yang close di bawah EMA"

    indicator_ready = prepared["ema"].notna() & previous_close.notna() & previous_ema.notna()
    entry_signal = trend_still_above & touch_ema & hold_above_ema

    prepared["entry_signal"] = entry_signal.fillna(False) & indicator_ready
    prepared["exit_signal"] = ema_breakdown_exit.fillna(False) & indicator_ready
    prepared["strategy_exit_price"] = prepared["ema"].where(prepared["exit_signal"])
    prepared["indicator_ready"] = indicator_ready.fillna(False)

    if exit_mode == "tp_sl_trailing_only":
        exit_rule_summary = (
            f"Exit saat ada {confirm_summary} di bawah EMA {ema_period} atau saat stop loss, take profit, "
            "trailing stop, batas holding, atau akhir data dari parameter umum backtest kena."
        )
        risk_management_enabled = True
    else:
        exit_rule_summary = (
            f"Exit saat ada {confirm_summary} di bawah EMA {ema_period}. "
            "Stop loss, take profit, dan trailing stop dari parameter umum tidak aktif di mode ini."
        )
        risk_management_enabled = False

    return StrategyPreparation(
        frame=prepared,
        warmup_bars=ema_period + 1,
        entry_rule_summary=(
            f"Buy saat harga pullback ke EMA {ema_period}, low menyentuh EMA dan close tetap di atas EMA."
        ),
        exit_rule_summary=exit_rule_summary,
        risk_management_enabled=risk_management_enabled,
        strategy_exit_price_column="strategy_exit_price",
    )
