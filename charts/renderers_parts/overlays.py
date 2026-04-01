from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.moving_averages import (
    build_cross_moving_average_dataframe as _build_cross_moving_average_dataframe,
    build_moving_average_dataframe as _build_moving_average_dataframe,
    build_pullback_moving_average_trade_markers as _build_pullback_moving_average_trade_markers,
)
from charts.chart_core import _build_cross_markers, _indicator_colors, _indicator_key, _indicator_params
from charts.renderers_parts.common import _overlay_series_specs
from charts.renderers_parts.overlay_lines import (
    render_bollinger_bands,
    render_fibonacci_levels,
    render_parabolic_sar,
    render_pivot_point_standard,
    render_vwap,
)
from charts.renderers_parts.overlay_patterns import render_candle_patterns, render_chart_patterns
from charts.renderers_parts.overlay_structures import (
    render_auto_trendline,
    render_consolidation_areas,
    render_major_trendline,
    render_nearest_support_resistance,
    render_strong_support_resistance,
    render_volume_breakout_zone,
)



def _render_overlay_indicator(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> None:
    """Render one overlay indicator into the main price chart."""
    indicator_key = _indicator_key(indicator)
    indicator_source = str(indicator.get("source") or "").strip().lower()
    colors = _indicator_colors(indicator)
    if indicator_key == "BOLLINGER_BANDS":
        render_bollinger_bands(chart, data, indicator)
        return
    if indicator_key == "VWAP":
        render_vwap(chart, data, indicator)
        return
    if indicator_key == "PARABOLIC_SAR":
        render_parabolic_sar(chart, data, indicator)
        return
    if indicator_key == "CANDLE_PATTERN":
        render_candle_patterns(chart, data, indicator)
        return
    if indicator_key == "CHART_PATTERN":
        render_chart_patterns(chart, data, indicator)
        return
    if indicator_key == "CONSOLIDATION_AREA":
        render_consolidation_areas(chart, data, indicator)
        return
    if indicator_key == "VOLUME_BREAKOUT_ZONE":
        render_volume_breakout_zone(chart, data, indicator)
        return
    if indicator_key == "TRENDLINE":
        render_auto_trendline(chart, data, indicator)
        return
    if indicator_key == "MAJOR_TRENDLINE":
        render_major_trendline(chart, data, indicator, interval_label)
        return
    if indicator_key == "NEAREST_SUPPORT_RESISTANCE":
        render_nearest_support_resistance(chart, data, indicator)
        return
    if indicator_key == "STRONG_SUPPORT_RESISTANCE":
        render_strong_support_resistance(chart, data, indicator, interval_label)
        return
    if indicator_key == "FIBONACCI":
        render_fibonacci_levels(chart, data, indicator)
        return
    if indicator_key == "PIVOT_POINT_STANDARD":
        render_pivot_point_standard(chart, data, indicator)
        return

    rendered_lines: list[Any] = []
    for series_spec in _overlay_series_specs(indicator):
        line_frame = _build_moving_average_dataframe(
            data=data,
            length=int(series_spec["length"]),
            line_name=str(series_spec["name"]),
            method=str(series_spec["method"]),
        )
        if line_frame.empty:
            continue

        line = chart.create_line(
            name=str(series_spec["name"]),
            color=str(series_spec["color"]),
            width=2,
            price_line=False,
            price_label=False,
        )
        line.set(line_frame)
        rendered_lines.append(line)

    if indicator_key in {"EMA", "MA"} and rendered_lines and indicator_source not in {"backtest", "backtest_helper"}:
        params = _indicator_params(indicator)
        pullback_markers = _build_pullback_moving_average_trade_markers(
            data=data,
            length=int(params.get("length", 10 if indicator_key == "EMA" else 20)),
            method="ema" if indicator_key == "EMA" else "ma",
            label="EMA" if indicator_key == "EMA" else "SMA",
        )
        if pullback_markers:
            rendered_lines[0].marker_list(pullback_markers)

    if indicator_key in {"EMA_CROSS", "MA_CROSS"} and len(rendered_lines) >= 1:
        params = _indicator_params(indicator)
        cross_frame = _build_cross_moving_average_dataframe(
            data=data,
            fast_length=params.get("fast_length", 9 if indicator_key == "EMA_CROSS" else 20),
            slow_length=params.get("slow_length", 21 if indicator_key == "EMA_CROSS" else 50),
            method="ema" if indicator_key == "EMA_CROSS" else "ma",
        )
        cross_markers = _build_cross_markers(
            series_frame=cross_frame,
            fast_column="fast",
            slow_column="slow",
            color=colors.get("cross", "#f8fafc"),
        )
        if cross_markers:
            rendered_lines[0].marker_list(cross_markers)


__all__ = ["_render_overlay_indicator"]
