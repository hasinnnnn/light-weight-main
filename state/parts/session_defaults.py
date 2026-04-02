from __future__ import annotations

from typing import Any

import streamlit as st

from backtest.config import (
    get_default_backtest_general_params,
    get_default_break_ema_params,
    get_default_break_ma_params,
    get_default_macd_params,
    get_default_parabolic_sar_params,
    get_default_rsi_params,
    get_default_volume_breakout_params,
    normalize_general_backtest_params,
)
from state.parts.indicator_state import initialize_indicator_state



def _default_session_state_values() -> dict[str, Any]:
    return {
        "current_app_page": "chart",
        "symbol_input": "BUMI",
        "interval_option": "1 hari",
        "period_option": "1y",
        "loaded_result": None,
        "last_error": "",
        "selected_company_name": "",
        "active_indicators": [],
        "indicator_id_counter": 0,
        "indicator_state_initialized": False,
        "indicator_editor_id": "",
        "pending_load": True,
        "selected_backtest_strategy": "",
        "backtest_search_query": "",
        "backtest_params_general": get_default_backtest_general_params(),
        "backtest_params_rsi": get_default_rsi_params(),
        "backtest_params_macd": get_default_macd_params(),
        "backtest_params_break_ema": get_default_break_ema_params(),
        "backtest_params_break_ma": get_default_break_ma_params(),
        "backtest_params_parabolic_sar": get_default_parabolic_sar_params(),
        "backtest_params_volume_breakout": get_default_volume_breakout_params(),
        "backtest_result": None,
        "backtest_period_label": "1y",
        "backtest_enabled": False,
        "backtest_refresh_requested": False,
        "show_indicator_preview": True,
        "backtest_parameter_modal_open": False,
        "backtest_last_error": "",
        "screener_ema_period": 10,
        "screener_breakdown_confirm_mode": "body_breakdown",
        "screener_exit_mode": "ema_breakdown",
        "screener_interval_label": "1 hari",
        "screener_period_label": "1y",
        "screener_selected_symbols": [],
    }



def _apply_backtest_session_migrations() -> None:
    st.session_state.backtest_params_general = normalize_general_backtest_params(
        st.session_state.backtest_params_general
    )
    params_version = int(st.session_state.get("backtest_general_params_version", 0))
    if params_version < 2:
        if (
            st.session_state.backtest_params_general["position_sizing_mode"] == "fixed_percent_of_equity"
            and abs(float(st.session_state.backtest_params_general["position_size_value"]) - 100.0) < 1e-9
        ):
            st.session_state.backtest_params_general["position_sizing_mode"] = "fixed_nominal"
            st.session_state.backtest_params_general["position_size_value"] = 1_000_000.0
        st.session_state.backtest_general_params_version = 2

    if params_version < 3:
        if abs(float(st.session_state.backtest_params_general["initial_capital"]) - 100_000_000.0) < 1e-9:
            st.session_state.backtest_params_general["initial_capital"] = 10_000_000.0
        st.session_state.backtest_general_params_version = 3

    selection_version = int(st.session_state.get("backtest_strategy_selection_version", 0))
    if selection_version < 1:
        if (
            str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR") == "RSI"
            and not st.session_state.backtest_enabled
            and st.session_state.backtest_result is None
        ):
            st.session_state.selected_backtest_strategy = ""
        st.session_state.backtest_strategy_selection_version = 1

    st.session_state.backtest_period_label = st.session_state.period_option
    st.session_state.show_indicator_preview = bool(
        st.session_state.backtest_params_general.get("show_indicator_preview", True)
    )



def initialize_session_state() -> None:
    """Set app defaults so selections and the last result survive reruns."""
    defaults = _default_session_state_values()
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    _apply_backtest_session_migrations()
    initialize_indicator_state()


__all__ = ["initialize_session_state"]


