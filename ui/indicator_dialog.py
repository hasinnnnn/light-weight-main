from __future__ import annotations

import html
from typing import Any

import streamlit as st

from state.app_state import (
    add_indicator,
    build_effective_indicator_configs,
    close_backtest_parameter_editor,
    close_indicator_editor,
    delete_indicator,
    find_indicator,
    indicator_color_widget_key,
    indicator_param_widget_key,
    is_backtest_indicator_config,
    is_indicator_active,
    open_backtest_parameter_editor,
    open_indicator_editor,
    remove_backtest_indicator,
    select_indicator_color,
    toggle_indicator_visibility,
    update_indicator_settings,
)
from charts.chart_service import describe_nearest_support_resistance, describe_strong_support_resistance
from indicators.catalog import (
    COLOR_PRESET_GRID,
    INDICATOR_CATALOG,
    INDICATOR_CATALOG_BY_KEY,
    format_indicator_instance_label,
    indicator_supports_edit,
    normalize_indicator_colors,
    normalize_indicator_params,
)
from ui.backtest_parameter_dialog import render_backtest_parameter_dialog
from ui.backtest_tab import render_backtest_tab
from ui.market_insight import format_price_value

@st.dialog("Indikator", dismissible=True)
def render_indicator_dialog() -> None:
    """Show the indicator picker modal."""
    editor_id = st.session_state.indicator_editor_id
    if editor_id:
        render_indicator_editor_view(editor_id)
        return
    if st.session_state.backtest_parameter_modal_open:
        render_backtest_parameter_dialog()
        return

    active_tab, indicator_list_tab, backtest_tab = st.tabs(
        ["Indikator Aktif", "List Indikator", "Backtest"]
    )

    with active_tab:
        render_indicator_active_tab()

    with indicator_list_tab:
        render_indicator_list_tab()

    with backtest_tab:
        backtest_actions = render_backtest_tab(has_loaded_data=st.session_state.loaded_result is not None)
        if backtest_actions["open_parameters"]:
            open_backtest_parameter_editor()
            st.rerun(scope="fragment")
        if backtest_actions["stop_backtest"]:
            remove_backtest_indicator()
            st.rerun()
        if backtest_actions["strategy_changed"]:
            close_backtest_parameter_editor()
            st.session_state.backtest_last_error = ""
            st.session_state.backtest_enabled = True
            st.session_state.backtest_refresh_requested = True
            st.session_state.show_indicator_preview = bool(
                st.session_state.backtest_params_general.get("show_indicator_preview", True)
            )
            st.rerun()


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


def render_indicator_editor_view(indicator_id: str) -> None:
    """Show the edit form inside the indicator modal."""
    indicator = find_indicator(indicator_id)
    if indicator is None:
        st.info("Indikator yang dipilih sudah tidak ada.")
        if st.button("Tutup", use_container_width=True):
            close_indicator_editor()
            st.rerun(scope="fragment")
        return

    indicator_definition = INDICATOR_CATALOG_BY_KEY[indicator["key"]]
    normalized_params = normalize_indicator_params(indicator["key"], indicator.get("params"))
    normalized_colors = normalize_indicator_colors(indicator["key"], indicator.get("colors"))

    st.markdown(f"**{indicator_definition['modal_label']}**")
    if indicator_definition["fields"] or indicator_definition.get("color_fields"):
        st.caption("Ubah parameter dan warna indikator, lalu klik OK untuk menerapkan ke chart.")
    else:
        st.caption("Indikator ini tidak punya parameter yang perlu diubah.")

    input_values: dict[str, int] = {}
    for field in indicator_definition["fields"]:
        widget_key = indicator_param_widget_key(indicator_id, field["name"])
        if widget_key not in st.session_state:
            st.session_state[widget_key] = int(normalized_params[field["name"]])
        input_values[field["name"]] = int(
            st.number_input(
                field["label"],
                min_value=int(field["min_value"]),
                step=1,
                value=int(st.session_state[widget_key]),
                format="%d",
                key=widget_key,
            )
        )

    color_values = render_indicator_color_controls(
        indicator_id=indicator_id,
        indicator_definition=indicator_definition,
        normalized_colors=normalized_colors,
    )

    if indicator["key"] == "NEAREST_SUPPORT_RESISTANCE":
        render_nearest_support_resistance_info(
            params=normalize_indicator_params(indicator["key"], input_values),
            colors=normalize_indicator_colors(indicator["key"], color_values),
        )
    elif indicator["key"] == "STRONG_SUPPORT_RESISTANCE":
        render_strong_support_resistance_info(
            params=normalize_indicator_params(indicator["key"], input_values),
            colors=normalize_indicator_colors(indicator["key"], color_values),
        )

    cancel_col, ok_col = st.columns(2)
    cancel_clicked = cancel_col.button("Batal", use_container_width=True)
    save_clicked = ok_col.button(
        "OK" if indicator_definition["fields"] or indicator_definition.get("color_fields") else "Tutup",
        use_container_width=True,
    )

    if cancel_clicked:
        close_indicator_editor()
        st.rerun(scope="fragment")

    if save_clicked:
        update_indicator_settings(indicator_id, input_values, color_values)
        close_indicator_editor()
        st.rerun()


