from __future__ import annotations

import html
from typing import Any

import streamlit as st

from state.app_state import indicator_color_widget_key, indicator_param_widget_key, select_indicator_color
from charts.chart_service import describe_nearest_support_resistance, describe_strong_support_resistance
from indicators.catalog import COLOR_PRESET_GRID
from ui.market_insight import format_price_value

def render_indicator_color_controls(
    indicator_id: str,
    indicator_definition: dict[str, Any],
    normalized_colors: dict[str, str],
) -> dict[str, str]:
    """Render color swatches and color pickers for one indicator editor."""
    color_fields = indicator_definition.get("color_fields", [])
    if not color_fields:
        return {}

    st.markdown("**Warna**")
    color_values: dict[str, str] = {}

    for color_field in color_fields:
        widget_key = indicator_color_widget_key(indicator_id, color_field["name"])
        if widget_key not in st.session_state:
            st.session_state[widget_key] = normalized_colors[color_field["name"]]

        current_color = str(st.session_state[widget_key]).lower()
        label_col, swatch_col, value_col, edit_col = st.columns([2.1, 0.45, 1.2, 0.7])
        with label_col:
            st.markdown(f"**{color_field['label']}**")
        with swatch_col:
            st.markdown(
                f"""
                <div style="
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 1px solid rgba(148, 163, 184, 0.55);
                    background: {html.escape(current_color)};
                    margin-top: 0.2rem;
                "></div>
                """,
                unsafe_allow_html=True,
            )
        with value_col:
            st.caption(current_color.upper())
        with edit_col:
            with st.popover(
                " ",
                icon=":material/edit:",
                help=f"Pilih warna {color_field['label']}",
                type="tertiary",
                width="content",
                key=f"indicator_color_popover_{indicator_id}_{color_field['name']}",
            ):
                st.caption("Preset warna")
                for row_index, color_row in enumerate(COLOR_PRESET_GRID):
                    palette_columns = st.columns(len(color_row), gap="small")
                    for color_index, preset_color in enumerate(color_row):
                        with palette_columns[color_index]:
                            st.markdown(
                                f"""
                                <div style="
                                    width: 24px;
                                    height: 24px;
                                    border-radius: 4px;
                                    border: 1px solid rgba(148, 163, 184, 0.45);
                                    background: {html.escape(preset_color)};
                                    margin: 0 auto 0.2rem auto;
                                "></div>
                                """,
                                unsafe_allow_html=True,
                            )
                            if st.button(
                                " ",
                                key=(
                                    f"indicator_color_preset_{indicator_id}_"
                                    f"{color_field['name']}_{row_index}_{color_index}"
                                ),
                                icon=":material/check:",
                                help=f"Pilih {preset_color.upper()}",
                                type="tertiary",
                                width="content",
                            ):
                                select_indicator_color(widget_key, preset_color)
                                st.rerun(scope="fragment")

                st.divider()
                st.caption("Custom color")
                st.color_picker(
                    color_field["label"],
                    key=widget_key,
                    label_visibility="collapsed",
                )

        color_values[color_field["name"]] = str(st.session_state[widget_key]).lower()

    return color_values


