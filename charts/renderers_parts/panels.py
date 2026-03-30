from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_core import (
    ATR_COLOR,
    INDICATOR_CHART_HEIGHT,
    PRICE_OSCILLATOR_COLOR,
    STOCHASTIC_COLORS,
    _build_cross_markers,
    _format_indicator_title,
    _indicator_colors,
    _indicator_key,
    _indicator_params,
    _style_indicator_chart,
    build_streamlit_chart,
    build_streamlit_subchart,
)
from indicators.atr import build_atr_dataframe as _build_atr_dataframe
from indicators.macd import build_macd_dataframe as _build_macd_dataframe
from indicators.price_oscillator import build_price_oscillator_dataframe as _build_price_oscillator_dataframe
from indicators.rsi import build_rsi_dataframe as _build_rsi_dataframe
from indicators.stochastic import (
    build_stochastic_dataframe as _build_stochastic_dataframe,
    build_stochastic_rsi_dataframe as _build_stochastic_rsi_dataframe,
)


def _render_oscillator_reference_lines(chart: Any, frame: pd.DataFrame) -> None:
    """Render shared guide lines for oscillator panels as explicit line series."""
    if frame.empty or "time" not in frame.columns:
        return

    sorted_frame = frame.copy()
    sorted_frame["time"] = pd.to_datetime(sorted_frame["time"], errors="coerce")
    sorted_frame = sorted_frame.dropna(subset=["time"]).sort_values("time")
    if sorted_frame.empty:
        return

    start_time = sorted_frame.iloc[0]["time"]
    end_time = sorted_frame.iloc[-1]["time"]
    if start_time == end_time:
        return

    for level in [80, 60, 20]:
        guide_series = chart.create_line(
            name="",
            color="rgba(96, 165, 250, 0.72)",
            style="dotted",
            width=2,
            price_line=False,
            price_label=False,
        )
        guide_series.set(
            pd.DataFrame(
                [
                    {"time": start_time, "value": float(level)},
                    {"time": end_time, "value": float(level)},
                ]
            )
        )
        guide_series.run_script(
            f"""
            {guide_series.id}.series.applyOptions({{
                lineVisible: true,
                pointMarkersVisible: false,
                crosshairMarkerVisible: false,
                lastValueVisible: false,
                priceLineVisible: false,
                lineWidth: 2,
                color: 'rgba(96, 165, 250, 0.72)'
            }})
            """
        )


def _render_rsi_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render RSI into a dedicated chart."""
    window = _indicator_params(indicator).get("length", 14)
    colors = _indicator_colors(indicator)
    rsi_frame = _build_rsi_dataframe(data, window)
    if rsi_frame.empty:
        return

    line_name = f"RSI {window}"
    rsi_line = chart.create_line(
        name=line_name,
        color=colors.get("line", "#a78bfa"),
        width=2,
        price_line=False,
        price_label=True,
    )
    rsi_line.set(rsi_frame)
    _render_oscillator_reference_lines(chart, rsi_frame)



def _render_atr_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render ATR into a dedicated chart."""
    window = _indicator_params(indicator).get("length", 14)
    colors = _indicator_colors(indicator)
    atr_frame = _build_atr_dataframe(data, window)
    if atr_frame.empty:
        return

    line_name = f"ATR {window}"
    atr_line = chart.create_line(
        name=line_name,
        color=colors.get("line", ATR_COLOR),
        width=2,
        price_line=False,
        price_label=True,
    )
    atr_line.set(atr_frame)



def _render_price_oscillator_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Price Oscillator into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    oscillator_frame = _build_price_oscillator_dataframe(
        data=data,
        fast_window=params.get("fast_length", 12),
        slow_window=params.get("slow_length", 26),
    )
    if oscillator_frame.empty:
        return

    oscillator_line = chart.create_line(
        name="Price Oscillator",
        color=colors.get("line", PRICE_OSCILLATOR_COLOR),
        width=2,
        price_line=False,
        price_label=True,
    )
    oscillator_line.set(oscillator_frame)
    chart.horizontal_line(
        price=0,
        color="rgba(148, 163, 184, 0.45)",
        width=1,
        style="dashed",
        axis_label_visible=False,
    )



