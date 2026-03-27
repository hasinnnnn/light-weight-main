from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_analysis import (
    _build_auto_trendline_summaries,
    _build_major_trendline_summaries,
    _build_nearest_support_resistance_summary,
    _build_strong_support_resistance_summary,
)
from charts.chart_core import (
    CONSOLIDATION_AREA_ACTIVE_FILL_ALPHA,
    CONSOLIDATION_AREA_COLORS,
    CONSOLIDATION_AREA_FILL_ALPHA,
    NEAREST_SUPPORT_RESISTANCE_COLORS,
    NEAREST_SUPPORT_RESISTANCE_FILL_ALPHA,
    NEAREST_SUPPORT_RESISTANCE_LINE_ALPHA,
    STRONG_SUPPORT_RESISTANCE_COLORS,
    STRONG_SUPPORT_RESISTANCE_FILL_ALPHA,
    STRONG_SUPPORT_RESISTANCE_LINE_ALPHA,
    TRENDLINE_COLORS,
    VOLUME_BREAKOUT_BREAKOUT_COLOR,
    VOLUME_BREAKOUT_FILL_ALPHA,
    VOLUME_BREAKOUT_LOW_VOLUME_COLOR,
    VOLUME_BREAKOUT_ZONE_COLOR,
    _indicator_colors,
    _with_alpha,
)
from backtest.strategies.volume_breakout_strategy import summarize_volume_breakout_zone
from indicators.consolidation_areas import detect_consolidation_areas
from charts.renderers_parts.common import _render_text_marker_series


