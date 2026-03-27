from __future__ import annotations

from typing import Any

import streamlit as st

from backtest.config import build_backtest_preview_indicator_config
from backtest.engine import BacktestError, run_backtest
from ui.backtest import clear_backtest_parameter_draft


VALID_BACKTEST_STRATEGIES = {"RSI", "MACD", "BREAK_EMA", "BREAK_MA", "PARABOLIC_SAR", "VOLUME_BREAKOUT"}



def _normalize_strategy_key(raw_value: Any) -> str:
    return str(raw_value or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")



def request_data_reload() -> None:
    """Flag the app to fetch fresh data on the next rerun."""
    st.session_state.pending_load = True
    st.session_state.backtest_last_error = ""
    st.session_state.backtest_period_label = st.session_state.period_option



def selected_backtest_strategy_params() -> dict[str, Any]:
    """Return the parameter dictionary for the selected backtest strategy."""
    selected_strategy = _normalize_strategy_key(st.session_state.selected_backtest_strategy)
    if selected_strategy == "VOLUME_BREAKOUT":
        return st.session_state.backtest_params_volume_breakout
    if selected_strategy == "PARABOLIC_SAR":
        return st.session_state.backtest_params_parabolic_sar
    if selected_strategy == "BREAK_EMA":
        return st.session_state.backtest_params_break_ema
    if selected_strategy == "BREAK_MA":
        return st.session_state.backtest_params_break_ma
    if selected_strategy == "MACD":
        return st.session_state.backtest_params_macd
    if selected_strategy == "RSI":
        return st.session_state.backtest_params_rsi
    return {}



def open_backtest_parameter_editor() -> None:
    """Open the parameter editor view inside the indicator dialog."""
    clear_backtest_parameter_draft()
    st.session_state.backtest_parameter_modal_open = True



def close_backtest_parameter_editor() -> None:
    """Close the parameter editor view inside the indicator dialog."""
    clear_backtest_parameter_draft()
    st.session_state.backtest_parameter_modal_open = False



def remove_backtest_indicator() -> None:
    """Remove the active backtest selection and disable its chart output."""
    close_backtest_parameter_editor()
    st.session_state.backtest_enabled = False
    st.session_state.backtest_refresh_requested = False
    st.session_state.backtest_result = None
    st.session_state.backtest_last_error = ""
    st.session_state.selected_backtest_strategy = ""



def build_effective_indicator_configs() -> list[dict[str, Any]]:
    """Add temporary backtest preview indicators when needed."""
    indicator_configs = list(st.session_state.active_indicators)
    selected_strategy = _normalize_strategy_key(st.session_state.selected_backtest_strategy)
    if selected_strategy not in VALID_BACKTEST_STRATEGIES:
        return indicator_configs

    should_render_backtest_indicator = (
        bool(st.session_state.backtest_enabled)
        or st.session_state.backtest_result is not None
        or bool(st.session_state.show_indicator_preview)
    )
    if not should_render_backtest_indicator:
        return indicator_configs

    try:
        preview_indicator = build_backtest_preview_indicator_config(
            selected_strategy,
            selected_backtest_strategy_params(),
        )
    except ValueError:
        return indicator_configs

    if isinstance(preview_indicator, list):
        return [*indicator_configs, *preview_indicator]
    return [*indicator_configs, preview_indicator]



def is_backtest_indicator_config(indicator: dict[str, Any]) -> bool:
    """Return whether one indicator row belongs to the backtest flow."""
    return str(indicator.get("source") or "").strip().lower() == "backtest"



def run_selected_backtest(show_spinner: bool = True) -> None:
    """Run the currently selected strategy against the active chart data."""
    result = st.session_state.loaded_result
    if result is None:
        st.session_state.backtest_result = None
        st.session_state.backtest_last_error = "Load chart dulu sebelum menjalankan backtest."
        st.session_state.backtest_refresh_requested = False
        return

    selected_strategy = _normalize_strategy_key(st.session_state.selected_backtest_strategy)
    st.session_state.backtest_period_label = st.session_state.period_option
    st.session_state.show_indicator_preview = bool(
        st.session_state.backtest_params_general.get("show_indicator_preview", True)
    )

    try:
        if show_spinner:
            with st.spinner("Menjalankan backtest..."):
                st.session_state.backtest_result = run_backtest(
                    data=result.data,
                    strategy_key=selected_strategy,
                    general_params=st.session_state.backtest_params_general,
                    strategy_params=selected_backtest_strategy_params(),
                    symbol=result.symbol,
                    interval_label=result.interval_label,
                    period_label=st.session_state.backtest_period_label,
                    use_lot_sizing=result.uses_bei_price_fractions,
                )
        else:
            st.session_state.backtest_result = run_backtest(
                data=result.data,
                strategy_key=selected_strategy,
                general_params=st.session_state.backtest_params_general,
                strategy_params=selected_backtest_strategy_params(),
                symbol=result.symbol,
                interval_label=result.interval_label,
                period_label=st.session_state.backtest_period_label,
                use_lot_sizing=result.uses_bei_price_fractions,
            )
    except BacktestError as exc:
        st.session_state.backtest_result = None
        st.session_state.backtest_last_error = str(exc)
    else:
        st.session_state.backtest_last_error = ""
    finally:
        st.session_state.backtest_refresh_requested = False


__all__ = [
    "VALID_BACKTEST_STRATEGIES",
    "build_effective_indicator_configs",
    "close_backtest_parameter_editor",
    "is_backtest_indicator_config",
    "open_backtest_parameter_editor",
    "remove_backtest_indicator",
    "request_data_reload",
    "run_selected_backtest",
    "selected_backtest_strategy_params",
]


