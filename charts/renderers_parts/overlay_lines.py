from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.fibonacci import FIBONACCI_FILL_ALPHAS, FIBONACCI_MONOCHROME_DEFAULT, build_fibonacci_analysis
from charts.chart_core import (
    BOLLINGER_COLORS,
    PARABOLIC_SAR_COLOR,
    PIVOT_LEVELS,
    VWAP_COLOR,
    _build_parabolic_sar_dataframe,
    _indicator_colors,
    _indicator_params,
    _split_parabolic_sar_segments,
    _with_alpha,
)
from indicators.bollinger_bands import build_bollinger_bands_dataframe as _build_bollinger_bands_dataframe
from indicators.pivot_points import build_standard_pivot_levels as _build_standard_pivot_levels
from indicators.vwap import build_vwap_dataframe as _build_vwap_dataframe


def render_bollinger_bands(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Bollinger Bands on the main chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    length = params.get("length", 20)
    deviation = params.get("deviation", 2)
    bollinger_frame = _build_bollinger_bands_dataframe(data, length, deviation)
    if bollinger_frame.empty:
        return

    for line_name, color in [
        (f"BB Upper {length}", colors.get("upper", BOLLINGER_COLORS["upper"])),
        (f"BB Basis {length}", colors.get("basis", BOLLINGER_COLORS["basis"])),
        (f"BB Lower {length}", colors.get("lower", BOLLINGER_COLORS["lower"])),
    ]:
        line = chart.create_line(
            name=line_name,
            color=color,
            width=2,
            price_line=False,
            price_label=False,
        )
        line.set(bollinger_frame[["time", line_name]])



def render_vwap(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render VWAP on the main chart."""
    colors = _indicator_colors(indicator)
    vwap_frame = _build_vwap_dataframe(data)
    if vwap_frame.empty:
        return

    line = chart.create_line(
        name="VWAP",
        color=colors.get("line", VWAP_COLOR),
        width=2,
        price_line=False,
        price_label=False,
    )
    line.set(vwap_frame)



def render_parabolic_sar(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Parabolic SAR on the main chart."""
    colors = _indicator_colors(indicator)
    params = _indicator_params(indicator)
    acceleration_pct = max(params.get("acceleration_pct", 2), 1) / 100.0
    max_acceleration_pct = max(params.get("max_acceleration_pct", 20), int(round(acceleration_pct * 100))) / 100.0
    psar_frame = _build_parabolic_sar_dataframe(
        data,
        acceleration=acceleration_pct,
        max_acceleration=max_acceleration_pct,
    )
    if psar_frame.empty:
        return

    psar_color = colors.get("line", PARABOLIC_SAR_COLOR)
    psar_segments = _split_parabolic_sar_segments(psar_frame)
    for index, segment_frame in enumerate(psar_segments):
        series_name = "Parabolic SAR" if index == 0 else ""
        sar_line = chart.create_line(
            name="",
            color=psar_color,
            width=1,
            price_line=False,
            price_label=False,
        )
        if series_name:
            sar_line.set(segment_frame)
        else:
            sar_line.set(segment_frame.rename(columns={"Parabolic SAR": "value"}))
        sar_line.run_script(
            f"""
            {sar_line.id}.series.applyOptions({{
                lineVisible: false,
                pointMarkersVisible: true,
                pointMarkersRadius: 2,
                crosshairMarkerVisible: false,
                lastValueVisible: false,
                priceLineVisible: false
            }})
            """
        )



def render_fibonacci_levels(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Fibonacci retracement levels on the main chart."""
    analysis = build_fibonacci_analysis(
        data=data,
        params=_indicator_params(indicator),
        colors=_indicator_colors(indicator),
    )
    if analysis is None:
        return

    level_configs = analysis["level_configs"]
    line_override = str(analysis.get("line_override") or "")
    chart.trend_line(
        start_time=analysis["swing_start_time"],
        start_value=float(analysis["swing_start_price"]),
        end_time=analysis["swing_end_time"],
        end_value=float(analysis["swing_end_price"]),
        line_color=_with_alpha(line_override or FIBONACCI_MONOCHROME_DEFAULT, 0.95),
        width=2,
        style="dashed",
    )

    for index in range(1, len(level_configs)):
        previous_level = level_configs[index - 1]
        current_level = level_configs[index]
        band_color = line_override if analysis["use_monochrome"] else current_level["color"]
        band_alpha = FIBONACCI_FILL_ALPHAS[min(index - 1, len(FIBONACCI_FILL_ALPHAS) - 1)]
        chart.box(
            start_time=analysis["render_start_time"],
            start_value=max(previous_level["price"], current_level["price"]),
            end_time=analysis["render_end_time"],
            end_value=min(previous_level["price"], current_level["price"]),
            color="rgba(0, 0, 0, 0)",
            fill_color=_with_alpha(band_color, band_alpha),
            width=1,
            style="solid",
        )

    for level in level_configs:
        chart.trend_line(
            start_time=analysis["render_start_time"],
            start_value=level["price"],
            end_time=analysis["render_end_time"],
            end_value=level["price"],
            line_color=level["color"],
            width=1,
            style="solid",
        )
        chart.horizontal_line(
            price=float(level["price"]),
            color=_with_alpha(level["color"], 0.18),
            width=1,
            style="solid",
            text=level["label"],
            axis_label_visible=False,
        )



def render_pivot_point_standard(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render standard pivot point levels from the previous completed candle."""
    line_color = _indicator_colors(indicator).get("line")
    levels = _build_standard_pivot_levels(data)
    if levels is None:
        return

    for label, color in PIVOT_LEVELS:
        chart.horizontal_line(
            price=levels[label],
            color=line_color or color,
            width=1,
            style="dashed",
            text=label,
            axis_label_visible=False,
        )


__all__ = [
    "render_bollinger_bands",
    "render_fibonacci_levels",
    "render_parabolic_sar",
    "render_pivot_point_standard",
    "render_vwap",
]