def render_volume_breakout_zone(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render one breakout-from-consolidation setup on price and volume panels."""
    colors = _indicator_colors(indicator)
    summary = summarize_volume_breakout_zone(data, indicator.get("params") or {})
    if summary is None:
        return

    zone_color = colors.get("zone", VOLUME_BREAKOUT_ZONE_COLOR)
    breakout_color = colors.get("breakout", VOLUME_BREAKOUT_BREAKOUT_COLOR)
    low_volume_color = colors.get("low_volume", VOLUME_BREAKOUT_LOW_VOLUME_COLOR)
    border_color = breakout_color if str(summary.get("status") or "") == "breakout" else zone_color

    chart.box(
        start_time=summary["start_time"],
        start_value=float(summary["zone_top"]),
        end_time=summary["end_time"],
        end_value=float(summary["zone_bottom"]),
        color=_with_alpha(border_color, 0.42),
        fill_color=_with_alpha(zone_color, VOLUME_BREAKOUT_FILL_ALPHA),
        width=1,
        style="solid",
    )
    chart.trend_line(
        start_time=summary["start_time"],
        start_value=float(summary["zone_top"]),
        end_time=summary["end_time"],
        end_value=float(summary["zone_top"]),
        line_color=_with_alpha(border_color, 0.95),
        width=2,
        style="solid",
    )
    chart.trend_line(
        start_time=summary["start_time"],
        start_value=float(summary["zone_bottom"]),
        end_time=summary["end_time"],
        end_value=float(summary["zone_bottom"]),
        line_color=_with_alpha(zone_color, 0.58),
        width=1,
        style="dashed",
    )

    label_points = [
        {
            "time": summary["label_time"],
            "Volume Breakout Zone": float(summary["label_price"]),
        }
    ]
    markers = [
        {
            "time": summary["label_time"],
            "position": "above",
            "shape": "square",
            "color": border_color,
            "text": "Area Konsolidasi",
        }
    ]

    breakout_time = summary.get("breakout_time")
    breakout_label_price = summary.get("breakout_label_price")
    if breakout_time is not None and breakout_label_price is not None:
        chart.trend_line(
            start_time=summary["end_time"],
            start_value=float(summary["zone_top"]),
            end_time=breakout_time,
            end_value=float(summary["zone_top"]),
            line_color=_with_alpha(breakout_color, 0.88),
            width=2,
            style="solid",
        )
        label_points.append(
            {
                "time": breakout_time,
                "Volume Breakout Zone": float(breakout_label_price),
            }
        )
        markers.append(
            {
                "time": breakout_time,
                "position": "above",
                "shape": "square",
                "color": breakout_color,
                "text": "Breakout",
            }
        )

    _render_text_marker_series(chart, "Volume Breakout Zone", label_points, markers)

    volume_scale_id = getattr(chart, "_volume_scale_id", None)
    low_volume_top = summary.get("low_volume_top")
    low_volume_bottom = summary.get("low_volume_bottom", 0.0)
    low_volume_label_value = summary.get("low_volume_label_value")
    if volume_scale_id is None or low_volume_top is None or pd.isna(low_volume_top):
        return

    low_volume_ceiling = float(low_volume_top)
    low_volume_label = (
        float(low_volume_label_value)
        if low_volume_label_value is not None and pd.notna(low_volume_label_value)
        else low_volume_ceiling
    )
    volume_overlay = chart.create_line(
        name="",
        color="rgba(0, 0, 0, 0)",
        width=1,
        price_line=False,
        price_label=False,
        price_scale_id=volume_scale_id,
    )
    volume_overlay.set(
        pd.DataFrame(
            [
                {
                    "time": summary["start_time"],
                    "Volume Breakout Low Volume": low_volume_ceiling,
                },
                {
                    "time": summary["label_time"],
                    "Volume Breakout Low Volume": low_volume_label,
                },
                {
                    "time": summary["end_time"],
                    "Volume Breakout Low Volume": low_volume_ceiling,
                },
            ]
        )
    )
    volume_overlay.box(
        start_time=summary["start_time"],
        start_value=low_volume_ceiling,
        end_time=summary["end_time"],
        end_value=float(low_volume_bottom),
        color=_with_alpha(low_volume_color, 0.42),
        fill_color=_with_alpha(low_volume_color, 0.20),
        width=1,
        style="solid",
    )
    volume_overlay.marker_list(
        [
            {
                "time": summary["label_time"],
                "position": "above",
                "shape": "square",
                "color": low_volume_color,
                "text": "Low Volume",
            }
        ]
    )
    volume_overlay.run_script(
        f"""
        {volume_overlay.id}.series.applyOptions({{
            lineVisible: false,
            pointMarkersVisible: false,
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            priceLineVisible: false
        }})
        """
    )



def render_consolidation_areas(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render multiple consolidation zones on the main chart."""
    colors = _indicator_colors(indicator)
    areas = detect_consolidation_areas(data, indicator.get("params") or {})
    if not areas:
        return

    marker_points: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    series_name = "Area Konsolidasi"

    for area in areas:
        status = str(area.get("status") or "completed")
        color_key = "active" if status == "active" else "zone"
        zone_color = colors.get(color_key, CONSOLIDATION_AREA_COLORS[color_key])
        fill_alpha = (
            CONSOLIDATION_AREA_ACTIVE_FILL_ALPHA
            if status == "active"
            else CONSOLIDATION_AREA_FILL_ALPHA
        )
        chart.box(
            start_time=area["start_time"],
            start_value=float(area["zone_top"]),
            end_time=area["end_time"],
            end_value=float(area["zone_bottom"]),
            color=_with_alpha(zone_color, 0.38),
            fill_color=_with_alpha(zone_color, fill_alpha),
            width=1,
            style="solid",
        )
        marker_points.append(
            {
                "time": area["label_time"],
                series_name: float(area["label_price"]),
            }
        )
        markers.append(
            {
                "time": area["label_time"],
                "position": "above",
                "shape": "square",
                "color": zone_color,
                "text": "Konsolidasi Aktif" if status == "active" else "Area Konsolidasi",
            }
        )

    _render_text_marker_series(chart, series_name, marker_points, markers)



def render_auto_trendline(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render multiple automatically detected minor trendlines near the latest candles."""
    colors = _indicator_colors(indicator)
    summary_bundle = _build_auto_trendline_summaries(data, indicator)
    if summary_bundle is None:
        return

    for index, trendline_summary in enumerate(summary_bundle["trendlines"]):
        direction = str(trendline_summary["direction"])
        chart.trend_line(
            start_time=trendline_summary["start_time"],
            start_value=trendline_summary["start_value"],
            end_time=trendline_summary["end_time"],
            end_value=trendline_summary["end_value"],
            line_color=colors.get(direction, TRENDLINE_COLORS[direction]),
            width=2 if index == 0 else 1,
            style="solid",
        )



def render_major_trendline(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> None:
    """Render multiple major higher-timeframe trendlines on the main chart."""
    colors = _indicator_colors(indicator)
    summary_bundle = _build_major_trendline_summaries(data, indicator, interval_label)
    if summary_bundle is None:
        return

    for index, trendline_summary in enumerate(summary_bundle["trendlines"]):
        direction = str(trendline_summary["direction"])
        chart.trend_line(
            start_time=trendline_summary["start_time"],
            start_value=trendline_summary["start_value"],
            end_time=trendline_summary["end_time"],
            end_value=trendline_summary["end_value"],
            line_color=colors.get(direction, TRENDLINE_COLORS[direction]),
            width=3 if index == 0 else 2,
            style="solid",
        )



def render_nearest_support_resistance(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> None:
    """Render the nearest support and resistance areas across the recent chart range."""
    colors = _indicator_colors(indicator)
    summary = _build_nearest_support_resistance_summary(data, indicator)
    if summary is None:
        return

    for direction, label in [("support", "Support"), ("resistance", "Resistance")]:
        level = summary.get(direction)
        if level is None:
            continue

        color = colors.get(direction, NEAREST_SUPPORT_RESISTANCE_COLORS[direction])
        chart.box(
            start_time=summary["start_time"],
            start_value=float(level["zone_top"]),
            end_time=summary["end_time"],
            end_value=float(level["zone_bottom"]),
            color=_with_alpha(color, 0.35),
            fill_color=_with_alpha(color, NEAREST_SUPPORT_RESISTANCE_FILL_ALPHA),
            width=1,
            style="solid",
        )
        chart.horizontal_line(
            price=float(level["price"]),
            color=_with_alpha(color, NEAREST_SUPPORT_RESISTANCE_LINE_ALPHA),
            width=2,
            style="solid",
            text=f"{label} x{int(level['bounces'])}",
            axis_label_visible=False,
        )



def render_strong_support_resistance(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> None:
    """Render strong support and resistance areas from repeated higher-timeframe tests."""
    colors = _indicator_colors(indicator)
    summary = _build_strong_support_resistance_summary(data, indicator, interval_label)
    if summary is None:
        return

    for direction, label in [("support", "Strong Support"), ("resistance", "Strong Resistance")]:
        level = summary.get(direction)
        if level is None:
            continue

        color = colors.get(direction, STRONG_SUPPORT_RESISTANCE_COLORS[direction])
        chart.box(
            start_time=summary["start_time"],
            start_value=float(level["zone_top"]),
            end_time=summary["end_time"],
            end_value=float(level["zone_bottom"]),
            color=_with_alpha(color, 0.42),
            fill_color=_with_alpha(color, STRONG_SUPPORT_RESISTANCE_FILL_ALPHA),
            width=1,
            style="solid",
        )
        chart.horizontal_line(
            price=float(level["price"]),
            color=_with_alpha(color, STRONG_SUPPORT_RESISTANCE_LINE_ALPHA),
            width=2,
            style="solid",
            text=(
                f"{label} x{int(level['bounces'])}"
                f" Vol {float(level['average_volume_ratio']):.2f}x"
            ),
            axis_label_visible=False,
        )


__all__ = [
    "render_auto_trendline",
    "render_consolidation_areas",
    "render_major_trendline",
    "render_nearest_support_resistance",
    "render_strong_support_resistance",
    "render_volume_breakout_zone",
]

