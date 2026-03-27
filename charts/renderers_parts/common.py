from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.moving_averages import (
    build_moving_average_overlay_series_specs as _build_moving_average_overlay_series_specs,
)
from charts.chart_core import (
    BOLLINGER_COLORS,
    EMA_COLORS,
    MA_COLORS,
    VWAP_COLOR,
    _indicator_colors,
    _indicator_key,
    _indicator_params,
)

def _overlay_series_specs(indicator: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the line-rendering instructions for overlay indicators."""
    indicator_key = _indicator_key(indicator)
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)

    moving_average_specs = _build_moving_average_overlay_series_specs(
        indicator_key=indicator_key,
        params=params,
        colors=colors,
        ema_colors=EMA_COLORS,
        ma_colors=MA_COLORS,
    )
    if moving_average_specs:
        return moving_average_specs

    if indicator_key == "BOLLINGER_BANDS":
        length = params.get("length", 20)
        return [
            {
                "method": "bollinger",
                "length": length,
                "name": f"BB Upper {length}",
                "color": colors.get("upper", BOLLINGER_COLORS["upper"]),
            },
            {
                "method": "bollinger",
                "length": length,
                "name": f"BB Basis {length}",
                "color": colors.get("basis", BOLLINGER_COLORS["basis"]),
            },
            {
                "method": "bollinger",
                "length": length,
                "name": f"BB Lower {length}",
                "color": colors.get("lower", BOLLINGER_COLORS["lower"]),
            },
        ]
    if indicator_key == "VWAP":
        return [
            {
                "method": "vwap",
                "name": "VWAP",
                "color": colors.get("line", VWAP_COLOR),
            }
        ]
    return []


def _prepare_marker_series_frame(
    marker_points: list[dict[str, Any]],
    series_name: str,
) -> pd.DataFrame:
    """Build one stable marker data frame with unique sorted timestamps."""
    marker_frame = pd.DataFrame(marker_points)
    if marker_frame.empty or "time" not in marker_frame or series_name not in marker_frame:
        return pd.DataFrame(columns=["time", series_name])

    marker_frame = marker_frame[["time", series_name]].copy()
    marker_frame["time"] = pd.to_datetime(marker_frame["time"], errors="coerce")
    marker_frame = marker_frame.dropna(subset=["time", series_name])
    if marker_frame.empty:
        return pd.DataFrame(columns=["time", series_name])

    marker_frame = marker_frame.sort_values("time")
    marker_frame = marker_frame.drop_duplicates(subset=["time"], keep="last")
    return marker_frame.reset_index(drop=True)




def _ensure_marker_series_interval(chart: Any, marker_series: Any, marker_frame: pd.DataFrame) -> None:
    """Prevent zero-interval marker series when labels share the same candle time."""
    current_interval = float(getattr(marker_series, "_interval", 0) or 0)
    if current_interval > 0:
        return

    chart_interval = float(getattr(chart, "_interval", 0) or 0)
    if chart_interval > 0:
        marker_series._interval = chart_interval
        return

    if len(marker_frame) >= 2:
        unique_times = pd.to_datetime(marker_frame["time"], errors="coerce").dropna().drop_duplicates().sort_values()
        if len(unique_times) >= 2:
            time_deltas = unique_times.diff().dropna()
            positive_deltas = time_deltas[time_deltas > pd.Timedelta(0)]
            if not positive_deltas.empty:
                marker_series._interval = max(float(positive_deltas.iloc[0].total_seconds()), 1.0)
                return

    marker_series._interval = 1




def _render_text_marker_series(
    chart: Any,
    series_name: str,
    marker_points: list[dict[str, Any]],
    markers: list[dict[str, Any]],
) -> None:
    """Render one invisible line series that only serves marker labels."""
    if not marker_points or not markers:
        return

    marker_frame = _prepare_marker_series_frame(marker_points, series_name)
    if marker_frame.empty:
        return

    marker_series = chart.create_line(
        name="",
        color="rgba(0, 0, 0, 0)",
        width=1,
        price_line=False,
        price_label=False,
    )
    marker_series.set(marker_frame)
    _ensure_marker_series_interval(chart, marker_series, marker_frame)
    marker_series.marker_list(markers)
    marker_series.run_script(
        f"""
        {marker_series.id}.series.applyOptions({{
            lineVisible: false,
            pointMarkersVisible: false,
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            priceLineVisible: false
        }})
        """
    )




__all__ = [
    "_overlay_series_specs",
    "_prepare_marker_series_frame",
    "_ensure_marker_series_interval",
    "_render_text_marker_series",
]