def _render_macd_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render MACD lines and histogram into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    macd_frame = _build_macd_dataframe(
        data=data,
        fast_window=params.get("fast_length", 12),
        slow_window=params.get("slow_length", 26),
        signal_window=params.get("signal_length", 9),
    )
    if macd_frame.empty:
        return

    histogram = chart.create_histogram(
        name="MACD Histogram",
        color="rgba(148, 163, 184, 0.45)",
        price_line=False,
        price_label=False,
        scale_margin_top=0.12,
        scale_margin_bottom=0.12,
    )
    histogram.set(
        macd_frame.assign(
            color=macd_frame["Histogram"].ge(0).map(
                {
                    True: colors.get("histogram_up", "#22c55e"),
                    False: colors.get("histogram_down", "#ef4444"),
                }
            )
        )[["time", "Histogram", "color"]].rename(columns={"Histogram": "MACD Histogram"})
    )

    macd_line = chart.create_line(
        name="MACD",
        color=colors.get("macd", "#38bdf8"),
        width=2,
        price_line=False,
        price_label=False,
        price_scale_id=histogram.id,
    )
    macd_line.set(macd_frame[["time", "MACD"]])

    signal_line = chart.create_line(
        name="Signal",
        color=colors.get("signal", "#f59e0b"),
        width=2,
        price_line=False,
        price_label=False,
        price_scale_id=histogram.id,
    )
    signal_line.set(macd_frame[["time", "Signal"]])

    macd_cross_markers = _build_cross_markers(
        series_frame=macd_frame,
        fast_column="MACD",
        slow_column="Signal",
        color=colors.get("cross", "#f8fafc"),
    )
    if macd_cross_markers:
        macd_line.marker_list(macd_cross_markers)

    chart.horizontal_line(
        price=0,
        color="rgba(148, 163, 184, 0.45)",
        width=1,
        style="dashed",
        axis_label_visible=False,
    )



def _render_stochastic_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Stochastic indicator into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    stochastic_frame = _build_stochastic_dataframe(
        data=data,
        k_length=params.get("k_length", 14),
        k_smoothing=params.get("k_smoothing", 3),
        d_length=params.get("d_length", 3),
    )
    if stochastic_frame.empty:
        return

    k_line = chart.create_line(
        name="%K",
        color=colors.get("k", STOCHASTIC_COLORS["k"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    k_line.set(stochastic_frame[["time", "%K"]])

    d_line = chart.create_line(
        name="%D",
        color=colors.get("d", STOCHASTIC_COLORS["d"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    d_line.set(stochastic_frame[["time", "%D"]])

    _render_oscillator_reference_lines(chart, stochastic_frame)



def _render_stochastic_rsi_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Stochastic RSI indicator into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    stochastic_rsi_frame = _build_stochastic_rsi_dataframe(
        data=data,
        rsi_length=params.get("rsi_length", 14),
        stoch_length=params.get("stoch_length", 14),
        k_smoothing=params.get("k_smoothing", 3),
        d_length=params.get("d_length", 3),
    )
    if stochastic_rsi_frame.empty:
        return

    k_line = chart.create_line(
        name="%K",
        color=colors.get("k", STOCHASTIC_COLORS["k"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    k_line.set(stochastic_rsi_frame[["time", "%K"]])

    d_line = chart.create_line(
        name="%D",
        color=colors.get("d", STOCHASTIC_COLORS["d"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    d_line.set(stochastic_rsi_frame[["time", "%D"]])

    _render_oscillator_reference_lines(chart, stochastic_rsi_frame)



def _create_indicator_chart(
    title: str,
    parent_chart: Any | None = None,
    total_height: int | None = None,
) -> Any:
    """Create one panel chart either as a synced subchart or a standalone chart."""
    if parent_chart is not None and total_height and total_height > 0:
        chart = build_streamlit_subchart(
            parent_chart=parent_chart,
            symbol=title,
            interval_label="",
            display_name=title,
            height_ratio=INDICATOR_CHART_HEIGHT / total_height,
            sync=True,
        )
    else:
        chart = build_streamlit_chart(
            symbol=title,
            interval_label="",
            display_name=title,
            height=INDICATOR_CHART_HEIGHT,
        )

    _style_indicator_chart(chart)
    return chart



def _render_single_indicator_chart(
    indicator: dict[str, Any],
    data: pd.DataFrame,
    parent_chart: Any | None = None,
    total_height: int | None = None,
) -> None:
    """Render one standalone indicator chart beneath the main price chart."""
    title = _format_indicator_title(indicator)
    chart = _create_indicator_chart(title, parent_chart=parent_chart, total_height=total_height)

    indicator_key = _indicator_key(indicator)
    if indicator_key == "ATR":
        _render_atr_indicator(chart, data, indicator)
    elif indicator_key == "PRICE_OSCILLATOR":
        _render_price_oscillator_indicator(chart, data, indicator)
    elif indicator_key == "RSI":
        _render_rsi_indicator(chart, data, indicator)
    elif indicator_key == "MACD":
        _render_macd_indicator(chart, data, indicator)
    elif indicator_key == "STOCHASTIC":
        _render_stochastic_indicator(chart, data, indicator)
    elif indicator_key == "STOCHASTIC_RSI":
        _render_stochastic_rsi_indicator(chart, data, indicator)
    else:
        return

    if parent_chart is None:
        chart.fit()
        chart.load()


__all__ = ["_render_single_indicator_chart"]
