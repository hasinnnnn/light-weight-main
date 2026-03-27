from __future__ import annotations

import streamlit as st

from backtest.config import (
    display_backtest_period_label,
    get_strategy_label,
    normalize_general_backtest_params,
    normalize_strategy_backtest_params,
)
from ui.backtest.sections.parameter_forms import (
    clear_backtest_parameter_draft,
    hydrate_draft_state,
    render_break_ema_inputs,
    render_break_ma_inputs,
    render_general_parameter_inputs,
    render_macd_inputs,
    render_parabolic_sar_inputs,
    render_rsi_inputs,
    render_volume_breakout_inputs,
)

STRATEGY_STATE_KEY_LOOKUP = {
    "RSI": "backtest_params_rsi",
    "MACD": "backtest_params_macd",
    "BREAK_EMA": "backtest_params_break_ema",
    "BREAK_MA": "backtest_params_break_ma",
    "PARABOLIC_SAR": "backtest_params_parabolic_sar",
    "VOLUME_BREAKOUT": "backtest_params_volume_breakout",
}

VALID_STRATEGIES = set(STRATEGY_STATE_KEY_LOOKUP)


def render_backtest_parameter_dialog() -> None:
    """Render the backtest parameter editor inside the existing indicator modal."""
    strategy_key = str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if strategy_key not in VALID_STRATEGIES:
        st.markdown("**Parameter Backtest**")
        st.info("Pilih strategi backtest dulu sebelum membuka parameter.")
        if st.button("Tutup", use_container_width=True):
            clear_backtest_parameter_draft()
            st.session_state.backtest_parameter_modal_open = False
            st.rerun(scope="fragment")
        return

    general_params = normalize_general_backtest_params(st.session_state.backtest_params_general)
    strategy_state_key = STRATEGY_STATE_KEY_LOOKUP[strategy_key]
    strategy_params = normalize_strategy_backtest_params(
        strategy_key,
        st.session_state[strategy_state_key],
    )
    hydrate_draft_state(general_params, strategy_params)

    st.markdown(f"**Parameter Backtest - {get_strategy_label(strategy_key)}**")
    period_text = display_backtest_period_label(st.session_state.backtest_period_label)
    st.caption(f"Periode backtest mengikuti chart aktif ({period_text}).")

    general_values = render_general_parameter_inputs()
    st.divider()
    if strategy_key == "RSI":
        strategy_values = render_rsi_inputs()
    elif strategy_key == "MACD":
        strategy_values = render_macd_inputs()
    elif strategy_key == "BREAK_EMA":
        strategy_values = render_break_ema_inputs()
    elif strategy_key == "BREAK_MA":
        strategy_values = render_break_ma_inputs()
    elif strategy_key == "PARABOLIC_SAR":
        strategy_values = render_parabolic_sar_inputs()
    else:
        strategy_values = render_volume_breakout_inputs()

    cancel_col, save_col = st.columns(2)
    cancel_clicked = cancel_col.button("Batal", use_container_width=True)
    save_clicked = save_col.button("Simpan", use_container_width=True, type="primary")

    if cancel_clicked:
        clear_backtest_parameter_draft()
        st.session_state.backtest_parameter_modal_open = False
        st.rerun(scope="fragment")

    if save_clicked:
        st.session_state.backtest_params_general = normalize_general_backtest_params(general_values)
        st.session_state[strategy_state_key] = normalize_strategy_backtest_params(
            strategy_key,
            strategy_values,
        )
        st.session_state.show_indicator_preview = bool(
            st.session_state.backtest_params_general["show_indicator_preview"]
        )
        st.session_state.backtest_last_error = ""
        st.session_state.backtest_refresh_requested = bool(st.session_state.backtest_enabled)
        clear_backtest_parameter_draft()
        st.session_state.backtest_parameter_modal_open = False
        st.rerun()


__all__ = ["clear_backtest_parameter_draft", "render_backtest_parameter_dialog"]



