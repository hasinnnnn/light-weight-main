from __future__ import annotations

import pandas as pd

from backtest.strategies.base_strategy import StrategyPreparation
from backtest.strategies.break_ema_strategy import prepare_break_ema_strategy
from backtest.strategies.break_ma_strategy import prepare_break_ma_strategy
from indicators.moving_average_parts.meta import _calculate_chart_ema, _calculate_chart_sma
from indicators.source_frames import build_close_source, build_hlcv_source


def build_moving_average_dataframe(
    data: pd.DataFrame,
    length: int,
    line_name: str,
    method: str,
) -> pd.DataFrame:
    """Prepare one EMA or MA series from close prices."""
    indicator_frame = build_close_source(data)
    close = indicator_frame["close"]

    if str(method).lower() == "ema":
        line_values = _calculate_chart_ema(close, length)
    else:
        line_values = _calculate_chart_sma(close, length)

    indicator_frame[line_name] = line_values
    indicator_frame = indicator_frame.dropna(subset=[line_name])
    return indicator_frame[["time", line_name]]



def build_cross_moving_average_dataframe(
    data: pd.DataFrame,
    fast_length: int,
    slow_length: int,
    method: str,
) -> pd.DataFrame:
    """Prepare two moving-average series in one dataframe for cross detection."""
    indicator_frame = build_close_source(data)
    close = indicator_frame["close"]

    if str(method).lower() == "ema":
        indicator_frame["fast"] = _calculate_chart_ema(close, fast_length)
        indicator_frame["slow"] = _calculate_chart_ema(close, slow_length)
    else:
        indicator_frame["fast"] = _calculate_chart_sma(close, fast_length)
        indicator_frame["slow"] = _calculate_chart_sma(close, slow_length)

    indicator_frame = indicator_frame.dropna(subset=["fast", "slow"])
    return indicator_frame[["time", "fast", "slow"]]



def build_pullback_moving_average_trade_markers(
    data: pd.DataFrame,
    length: int,
    method: str,
    label: str,
) -> list[dict[str, object]]:
    """Build BUY/SELL markers using the same pullback strategy flow as backtest."""
    indicator_frame = build_hlcv_source(data)
    if indicator_frame.empty:
        return []

    normalized_method = str(method).lower()
    normalized_label = str(label).strip().upper()
    if normalized_method == "ema":
        prepared_strategy = prepare_break_ema_strategy(
            indicator_frame,
            {
                "ema_period": max(int(length), 1),
                "exit_mode": "ema_breakdown",
                "breakdown_confirm_mode": "body_breakdown",
            },
        )
    else:
        prepared_strategy = prepare_break_ma_strategy(
            indicator_frame,
            {
                "ma_period": max(int(length), 1),
                "exit_mode": "ma_breakdown",
                "breakdown_confirm_mode": "body_breakdown",
            },
        )

    return _build_strategy_trade_markers(prepared_strategy, normalized_label)



def _build_strategy_trade_markers(
    prepared_strategy: StrategyPreparation,
    normalized_label: str,
) -> list[dict[str, object]]:
    """Convert one prepared backtest strategy into BUY/SELL markers on execution bars."""
    strategy_frame = prepared_strategy.frame.reset_index(drop=True)
    if strategy_frame.empty:
        return []

    markers: list[dict[str, object]] = []
    in_position = False
    pending_action: str | None = None
    strategy_exit_price_column = prepared_strategy.strategy_exit_price_column

    for index in range(len(strategy_frame)):
        row = strategy_frame.iloc[index]
        current_time = pd.Timestamp(row["time"])
        is_last_bar = index == len(strategy_frame) - 1

        if pending_action == "entry" and not in_position:
            markers.append(
                {
                    "time": current_time,
                    "position": "below",
                    "shape": "arrow_up",
                    "color": "#22c55e",
                    "text": f"BUY {normalized_label}",
                }
            )
            in_position = True
        elif pending_action == "exit" and in_position:
            markers.append(
                {
                    "time": current_time,
                    "position": "above",
                    "shape": "arrow_down",
                    "color": "#ef4444",
                    "text": f"SELL {normalized_label}",
                }
            )
            in_position = False
        pending_action = None

        if in_position:
            if _strategy_exit_triggers_on_bar(row, strategy_exit_price_column):
                markers.append(
                    {
                        "time": current_time,
                        "position": "above",
                        "shape": "arrow_down",
                        "color": "#ef4444",
                        "text": f"SELL {normalized_label}",
                    }
                )
                in_position = False
                continue

            if not is_last_bar and bool(row.get("exit_signal", False)):
                pending_action = "exit"
        elif not is_last_bar:
            can_enter = (
                index >= int(prepared_strategy.warmup_bars)
                and bool(row.get("indicator_ready", False))
                and bool(row.get("entry_signal", False))
            )
            if can_enter:
                pending_action = "entry"

    return markers



def _strategy_exit_triggers_on_bar(
    row: pd.Series,
    strategy_exit_price_column: str | None,
) -> bool:
    """Return True when the prepared strategy would exit intrabar on this candle."""
    if not strategy_exit_price_column or not bool(row.get("exit_signal", False)):
        return False

    raw_exit_level = pd.to_numeric(
        pd.Series([row.get(strategy_exit_price_column)]),
        errors="coerce",
    ).iloc[0]
    if pd.isna(raw_exit_level):
        return False

    exit_level = float(raw_exit_level)
    current_open = float(row["open"])
    current_low = float(row["low"])
    return current_open <= exit_level or current_low <= exit_level
