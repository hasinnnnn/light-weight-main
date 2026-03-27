from __future__ import annotations

from typing import Any


class ChartServiceError(Exception):
    """Raised when the chart layer cannot be initialized."""


def _get_streamlit_chart_class() -> Any:
    """Import the Streamlit chart widget lazily so the app can fail gracefully."""
    try:
        from lightweight_charts.widgets import StreamlitChart
    except ModuleNotFoundError as exc:
        raise ChartServiceError(
            "Package `lightweight-charts` belum terpasang. "
            "Install dulu dengan `pip install -r requirements.txt` "
            "atau `pip install lightweight-charts`, lalu jalankan ulang app."
        ) from exc

    return StreamlitChart


from charts.core_parts.constants import MAIN_CHART_HEIGHT, VOLUME_PANEL_BOTTOM_MARGIN, VOLUME_PANEL_TOP_MARGIN


def _style_streamlit_chart(chart: Any, watermark_text: str) -> None:
    """Apply the shared TradingView-like theme to one chart instance."""
    chart.layout(
        background_color="#0b1220",
        text_color="#d6deeb",
        font_size=13,
        font_family="Trebuchet MS",
    )
    chart.grid(
        vert_enabled=True,
        horz_enabled=True,
        color="rgba(148, 163, 184, 0.15)",
        style="solid",
    )
    chart.candle_style(
        up_color="#22c55e",
        down_color="#ef4444",
        border_up_color="#22c55e",
        border_down_color="#ef4444",
        wick_up_color="#94f4b2",
        wick_down_color="#fca5a5",
    )
    chart.volume_config(
        scale_margin_top=VOLUME_PANEL_TOP_MARGIN,
        scale_margin_bottom=VOLUME_PANEL_BOTTOM_MARGIN,
        up_color="rgba(34, 197, 94, 0.45)",
        down_color="rgba(239, 68, 68, 0.45)",
    )
    chart.crosshair(
        mode="normal",
        vert_visible=True,
        vert_color="rgba(148, 163, 184, 0.35)",
        vert_style="dotted",
        horz_visible=True,
        horz_color="rgba(148, 163, 184, 0.35)",
        horz_style="dotted",
    )
    chart.legend(
        visible=True,
        ohlc=True,
        percent=False,
        lines=True,
        color="#d6deeb",
        font_size=12,
        color_based_on_candle=True,
    )
    chart.price_scale(
        auto_scale=True,
        scale_margin_top=0.08,
        scale_margin_bottom=0.22,
        border_visible=False,
        text_color="#cbd5e1",
    )
    chart.time_scale(
        visible=True,
        time_visible=True,
        seconds_visible=False,
        border_visible=False,
    )
    chart.watermark(
        text=watermark_text,
        font_size=42,
        color="rgba(148, 163, 184, 0.10)",
    )
    chart.price_line(label_visible=True, line_visible=True)


def build_streamlit_chart(
    symbol: str,
    interval_label: str,
    display_name: str | None = None,
    height: int = MAIN_CHART_HEIGHT,
    inner_width: float = 1.0,
    inner_height: float = 1.0,
) -> Any:
    """Create and style a TradingView-like Streamlit chart."""
    streamlit_chart_class = _get_streamlit_chart_class()
    chart = streamlit_chart_class(
        width=None,
        height=height,
        inner_width=inner_width,
        inner_height=inner_height,
    )
    _style_streamlit_chart(chart, display_name or symbol)
    return chart


def build_streamlit_subchart(
    parent_chart: Any,
    symbol: str,
    interval_label: str,
    display_name: str | None = None,
    height_ratio: float = 0.25,
    position: str = "left",
    sync: bool = True,
    sync_crosshairs_only: bool = False,
) -> Any:
    """Create one synced subchart inside the same Streamlit chart window."""
    chart = parent_chart.create_subchart(
        position=position,
        width=1.0,
        height=height_ratio,
        sync=sync,
        sync_crosshairs_only=sync_crosshairs_only,
    )
    _style_streamlit_chart(chart, display_name or symbol)
    return chart


def _bei_price_fraction_step(price: float) -> int:
    """Return the BEI tick-size step based on one latest price snapshot."""
    if price >= 5000:
        return 25
    if price >= 2000:
        return 10
    if price >= 500:
        return 5
    if price >= 200:
        return 2
    return 1


def _apply_bei_price_fraction_format(chart: Any, latest_price: float) -> None:
    """Apply BEI tick-size formatting to price scale and crosshair labels."""
    fraction_step = _bei_price_fraction_step(latest_price)
    chart.precision(0)
    chart.run_script(
        f"""
        {chart.id}.__beiFractionStep = {fraction_step};
        {chart.id}.__beiFractionFormatter = (rawPrice) => {{
            const price = Number(rawPrice);
            if (!Number.isFinite(price)) return '';
            const step = Number({chart.id}.__beiFractionStep) || 1;
            const roundedPrice = Math.round(price / step) * step;
            return roundedPrice.toLocaleString('en-US', {{
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }});
        }};
        {chart.id}.series.applyOptions({{
            priceFormat: {{
                type: 'price',
                precision: 0,
                minMove: {fraction_step}
            }}
        }});
        {chart.id}.chart.applyOptions({{
            localization: {{
                priceFormatter: {chart.id}.__beiFractionFormatter
            }}
        }});
        """
    )



def _apply_mobile_touch_behavior(chart: Any) -> None:
    """Prefer page scrolling on touch devices so chart gestures do not hijack mobile scroll."""
    chart.run_script(
        f"""
        (() => {{
            try {{
                const isTouchDevice =
                    window.matchMedia('(pointer: coarse)').matches ||
                    window.matchMedia('(hover: none)').matches ||
                    window.innerWidth <= 820;
                if (!isTouchDevice) {{
                    return;
                }}

                if (typeof {chart.id} === 'undefined' || !{chart.id}.chart) {{
                    return;
                }}

                {chart.id}.chart.applyOptions({{
                    handleScroll: {{
                        mouseWheel: true,
                        pressedMouseMove: true,
                        horzTouchDrag: false,
                        vertTouchDrag: false,
                    }},
                    handleScale: {{
                        axisPressedMouseMove: {{
                            time: false,
                            price: false,
                        }},
                        axisDoubleClickReset: {{
                            time: true,
                            price: true,
                        }},
                        mouseWheel: true,
                        pinch: false,
                    }},
                    kineticScroll: {{
                        mouse: false,
                        touch: false,
                    }},
                }});
            }} catch (error) {{
                console.debug('mobile chart touch preset skipped', error);
            }}
        }})();
        """
    )
