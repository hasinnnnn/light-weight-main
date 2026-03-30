from __future__ import annotations

import streamlit as st

from state.app_state import (
    close_backtest_parameter_editor,
    open_backtest_parameter_editor,
    open_screener_page,
    remove_backtest_indicator,
)
from ui.backtest_parameter_dialog import render_backtest_parameter_dialog
from ui.backtest_tab import render_backtest_tab
from ui.screener import render_screener_tab
from .editor_view import render_indicator_editor_view
from .tabs import render_indicator_active_tab, render_indicator_list_tab

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

    active_tab, indicator_list_tab, backtest_tab, screener_tab = st.tabs(
        ["Indikator Aktif", "List Indikator", "Backtest", "Screener"]
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

    with screener_tab:
        screener_actions = render_screener_tab()
        if screener_actions["open_page"]:
            open_screener_page()
            st.rerun()