def render_indicator_active_tab() -> None:
    """Render the active-indicator list inside the indicator modal."""
    display_indicators = build_effective_indicator_configs()
    if not display_indicators:
        st.info("Belum ada indikator aktif.")
        return

    for indicator in display_indicators:
        if is_backtest_indicator_config(indicator):
            indicator_label = html.escape(f"Backtest - {format_indicator_instance_label(indicator)}")
            if st.session_state.backtest_enabled:
                status_text = "Indikator backtest aktif di chart"
            elif st.session_state.backtest_result is not None:
                status_text = "Indikator backtest tampil dari hasil terakhir"
            else:
                status_text = "Preview indikator dari tab Backtest"
            status_label = html.escape(status_text)

            with st.container(border=True):
                info_col, edit_col, delete_col = st.columns([6.3, 0.8, 0.8])
                with info_col:
                    st.markdown(
                        f"""
                        <div class="indicator-row-title">{indicator_label}</div>
                        <div class="indicator-row-status">{status_label}</div>
                        <div class="indicator-row-status">Kelola strategi dan parameternya dari tab Backtest.</div>
                        """,
                        unsafe_allow_html=True,
                    )
                with edit_col:
                    if st.button(
                        " ",
                        key=f"backtest_indicator_edit_{indicator['id']}",
                        icon=":material/edit:",
                        help="Edit parameter backtest",
                        type="tertiary",
                        width="content",
                    ):
                        open_backtest_parameter_editor()
                        st.rerun(scope="fragment")
                with delete_col:
                    if st.button(
                        " ",
                        key=f"backtest_indicator_delete_{indicator['id']}",
                        icon=":material/delete:",
                        help="Hapus backtest",
                        type="tertiary",
                        width="content",
                    ):
                        remove_backtest_indicator()
                        close_indicator_editor()
                        st.rerun()
            continue

        is_visible = bool(indicator.get("visible", True))
        status_text = "Tampil di chart" if is_visible else "Disembunyikan"
        indicator_label = html.escape(format_indicator_instance_label(indicator))
        status_label = html.escape(status_text)
        visibility_icon = ":material/visibility:" if is_visible else ":material/visibility_off:"
        visibility_help = "Sembunyikan indikator" if is_visible else "Tampilkan indikator"
        edit_disabled = not indicator_supports_edit(indicator["key"])
        edit_help = "Edit indikator" if not edit_disabled else "Indikator ini tidak punya parameter"

        with st.container(border=True):
            info_col, visibility_col, edit_col, delete_col = st.columns([6.3, 0.8, 0.8, 0.8])
            with info_col:
                st.markdown(
                    f"""
                    <div class="indicator-row-title">{indicator_label}</div>
                    <div class="indicator-row-status">{status_label}</div>
                    """,
                    unsafe_allow_html=True,
                )
            with visibility_col:
                if st.button(
                    " ",
                    key=f"indicator_visibility_{indicator['id']}",
                    icon=visibility_icon,
                    help=visibility_help,
                    type="tertiary",
                    width="content",
                ):
                    toggle_indicator_visibility(indicator["id"])
                    close_indicator_editor()
                    st.rerun()
            with edit_col:
                if st.button(
                    " ",
                    key=f"indicator_edit_{indicator['id']}",
                    icon=":material/edit:",
                    help=edit_help,
                    type="tertiary",
                    width="content",
                    disabled=edit_disabled,
                ):
                    open_indicator_editor(indicator["id"])
                    st.rerun(scope="fragment")
            with delete_col:
                if st.button(
                    " ",
                    key=f"indicator_delete_{indicator['id']}",
                    icon=":material/delete:",
                    help="Hapus indikator",
                    type="tertiary",
                    width="content",
                ):
                    delete_indicator(indicator["id"])
                    close_indicator_editor()
                    st.rerun()


def render_indicator_list_tab() -> None:
    """Render the searchable indicator catalog inside the indicator modal."""
    search_query = st.text_input(
        "Cari indikator",
        key="indicator_search_query",
        placeholder="Cari EMA, MA, RSI, atau MACD",
    ).strip()
    normalized_query = search_query.casefold()

    filtered_indicators = [
        indicator
        for indicator in INDICATOR_CATALOG
        if not normalized_query
        or normalized_query in indicator["modal_label"].casefold()
        or normalized_query in indicator["description"].casefold()
    ]
    filtered_indicators = sorted(
        filtered_indicators,
        key=lambda indicator: indicator["modal_label"].casefold(),
    )

    if not filtered_indicators:
        st.info("Belum ada indikator yang cocok dengan pencarian itu.")
        return

    for indicator in filtered_indicators:
        is_active = is_indicator_active(indicator["key"])
        with st.container(border=True):
            info_col, action_col = st.columns([6.4, 0.7])
            with info_col:
                st.markdown(f"**{indicator['modal_label']}**")
                st.caption(indicator["description"])
            with action_col:
                if not is_active and st.button(
                    " ",
                    key=f"indicator_add_{indicator['key']}",
                    icon=":material/add:",
                    help="Tambah indikator",
                    type="tertiary",
                    width="content",
                ):
                    add_indicator(indicator["key"])
                    close_indicator_editor()
                    st.rerun()



