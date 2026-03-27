from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_core import (
    CANDLE_PATTERN_COLORS,
    CHART_PATTERN_COLORS,
    _indicator_colors,
    _with_alpha,
)
from indicators.candle_patterns import detect_candle_patterns
from indicators.chart_patterns import detect_chart_patterns
from charts.renderers_parts.common import _render_text_marker_series


def render_candle_patterns(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render detected candle-pattern labels directly on the main chart."""
    colors = _indicator_colors(indicator)
    events = detect_candle_patterns(data, indicator.get("params") or {})
    if events.empty:
        return

    marker_points: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    series_name = "Candle Pattern"
    for row in events.itertuples(index=False):
        direction = str(row.direction)
        marker_points.append({"time": row.time, series_name: float(row.price)})
        markers.append(
            {
                "time": row.time,
                "position": str(row.position),
                "shape": "square",
                "color": colors.get(direction, CANDLE_PATTERN_COLORS.get(direction, "#f8fafc")),
                "text": str(row.short_label),
            }
        )

    _render_text_marker_series(chart, series_name, marker_points, markers)



def render_chart_patterns(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render detected chart patterns as guide lines and compact labels."""
    colors = _indicator_colors(indicator)
    patterns = detect_chart_patterns(data, indicator.get("params") or {})
    if not patterns:
        return

    marker_points: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    series_name = "Chart Pattern"
    line_base_color = colors.get("line", CHART_PATTERN_COLORS["line"])

    for pattern in patterns:
        direction = str(pattern.get("direction") or "neutral")
        tone_color = colors.get(direction, CHART_PATTERN_COLORS.get(direction, line_base_color))
        for point_start, point_end in zip(pattern.get("points") or [], (pattern.get("points") or [])[1:]):
            chart.trend_line(
                start_time=point_start["time"],
                start_value=float(point_start["price"]),
                end_time=point_end["time"],
                end_value=float(point_end["price"]),
                line_color=_with_alpha(line_base_color, 0.72),
                width=2,
                style="solid",
            )
        for line in pattern.get("lines") or []:
            chart.trend_line(
                start_time=line["start_time"],
                start_value=float(line["start_value"]),
                end_time=line["end_time"],
                end_value=float(line["end_value"]),
                line_color=_with_alpha(line_base_color, 0.96),
                width=2,
                style="solid",
            )

        marker_points.append({"time": pattern["label_time"], series_name: float(pattern["label_price"])} )
        markers.append(
            {
                "time": pattern["label_time"],
                "position": "below" if direction == "bullish" else "above",
                "shape": "square",
                "color": tone_color,
                "text": str(pattern["short_label"]),
            }
        )

    _render_text_marker_series(chart, series_name, marker_points, markers)


__all__ = ["render_candle_patterns", "render_chart_patterns"]

