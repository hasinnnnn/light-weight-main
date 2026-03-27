from __future__ import annotations

import pandas as pd

from indicators.sma import calculate_sma
from .base_strategy import StrategyPreparation


MARUBOZU_BODY_RATIO_MIN = 0.8
MARUBOZU_SHADOW_RATIO_MAX = 0.1


def prepare_break_ma_strategy(frame: pd.DataFrame, params: dict[str, object]) -> StrategyPreparation:
    """Prepare one OHLCV dataframe for the Break MA support strategy."""
    prepared = frame.copy()
    ma_period = max(int(params["ma_period"]), 1)
    exit_mode = str(params.get("exit_mode", "ma_breakdown")).strip()
    breakdown_confirm_mode = str(params.get("breakdown_confirm_mode", "body_breakdown")).strip()

    prepared["ma"] = calculate_sma(prepared["close"], period=ma_period)

    previous_close = prepared["close"].shift(1)
    previous_ma = prepared["ma"].shift(1)
    touch_ma = prepared["low"].le(prepared["ma"])
    hold_above_ma = prepared["close"].ge(prepared["ma"])
    trend_still_above = previous_close.gt(previous_ma)

    bearish_candle = prepared["close"].lt(prepared["open"])
    body_breakdown = bearish_candle & prepared["close"].lt(prepared["ma"])

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
        ma_breakdown_exit = marubozu_breakdown
        confirm_summary = "marubozu bearish yang breakdown di bawah MA"
    else:
        ma_breakdown_exit = body_breakdown
        confirm_summary = "body candle bearish yang close di bawah MA"

    indicator_ready = prepared["ma"].notna() & previous_close.notna() & previous_ma.notna()
    entry_signal = trend_still_above & touch_ma & hold_above_ma

    prepared["entry_signal"] = entry_signal.fillna(False) & indicator_ready
    prepared["exit_signal"] = ma_breakdown_exit.fillna(False) & indicator_ready
    prepared["strategy_exit_price"] = prepared["ma"].where(prepared["exit_signal"])
    prepared["indicator_ready"] = indicator_ready.fillna(False)

    if exit_mode == "tp_sl_trailing_only":
        exit_rule_summary = (
            f"Exit saat ada {confirm_summary} di bawah MA {ma_period} atau saat stop loss, take profit, "
            "trailing stop, batas holding, atau akhir data dari parameter umum backtest kena."
        )
        risk_management_enabled = True
    else:
        exit_rule_summary = (
            f"Exit saat ada {confirm_summary} di bawah MA {ma_period}. "
            "Stop loss, take profit, dan trailing stop dari parameter umum tidak aktif di mode ini."
        )
        risk_management_enabled = False

    return StrategyPreparation(
        frame=prepared,
        warmup_bars=ma_period + 1,
        entry_rule_summary=(
            f"Buy saat harga pullback ke MA {ma_period}, low menyentuh MA dan close tetap di atas MA."
        ),
        exit_rule_summary=exit_rule_summary,
        risk_management_enabled=risk_management_enabled,
        strategy_exit_price_column="strategy_exit_price",
    )
