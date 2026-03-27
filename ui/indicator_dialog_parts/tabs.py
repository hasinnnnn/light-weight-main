from __future__ import annotations

import html

import streamlit as st

from state.app_state import (
    add_indicator,
    build_effective_indicator_configs,
    close_indicator_editor,
    delete_indicator,
    is_backtest_indicator_config,
    is_indicator_active,
    open_backtest_parameter_editor,
    open_indicator_editor,
    remove_backtest_indicator,
    toggle_indicator_visibility,
)
from indicators.catalog import (
    INDICATOR_CATALOG,
    format_indicator_instance_label,
    indicator_supports_edit,
)

def render_indicator_active_tab() -> None:
    """Render the active-indicator list inside the indicator modal."""
    display_indicators = build_effective_indicator_configs()
    if not display_indicators:
        st.info("Belum ada indikator aktif.")
        return

    for indicator in display_indicators:
        indicator_source = str(indicator.get("source") or "").strip().lower()
        if indicator_source == "backtest_helper":
            continue
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







