from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_core import (
    INDICATOR_CHART_HEIGHT,
    MAIN_CHART_HEIGHT,
    OVERLAY_INDICATOR_KEYS,
    PANEL_INDICATOR_KEYS,
    VOLUME_MA_WINDOW,
    VOLUME_PANEL_BOTTOM_MARGIN,
    VOLUME_PANEL_TOP_MARGIN,
    _apply_bei_price_fraction_format,
    _build_price_dataframe,
    _build_volume_dataframe,
    _indicator_key,
    _indicator_visible,
    build_streamlit_chart,
)
from charts.renderers_parts.backtest import _render_backtest_trade_markers
from charts.renderers_parts.overlays import _render_overlay_indicator
from charts.renderers_parts.panels import _render_single_indicator_chart


VOLUME_MA_COLOR = "#f59e0b"


def _visible_panel_indicators(indicator_configs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return the visible panel indicators that should live under the main chart."""
    return [
        indicator
        for indicator in indicator_configs or []
        if _indicator_visible(indicator) and _indicator_key(indicator) in PANEL_INDICATOR_KEYS
    ]



def _resolve_main_chart_layout(indicator_configs: list[dict[str, Any]] | None = None) -> tuple[int, float]:
    """Return the total iframe height and the main chart height ratio."""
    panel_count = len(_visible_panel_indicators(indicator_configs))
    total_height = MAIN_CHART_HEIGHT + (panel_count * INDICATOR_CHART_HEIGHT)
    main_chart_ratio = MAIN_CHART_HEIGHT / total_height if total_height > 0 else 1.0
    return total_height, main_chart_ratio



def _render_volume_panel(chart: Any, data: pd.DataFrame) -> None:
    """Render custom volume bars and Volume MA 20 in the lower volume pane."""
    volume_frame = _build_volume_dataframe(data)
    if volume_frame.empty:
        return

    line_name = f"Volume MA {VOLUME_MA_WINDOW}"

    histogram = chart.create_histogram(
        name="Volume",
        color="rgba(148, 163, 184, 0.40)",
        price_line=False,
        price_label=False,
        scale_margin_top=VOLUME_PANEL_TOP_MARGIN,
        scale_margin_bottom=VOLUME_PANEL_BOTTOM_MARGIN,
    )
    histogram.set(
        volume_frame[["time", "volume", "color"]].rename(columns={"volume": "Volume"})
    )
    chart._volume_scale_id = histogram.id

    volume_ma_line = chart.create_line(
        name=line_name,
        color=VOLUME_MA_COLOR,
        width=2,
        price_line=False,
        price_label=False,
        price_scale_id=histogram.id,
    )
    volume_ma_line.set(volume_frame[["time", line_name]])

    histogram.run_script(
        f"""
        (() => {{
            window.__compactVolumeFormatter = window.__compactVolumeFormatter || function(rawValue) {{
                const value = Number(rawValue);
                if (!Number.isFinite(value)) return '';
                const absValue = Math.abs(value);
                if (absValue >= 1000000) {{
                    return `${{(value / 1000000).toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }})}}M`;
                }}
                if (absValue >= 1000) {{
                    return `${{(value / 1000).toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }})}}K`;
                }}
                return value.toLocaleString('en-US', {{ maximumFractionDigits: 0 }});
            }};

            const formatVolume = window.__compactVolumeFormatter;

            {histogram.id}.series.applyOptions({{
                priceFormat: {{
                    type: 'custom',
                    minMove: 1,
                    formatter: formatVolume,
                }},
                lastValueVisible: false,
                priceLineVisible: false
            }});
            {volume_ma_line.id}.series.applyOptions({{
                priceFormat: {{
                    type: 'custom',
                    minMove: 1,
                    formatter: formatVolume,
                }},
                lastValueVisible: false,
                priceLineVisible: false,
                crosshairMarkerVisible: false
            }});
        }})();
        """
    )



def render_candlestick_chart(
    data: pd.DataFrame,
    symbol: str,
    interval_label: str,
    display_name: str | None = None,
    indicator_configs: list[dict[str, Any]] | None = None,
    use_bei_price_fractions: bool = False,
    backtest_trade_log: pd.DataFrame | None = None,
) -> None:
    """Load prepared OHLCV data into the Streamlit chart and render it."""
    total_height, main_chart_ratio = _resolve_main_chart_layout(indicator_configs)
    chart = build_streamlit_chart(
        symbol=symbol,
        interval_label=interval_label,
        display_name=display_name,
        height=total_height,
        inner_height=main_chart_ratio,
    )
    price_frame = _build_price_dataframe(data)

    if price_frame.empty:
        chart.load()
        return

    chart.set(price_frame.drop(columns=["volume"], errors="ignore"))
    _render_volume_panel(chart, data)
    latest_close = float(pd.to_numeric(price_frame["close"], errors="coerce").iloc[-1])
    if use_bei_price_fractions and latest_close > 0:
        _apply_bei_price_fraction_format(chart, latest_close)

    for indicator in indicator_configs or []:
        if not _indicator_visible(indicator):
            continue
        if _indicator_key(indicator) not in OVERLAY_INDICATOR_KEYS:
            continue
        _render_overlay_indicator(
            chart,
            data,
            indicator,
            interval_label=interval_label,
        )

    _render_backtest_trade_markers(chart, backtest_trade_log)
    render_indicator_charts(
        data=data,
        indicator_configs=indicator_configs,
        parent_chart=chart,
        total_height=total_height,
    )

    chart.fit()
    chart.load()



def render_indicator_charts(
    data: pd.DataFrame,
    indicator_configs: list[dict[str, Any]] | None = None,
    parent_chart: Any | None = None,
    total_height: int | None = None,
) -> None:
    """Render selected panel indicators either standalone or as synced subcharts."""
    for indicator in _visible_panel_indicators(indicator_configs):
        _render_single_indicator_chart(
            indicator,
            data,
            parent_chart=parent_chart,
            total_height=total_height,
        )


__all__ = [
    "render_candlestick_chart",
    "render_indicator_charts",
    "_resolve_main_chart_layout",
    "_visible_panel_indicators",
]