def render_nearest_support_resistance_info(
    params: dict[str, int],
    colors: dict[str, str],
) -> None:
    """Show the nearest support and resistance snapshot inside the indicator editor."""
    result = st.session_state.loaded_result
    if result is None:
        st.caption("Load chart dulu untuk melihat support dan resistance terdekat.")
        return

    level_summary = describe_nearest_support_resistance(
        result.data,
        {
            "key": "NEAREST_SUPPORT_RESISTANCE",
            "params": params,
            "colors": colors,
            "visible": True,
        },
    )
    if level_summary is None:
        st.caption("Data belum cukup untuk menghitung support dan resistance terdekat.")
        return

    def _render_level_card(
        label: str,
        level: dict[str, Any] | None,
        color: str,
    ) -> None:
        if level is None:
            st.markdown(f"**{label}**")
            st.caption("Belum ketemu level yang valid.")
            return

        st.markdown(
            f"""
            <div style="
                border: 1px solid {html.escape(color)};
                border-radius: 12px;
                padding: 0.8rem 0.85rem;
                background: linear-gradient(
                    180deg,
                    {html.escape(color)}22 0%,
                    rgba(11, 18, 32, 0.78) 100%
                );
                margin-bottom: 0.35rem;
            ">
                <div style="font-weight: 700; color: #f8fafc; margin-bottom: 0.2rem;">
                    {html.escape(label)}
                </div>
                <div style="font-size: 1.02rem; color: #ffffff; margin-bottom: 0.2rem;">
                    {html.escape(format_price_value(float(level["price"])))}
                </div>
                <div style="font-size: 0.84rem; color: #d6deeb;">
                    Pantulan: {int(level["bounces"])}
                </div>
                <div style="font-size: 0.84rem; color: #94a3b8;">
                    Zona: {html.escape(format_price_value(float(level["zone_bottom"])))} - {html.escape(format_price_value(float(level["zone_top"])))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("**Level Saat Ini**")
    st.caption(
        f"Harga terakhir: {format_price_value(float(level_summary['current_price']))}. "
        "Jumlah pantulan dihitung dari pivot yang masuk ke area level."
    )

    support_col, resistance_col = st.columns(2)
    with support_col:
        _render_level_card(
            label="Support",
            level=level_summary.get("support"),
            color=colors.get("support", "#ef4444"),
        )
    with resistance_col:
        _render_level_card(
            label="Resistance",
            level=level_summary.get("resistance"),
            color=colors.get("resistance", "#22c55e"),
        )


def render_strong_support_resistance_info(
    params: dict[str, int],
    colors: dict[str, str],
) -> None:
    """Show the strong support/resistance snapshot inside the indicator editor."""
    result = st.session_state.loaded_result
    if result is None:
        st.caption("Load chart dulu untuk melihat support dan resistance kuat.")
        return

    level_summary = describe_strong_support_resistance(
        result.data,
        {
            "key": "STRONG_SUPPORT_RESISTANCE",
            "params": params,
            "colors": colors,
            "visible": True,
        },
        interval_label=result.interval_label,
    )
    if level_summary is None:
        st.caption(
            "Data belum cukup untuk menemukan level kuat. "
            "Coba period lebih panjang atau turunkan minimal pantulan."
        )
        return

    def _render_level_card(
        label: str,
        level: dict[str, Any] | None,
        color: str,
    ) -> None:
        if level is None:
            st.markdown(f"**{label}**")
            st.caption("Belum ada level kuat yang lolos kriteria.")
            return

        st.markdown(
            f"""
            <div style="
                border: 1px solid {html.escape(color)};
                border-radius: 12px;
                padding: 0.8rem 0.85rem;
                background: linear-gradient(
                    180deg,
                    {html.escape(color)}22 0%,
                    rgba(11, 18, 32, 0.82) 100%
                );
                margin-bottom: 0.35rem;
            ">
                <div style="font-weight: 700; color: #f8fafc; margin-bottom: 0.2rem;">
                    {html.escape(label)}
                </div>
                <div style="font-size: 1.02rem; color: #ffffff; margin-bottom: 0.2rem;">
                    {html.escape(format_price_value(float(level["price"])))}
                </div>
                <div style="font-size: 0.84rem; color: #d6deeb;">
                    Pantulan: {int(level["bounces"])} | Breakout: {int(level["breakout_count"])}
                </div>
                <div style="font-size: 0.84rem; color: #d6deeb;">
                    Vol reversal kuat: {int(level["high_volume_reversals"])} | Rata-rata: {float(level["average_volume_ratio"]):.2f}x
                </div>
                <div style="font-size: 0.84rem; color: #94a3b8;">
                    Zona: {html.escape(format_price_value(float(level["zone_bottom"])))} - {html.escape(format_price_value(float(level["zone_top"])))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("**Level Kuat**")
    st.caption(
        f"Analisis memakai timeframe {level_summary['analysis_timeframe']} "
        f"dengan minimal {int(level_summary['minimum_bounces'])} pantulan."
    )

    support_col, resistance_col = st.columns(2)
    with support_col:
        _render_level_card(
            label="Support Kuat",
            level=level_summary.get("support"),
            color=colors.get("support", "#ef4444"),
        )
    with resistance_col:
        _render_level_card(
            label="Resistance Kuat",
            level=level_summary.get("resistance"),
            color=colors.get("resistance", "#22c55e"),
        )


def render_pattern_toggle_section(
    indicator_id: str,
    pattern_keys: list[str],
    pattern_definitions: dict[str, dict[str, str]],
    normalized_params: dict[str, Any],
) -> dict[str, bool]:
    """Render per-pattern checkboxes for pattern-based indicators."""
    toggle_values: dict[str, bool] = {}
    columns = st.columns(2, gap="small")

    for index, pattern_key in enumerate(pattern_keys):
        pattern_meta = pattern_definitions[pattern_key]
        param_key = f"show_{pattern_key}"
        widget_key = indicator_param_widget_key(indicator_id, param_key)
        if widget_key not in st.session_state:
            st.session_state[widget_key] = bool(normalized_params.get(param_key, True))

        with columns[index % 2]:
            toggle_values[param_key] = bool(
                st.checkbox(
                    str(pattern_meta["label"]),
                    key=widget_key,
                    help=str(pattern_meta["description"]),
                )
            )

    return toggle_values


