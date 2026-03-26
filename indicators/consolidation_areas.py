from __future__ import annotations

from typing import Any

import pandas as pd

from backtest.config import get_default_volume_breakout_params
from strategies.volume_breakout_strategy import build_volume_breakout_analysis


def get_default_consolidation_area_params() -> dict[str, Any]:
    """Return the default parameters for the consolidation-area indicator."""
    defaults = get_default_volume_breakout_params()
    return {
        "lookback": 220,
        "consolidation_bars": int(defaults["consolidation_bars"]),
        "max_consolidation_range_pct": float(defaults["max_consolidation_range_pct"]),
        "volume_ma_period": int(defaults["volume_ma_period"]),
        "consolidation_volume_ratio_max": float(defaults["consolidation_volume_ratio_max"]),
        "max_zones": 6,
    }


def normalize_consolidation_area_params(raw_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize raw consolidation-area parameters into safe numeric values."""
    defaults = get_default_consolidation_area_params()
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

    normalized = {
        "lookback": _coerce_int("lookback", 40),
        "consolidation_bars": _coerce_int("consolidation_bars", 3),
        "max_consolidation_range_pct": _coerce_float("max_consolidation_range_pct", 0.1),
        "volume_ma_period": _coerce_int("volume_ma_period", 3),
        "consolidation_volume_ratio_max": _coerce_float("consolidation_volume_ratio_max", 0.1),
        "max_zones": _coerce_int("max_zones", 1),
    }
    normalized["max_zones"] = min(normalized["max_zones"], 12)
    return normalized


def _build_analysis_frame(
    frame: pd.DataFrame,
    normalized_params: dict[str, Any],
) -> tuple[pd.DataFrame, int]:
    """Build the analysis dataframe and the source offset used for index conversion."""
    if frame is None or frame.empty:
        return pd.DataFrame(), 0

    lookback = int(normalized_params["lookback"])
    padding = max(
        int(normalized_params["consolidation_bars"]),
        int(normalized_params["volume_ma_period"]),
    ) + 12
    source_frame = frame.tail(lookback + padding).copy()

    strategy_params = get_default_volume_breakout_params()
    strategy_params.update(
        {
            "consolidation_bars": int(normalized_params["consolidation_bars"]),
            "max_consolidation_range_pct": float(normalized_params["max_consolidation_range_pct"]),
            "volume_ma_period": int(normalized_params["volume_ma_period"]),
            "consolidation_volume_ratio_max": float(normalized_params["consolidation_volume_ratio_max"]),
        }
    )

    prepared = build_volume_breakout_analysis(source_frame, strategy_params)
    if prepared.empty:
        return prepared, 0

    source_offset = max(len(prepared) - lookback, 0)
    analysis = prepared.iloc[source_offset:].copy().reset_index(drop=True)
    return analysis, source_offset


def detect_consolidation_areas(
    frame: pd.DataFrame,
    raw_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return recent consolidation zones that match the same logic as the breakout backtest."""
    normalized_params = normalize_consolidation_area_params(raw_params)
    analysis, source_offset = _build_analysis_frame(frame, normalized_params)
    if analysis.empty:
        return []

    valid_mask = analysis["valid_consolidation"].fillna(False)
    if not bool(valid_mask.any()):
        return []

    group_ids = valid_mask.ne(valid_mask.shift(fill_value=False)).cumsum()
    areas: list[dict[str, Any]] = []
    seen_signatures: set[tuple[Any, Any, float, float]] = set()

    for group_id in group_ids[valid_mask].drop_duplicates().tolist():
        group_frame = analysis.loc[group_ids.eq(group_id)].copy()
        start_candidates = pd.to_numeric(group_frame["consolidation_start_index"], errors="coerce").dropna()
        end_candidates = pd.to_numeric(group_frame["consolidation_end_index"], errors="coerce").dropna()
        if start_candidates.empty or end_candidates.empty:
            continue

        start_index = max(int(start_candidates.min() - source_offset), 0)
        end_index = min(int(end_candidates.max() - source_offset), len(analysis) - 1)
        if end_index < start_index:
            continue

        zone_window = analysis.iloc[start_index : end_index + 1].copy()
        if zone_window.empty:
            continue

        zone_top = float(zone_window["high"].max())
        zone_bottom = float(zone_window["low"].min())
        if pd.isna(zone_top) or pd.isna(zone_bottom):
            continue

        signature = (
            zone_window.iloc[0]["time"],
            zone_window.iloc[-1]["time"],
            round(zone_top, 6),
            round(zone_bottom, 6),
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        breakout_rows = group_frame.loc[group_frame["entry_signal"].fillna(False)]
        if not breakout_rows.empty:
            status = "breakout"
            status_label = "Zona ini sudah breakout"
        elif int(group_frame.index.max()) == len(analysis) - 1:
            status = "active"
            status_label = "Harga masih bergerak di area konsolidasi ini"
        else:
            status = "completed"
            status_label = "Zona konsolidasi historis"

        label_index = start_index + ((end_index - start_index) // 2)
        zone_height = max(zone_top - zone_bottom, abs(zone_top) * 0.004, 0.01)
        volume_ratio_values = pd.to_numeric(group_frame["consolidation_volume_ratio"], errors="coerce").dropna()
        breakout_row = breakout_rows.iloc[-1] if not breakout_rows.empty else None
        breakout_volume_ratio = None
        breakout_time = None
        if breakout_row is not None:
            breakout_time = breakout_row["time"]
            breakout_volume_ratio_value = breakout_row.get("breakout_volume_ratio")
            if breakout_volume_ratio_value is not None and pd.notna(breakout_volume_ratio_value):
                breakout_volume_ratio = float(breakout_volume_ratio_value)

        range_pct = None
        if zone_bottom > 0:
            range_pct = ((zone_top - zone_bottom) / zone_bottom) * 100.0

        areas.append(
            {
                "start_time": zone_window.iloc[0]["time"],
                "end_time": zone_window.iloc[-1]["time"],
                "label_time": analysis.iloc[label_index]["time"],
                "label_price": zone_top + (zone_height * 0.25),
                "zone_top": zone_top,
                "zone_bottom": zone_bottom,
                "status": status,
                "status_label": status_label,
                "breakout_time": breakout_time,
                "breakout_volume_ratio": breakout_volume_ratio,
                "range_pct": range_pct,
                "consolidation_volume_ratio": (
                    float(volume_ratio_values.iloc[-1]) if not volume_ratio_values.empty else None
                ),
                "bar_count": int(len(zone_window)),
            }
        )

    areas.sort(key=lambda item: pd.to_datetime(item["end_time"], errors="coerce"))
    max_zones = int(normalized_params["max_zones"])
    if len(areas) > max_zones:
        areas = areas[-max_zones:]
    return areas


def summarize_consolidation_areas(
    frame: pd.DataFrame,
    raw_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the current summary for the consolidation-area indicator."""
    normalized_params = normalize_consolidation_area_params(raw_params)
    areas = detect_consolidation_areas(frame, normalized_params)
    latest_area = areas[-1] if areas else None
    active_area = next((area for area in reversed(areas) if area["status"] == "active"), None)
    latest_breakout_area = next((area for area in reversed(areas) if area["status"] == "breakout"), None)
    return {
        "areas": areas,
        "latest_area": latest_area,
        "active_area": active_area,
        "latest_breakout_area": latest_breakout_area,
        "total_areas": len(areas),
        "params": normalized_params,
    }
