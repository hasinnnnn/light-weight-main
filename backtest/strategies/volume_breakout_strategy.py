from __future__ import annotations

from typing import Any

import pandas as pd

from backtest.config import get_default_volume_breakout_params
from .base_strategy import StrategyPreparation


def _normalize_source_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare one OHLCV dataframe for volume-breakout analysis."""
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    prepared = frame[["time", "open", "high", "low", "close", "volume"]].copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared["volume"] = prepared["volume"].fillna(0.0)
    prepared = prepared.dropna(subset=["time", "open", "high", "low", "close"])
    prepared = prepared.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    return prepared.reset_index(drop=True)



def _normalize_volume_breakout_params(raw_params: dict[str, Any] | None = None) -> dict[str, float | int]:
    """Convert one raw parameter dictionary into safe volume-breakout values."""
    defaults = get_default_volume_breakout_params()
    raw_params = raw_params or {}

    def _coerce_int(name: str, minimum: int) -> int:
        try:
            value = int(raw_params.get(name, defaults[name]))
        except (TypeError, ValueError):
            value = int(defaults[name])
        return max(value, minimum)

    def _coerce_float(name: str, minimum: float) -> float:
        try:
            value = float(raw_params.get(name, defaults[name]))
        except (TypeError, ValueError):
            value = float(defaults[name])
        return max(value, minimum)

    return {
        "consolidation_bars": _coerce_int("consolidation_bars", 3),
        "max_consolidation_range_pct": _coerce_float("max_consolidation_range_pct", 0.1),
        "volume_ma_period": _coerce_int("volume_ma_period", 3),
        "consolidation_volume_ratio_max": _coerce_float("consolidation_volume_ratio_max", 0.1),
        "breakout_volume_ratio_min": _coerce_float("breakout_volume_ratio_min", 1.0),
        "breakout_buffer_pct": _coerce_float("breakout_buffer_pct", 0.0),
        "exit_after_bars": _coerce_int("exit_after_bars", 1),
    }



def build_volume_breakout_analysis(
    frame: pd.DataFrame,
    params: dict[str, Any] | None,
) -> pd.DataFrame:
    """Build one analysis frame for the low-volume consolidation breakout strategy."""
    prepared = _normalize_source_frame(frame)
    if prepared.empty:
        return prepared

    normalized_params = _normalize_volume_breakout_params(params)
    consolidation_bars = int(normalized_params["consolidation_bars"])
    volume_ma_period = int(normalized_params["volume_ma_period"])
    max_consolidation_range_pct = float(normalized_params["max_consolidation_range_pct"])
    consolidation_volume_ratio_max = float(normalized_params["consolidation_volume_ratio_max"])
    breakout_volume_ratio_min = float(normalized_params["breakout_volume_ratio_min"])
    breakout_buffer_rate = float(normalized_params["breakout_buffer_pct"]) / 100.0
    exit_after_bars = int(normalized_params["exit_after_bars"])

    row_index = pd.Series(range(len(prepared)), index=prepared.index, dtype="int64")

    prepared["zone_top"] = prepared["high"].shift(1).rolling(
        window=consolidation_bars,
        min_periods=consolidation_bars,
    ).max()
    prepared["zone_bottom"] = prepared["low"].shift(1).rolling(
        window=consolidation_bars,
        min_periods=consolidation_bars,
    ).min()
    prepared["consolidation_avg_volume"] = prepared["volume"].shift(1).rolling(
        window=consolidation_bars,
        min_periods=consolidation_bars,
    ).mean()
    prepared["reference_volume"] = prepared["volume"].shift(1).rolling(
        window=volume_ma_period,
        min_periods=volume_ma_period,
    ).mean()

    safe_zone_bottom = prepared["zone_bottom"].replace(0, pd.NA)
    safe_reference_volume = prepared["reference_volume"].replace(0, pd.NA)
    prepared["consolidation_range_pct"] = (
        prepared["zone_top"].sub(prepared["zone_bottom"]).div(safe_zone_bottom) * 100.0
    )
    prepared["consolidation_volume_ratio"] = prepared["consolidation_avg_volume"].div(safe_reference_volume)
    prepared["breakout_volume_ratio"] = prepared["volume"].div(safe_reference_volume)
    prepared["breakout_level"] = prepared["zone_top"] * (1.0 + breakout_buffer_rate)

    prepared["narrow_consolidation"] = prepared["consolidation_range_pct"].le(max_consolidation_range_pct)
    prepared["low_volume_consolidation"] = prepared["consolidation_volume_ratio"].le(
        consolidation_volume_ratio_max
    )
    prepared["indicator_ready"] = (
        prepared["zone_top"].notna()
        & prepared["zone_bottom"].notna()
        & safe_reference_volume.notna()
    )
    prepared["valid_consolidation"] = (
        prepared["indicator_ready"]
        & prepared["narrow_consolidation"].fillna(False)
        & prepared["low_volume_consolidation"].fillna(False)
    )

    previous_close = prepared["close"].shift(1)
    prepared["breakout_close"] = prepared["close"].gt(prepared["breakout_level"])
    prepared["volume_expansion"] = prepared["breakout_volume_ratio"].ge(breakout_volume_ratio_min)
    prepared["first_breakout_close"] = previous_close.le(prepared["zone_top"])

    prepared["entry_signal"] = (
        prepared["valid_consolidation"]
        & prepared["breakout_close"].fillna(False)
        & prepared["volume_expansion"].fillna(False)
        & prepared["first_breakout_close"].fillna(False)
    )

    prepared["consolidation_start_index"] = (row_index - consolidation_bars).where(
        prepared["valid_consolidation"]
    )
    prepared["consolidation_end_index"] = (row_index - 1).where(prepared["valid_consolidation"])

    breakout_sequence = prepared["entry_signal"].astype(int).cumsum()
    prepared["bars_since_breakout"] = (
        prepared.groupby(breakout_sequence, sort=False).cumcount().where(breakout_sequence.gt(0))
    )
    prepared["active_breakout_level"] = (
        prepared["zone_top"].where(prepared["entry_signal"]).ffill().where(breakout_sequence.gt(0))
    )
    prepared["exit_signal"] = breakout_sequence.gt(0) & (
        prepared["close"].lt(prepared["active_breakout_level"])
        | prepared["bars_since_breakout"].ge(exit_after_bars).fillna(False)
    )

    prepared["ongoing_consolidation"] = (
        prepared["valid_consolidation"]
        & prepared["close"].le(prepared["breakout_level"]).fillna(False)
        & ~prepared["entry_signal"]
    )
    return prepared



def _build_low_volume_overlay(zone_frame: pd.DataFrame) -> dict[str, float]:
    """Return the panel-volume range used to highlight low volume during consolidation."""
    if zone_frame is None or zone_frame.empty:
        return {
            "low_volume_top": 1.0,
            "low_volume_bottom": 0.0,
            "low_volume_label_value": 1.08,
        }

    volume_values = pd.to_numeric(zone_frame["volume"], errors="coerce").fillna(0.0)
    reference_values = pd.to_numeric(zone_frame.get("reference_volume"), errors="coerce").dropna()
    top_value = max(
        float(volume_values.max()) if not volume_values.empty else 0.0,
        float(reference_values.max()) if not reference_values.empty else 0.0,
        1.0,
    )
    return {
        "low_volume_top": top_value * 1.05,
        "low_volume_bottom": 0.0,
        "low_volume_label_value": top_value * 1.08,
    }


def _build_watch_summary(
    prepared: pd.DataFrame,
    normalized_params: dict[str, float | int],
) -> dict[str, Any] | None:
    """Return the current consolidation zone when price is still compressing."""
    consolidation_bars = int(normalized_params["consolidation_bars"])
    volume_ma_period = int(normalized_params["volume_ma_period"])
    max_consolidation_range_pct = float(normalized_params["max_consolidation_range_pct"])
    consolidation_volume_ratio_max = float(normalized_params["consolidation_volume_ratio_max"])
    breakout_buffer_rate = float(normalized_params["breakout_buffer_pct"]) / 100.0

    if len(prepared) < max(consolidation_bars, volume_ma_period):
        return None

    latest_window = prepared.tail(consolidation_bars).copy()
    zone_top = float(latest_window["high"].max())
    zone_bottom = float(latest_window["low"].min())
    if zone_bottom <= 0:
        return None

    range_pct = ((zone_top - zone_bottom) / zone_bottom) * 100.0
    reference_volume = float(prepared["volume"].tail(volume_ma_period).mean())
    if reference_volume <= 0:
        return None

    consolidation_avg_volume = float(latest_window["volume"].mean())
    consolidation_volume_ratio = consolidation_avg_volume / reference_volume
    latest_close = float(prepared["close"].iloc[-1])
    breakout_level = zone_top * (1.0 + breakout_buffer_rate)

    if range_pct > max_consolidation_range_pct:
        return None
    if consolidation_volume_ratio > consolidation_volume_ratio_max:
        return None
    if latest_close > breakout_level:
        return None

    start_index = max(len(prepared) - consolidation_bars, 0)
    end_index = len(prepared) - 1
    label_index = start_index + ((end_index - start_index) // 2)
    zone_height = max(zone_top - zone_bottom, abs(zone_top) * 0.004, 0.01)
    zone_frame = prepared.iloc[start_index : end_index + 1].copy()
    return {
        "status": "watch",
        "status_label": "Masih konsolidasi",
        "start_time": prepared.iloc[start_index]["time"],
        "end_time": prepared.iloc[end_index]["time"],
        "label_time": prepared.iloc[label_index]["time"],
        "label_price": zone_top + (zone_height * 0.25),
        "zone_top": zone_top,
        "zone_bottom": zone_bottom,
        "breakout_time": None,
        "breakout_label_price": None,
        "breakout_volume_ratio": None,
        "consolidation_volume_ratio": consolidation_volume_ratio,
        **_build_low_volume_overlay(zone_frame),
    }



def summarize_volume_breakout_zone(
    frame: pd.DataFrame,
    params: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Return the latest breakout zone, or the current watch zone when no breakout exists."""
    normalized_params = _normalize_volume_breakout_params(params)
    prepared = build_volume_breakout_analysis(frame, normalized_params)
    if prepared.empty:
        return None

    watch_summary = _build_watch_summary(prepared, normalized_params)

    breakout_rows = prepared.loc[prepared["entry_signal"]]
    if breakout_rows.empty:
        return watch_summary

    breakout_row = breakout_rows.iloc[-1]
    breakout_index = int(breakout_row.name)
    start_index = int(breakout_row["consolidation_start_index"])
    end_index = int(breakout_row["consolidation_end_index"])
    if start_index < 0 or end_index < start_index:
        return watch_summary

    label_index = start_index + ((end_index - start_index) // 2)
    zone_top = float(breakout_row["zone_top"])
    zone_bottom = float(breakout_row["zone_bottom"])
    breakout_close = float(breakout_row["close"])
    zone_height = max(zone_top - zone_bottom, abs(zone_top) * 0.004, 0.01)
    zone_frame = prepared.iloc[start_index : end_index + 1].copy()
    return {
        "status": "breakout",
        "status_label": "Breakout volume kuat",
        "start_time": prepared.iloc[start_index]["time"],
        "end_time": prepared.iloc[end_index]["time"],
        "label_time": prepared.iloc[label_index]["time"],
        "label_price": zone_top + (zone_height * 0.25),
        "zone_top": zone_top,
        "zone_bottom": zone_bottom,
        "breakout_time": prepared.iloc[breakout_index]["time"],
        "breakout_label_price": max(zone_top, breakout_close) + (zone_height * 0.35),
        "breakout_volume_ratio": float(breakout_row["breakout_volume_ratio"]),
        "consolidation_volume_ratio": float(breakout_row["consolidation_volume_ratio"]),
        **_build_low_volume_overlay(zone_frame),
    }



def prepare_volume_breakout_strategy(
    frame: pd.DataFrame,
    params: dict[str, Any] | None,
) -> StrategyPreparation:
    """Prepare the low-volume consolidation breakout strategy for the engine."""
    normalized_params = _normalize_volume_breakout_params(params)
    prepared = build_volume_breakout_analysis(frame, normalized_params)
    consolidation_bars = int(normalized_params["consolidation_bars"])
    volume_ma_period = int(normalized_params["volume_ma_period"])
    breakout_volume_ratio_min = float(normalized_params["breakout_volume_ratio_min"])
    exit_after_bars = int(normalized_params["exit_after_bars"])

    return StrategyPreparation(
        frame=prepared,
        warmup_bars=max(consolidation_bars + 1, volume_ma_period + 1),
        entry_rule_summary=(
            "Buy saat close breakout di atas area konsolidasi dengan volume rendah sebelumnya, "
            f"lalu volume breakout minimal {breakout_volume_ratio_min:.2f}x rata-rata volume referensi."
        ),
        exit_rule_summary=(
            "Exit saat close gagal bertahan di atas batas atas konsolidasi "
            f"atau setelah {exit_after_bars} bar sejak breakout."
        ),
    )




