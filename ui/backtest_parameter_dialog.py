from __future__ import annotations

from typing import Any

import streamlit as st

from backtest.config import (
    BREAK_EMA_EXIT_MODES,
    MACD_ENTRY_MODES,
    MACD_EXIT_MODES,
    POSITION_SIZING_MODES,
    RSI_ENTRY_MODES,
    RSI_EXIT_MODES,
    display_backtest_period_label,
    get_default_backtest_general_params,
    get_default_strategy_params,
    get_strategy_label,
    normalize_general_backtest_params,
    normalize_strategy_backtest_params,
)

GENERAL_DRAFT_PREFIX = "backtest_general_draft_"
STRATEGY_DRAFT_PREFIX = "backtest_strategy_draft_"

OPTION_LABELS = {
    "fixed_percent_of_equity": "Persentase ekuitas tetap",
    "fixed_nominal": "Nominal tetap",
    "cross_up_oversold": "Cross naik dari area oversold",
    "rsi_above_level": "RSI di atas level exit",
    "cross_down_overbought": "Cross turun dari area overbought",
    "fixed_tp_sl": "Hanya stop loss dan take profit",
    "ema_breakdown": "Close breakdown di bawah EMA",
    "tp_sl_trailing_only": "Stop loss / take profit / trailing saja",
    "macd_cross_up_signal": "MACD cross naik di atas signal",
    "macd_cross_up_zero": "MACD cross naik di atas garis nol",
    "histogram_turn_positive": "Histogram berubah positif",
    "macd_cross_down_signal": "MACD cross turun di bawah signal",
    "macd_cross_down_zero": "MACD turun di bawah garis nol",
}


def _option_label(value: str) -> str:
    """Map one internal option value into an Indonesian UI label."""
    return OPTION_LABELS.get(str(value), str(value))


def _draft_key(prefix: str, field_name: str) -> str:
    """Build one widget key for the parameter editor."""
    return f"{prefix}{field_name}"


def clear_backtest_parameter_draft() -> None:
    """Clear all draft widgets used by the parameter editor."""
    general_defaults = get_default_backtest_general_params()
    for field_name in general_defaults:
        st.session_state.pop(_draft_key(GENERAL_DRAFT_PREFIX, field_name), None)

    for strategy_key in ["RSI", "MACD", "BREAK_EMA", "PARABOLIC_SAR", "VOLUME_BREAKOUT"]:
        for field_name in get_default_strategy_params(strategy_key):
            st.session_state.pop(_draft_key(STRATEGY_DRAFT_PREFIX, field_name), None)


def _hydrate_draft_state(
    general_params: dict[str, Any],
    strategy_params: dict[str, Any],
) -> None:
    """Populate draft widgets from the saved session-state values."""
    for field_name, value in general_params.items():
        widget_key = _draft_key(GENERAL_DRAFT_PREFIX, field_name)
        if widget_key not in st.session_state:
            st.session_state[widget_key] = value

    for field_name, value in strategy_params.items():
        widget_key = _draft_key(STRATEGY_DRAFT_PREFIX, field_name)
        if widget_key not in st.session_state:
            st.session_state[widget_key] = value


def _render_general_parameter_inputs() -> dict[str, Any]:
    """Render the general backtest parameter fields."""
    values: dict[str, Any] = {}
    st.markdown("**Parameter Umum**")
    values["initial_capital"] = float(
        st.number_input(
            "Modal Awal",
            min_value=1_000.0,
            value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "initial_capital")]),
            step=100_000.0,
            format="%.2f",
            key=_draft_key(GENERAL_DRAFT_PREFIX, "initial_capital"),
        )
    )
    values["position_sizing_mode"] = st.selectbox(
        "Mode Ukuran Posisi",
        POSITION_SIZING_MODES,
        index=POSITION_SIZING_MODES.index(
            str(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "position_sizing_mode")])
        ),
        format_func=_option_label,
        key=_draft_key(GENERAL_DRAFT_PREFIX, "position_sizing_mode"),
    )
    position_size_label = (
        "Ukuran Posisi (%)" if values["position_sizing_mode"] == "fixed_percent_of_equity" else "Ukuran Posisi Nominal"
    )
    values["position_size_value"] = float(
        st.number_input(
            position_size_label,
            min_value=0.01,
            value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "position_size_value")]),
            step=1.0,
            format="%.2f",
            key=_draft_key(GENERAL_DRAFT_PREFIX, "position_size_value"),
        )
    )
    fee_col, sell_fee_col, slip_col = st.columns(3)
    with fee_col:
        values["buy_fee_pct"] = float(
            st.number_input(
                "Fee Beli (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "buy_fee_pct")]),
                step=0.01,
                format="%.2f",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "buy_fee_pct"),
            )
        )
    with sell_fee_col:
        values["sell_fee_pct"] = float(
            st.number_input(
                "Fee Jual (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "sell_fee_pct")]),
                step=0.01,
                format="%.2f",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "sell_fee_pct"),
            )
        )
    with slip_col:
        values["slippage_pct"] = float(
            st.number_input(
                "Slippage (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "slippage_pct")]),
                step=0.01,
                format="%.2f",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "slippage_pct"),
            )
        )
    stop_col, take_col, trailing_col = st.columns(3)
    with stop_col:
        values["stop_loss_pct"] = float(
            st.number_input(
                "Stop Loss (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "stop_loss_pct")]),
                step=0.10,
                format="%.2f",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "stop_loss_pct"),
            )
        )
    with take_col:
        values["take_profit_pct"] = float(
            st.number_input(
                "Take Profit (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "take_profit_pct")]),
                step=0.10,
                format="%.2f",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "take_profit_pct"),
            )
        )
    with trailing_col:
        values["trailing_stop_pct"] = float(
            st.number_input(
                "Trailing Stop (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "trailing_stop_pct")]),
                step=0.10,
                format="%.2f",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "trailing_stop_pct"),
            )
        )
    holding_col, cooldown_col = st.columns(2)
    with holding_col:
        values["max_holding_bars"] = int(
            st.number_input(
                "Batas Holding (bar)",
                min_value=0,
                value=int(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "max_holding_bars")]),
                step=1,
                format="%d",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "max_holding_bars"),
            )
        )
    with cooldown_col:
        values["cooldown_bars"] = int(
            st.number_input(
                "Cooldown (bar)",
                min_value=0,
                value=int(st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "cooldown_bars")]),
                step=1,
                format="%d",
                key=_draft_key(GENERAL_DRAFT_PREFIX, "cooldown_bars"),
            )
        )
    values["show_indicator_preview"] = bool(
        st.checkbox(
            "Tampilkan preview indikator sebelum backtest dijalankan",
            value=bool(
                st.session_state[_draft_key(GENERAL_DRAFT_PREFIX, "show_indicator_preview")]
            ),
            key=_draft_key(GENERAL_DRAFT_PREFIX, "show_indicator_preview"),
        )
    )
    return values


def _render_rsi_inputs() -> dict[str, Any]:
    """Render the RSI strategy-specific fields."""
    values: dict[str, Any] = {}
    st.markdown("**Parameter RSI**")
    first_col, second_col, third_col = st.columns(3)
    with first_col:
        values["rsi_period"] = int(
            st.number_input(
                "Periode RSI",
                min_value=2,
                value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "rsi_period")]),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "rsi_period"),
            )
        )
    with second_col:
        values["oversold_level"] = float(
            st.number_input(
                "Level Oversold",
                min_value=1.0,
                max_value=49.0,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "oversold_level")]),
                step=1.0,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "oversold_level"),
            )
        )
    with third_col:
        values["overbought_level"] = float(
            st.number_input(
                "Level Overbought",
                min_value=50.0,
                max_value=99.0,
                value=float(
                    st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "overbought_level")]
                ),
                step=1.0,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "overbought_level"),
            )
        )
    values["exit_rsi_level"] = float(
        st.number_input(
            "Level Exit RSI",
            min_value=1.0,
            max_value=99.0,
            value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "exit_rsi_level")]),
            step=1.0,
            format="%.2f",
            key=_draft_key(STRATEGY_DRAFT_PREFIX, "exit_rsi_level"),
        )
    )
    values["trend_filter_enabled"] = bool(
        st.checkbox(
            "Aktifkan trend filter",
            value=bool(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "trend_filter_enabled")]),
            key=_draft_key(STRATEGY_DRAFT_PREFIX, "trend_filter_enabled"),
        )
    )
    values["trend_ma_period"] = int(
        st.number_input(
            "Periode MA Tren",
            min_value=2,
            value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "trend_ma_period")]),
            step=1,
            format="%d",
            key=_draft_key(STRATEGY_DRAFT_PREFIX, "trend_ma_period"),
        )
    )
    values["entry_mode"] = st.selectbox(
        "Mode Entry",
        RSI_ENTRY_MODES,
        index=RSI_ENTRY_MODES.index(
            str(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "entry_mode")])
        ),
        format_func=_option_label,
        key=_draft_key(STRATEGY_DRAFT_PREFIX, "entry_mode"),
    )
    values["exit_mode"] = st.selectbox(
        "Mode Exit",
        RSI_EXIT_MODES,
        index=RSI_EXIT_MODES.index(
            str(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "exit_mode")])
        ),
        format_func=_option_label,
        key=_draft_key(STRATEGY_DRAFT_PREFIX, "exit_mode"),
    )
    return values


def _render_macd_inputs() -> dict[str, Any]:
    """Render the MACD strategy-specific fields."""
    values: dict[str, Any] = {}
    st.markdown("**Parameter MACD**")
    first_col, second_col, third_col = st.columns(3)
    with first_col:
        values["macd_fast_period"] = int(
            st.number_input(
                "Periode Cepat MACD",
                min_value=1,
                value=int(
                    st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "macd_fast_period")]
                ),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "macd_fast_period"),
            )
        )
    with second_col:
        values["macd_slow_period"] = int(
            st.number_input(
                "Periode Lambat MACD",
                min_value=2,
                value=int(
                    st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "macd_slow_period")]
                ),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "macd_slow_period"),
            )
        )
    with third_col:
        values["macd_signal_period"] = int(
            st.number_input(
                "Periode Signal MACD",
                min_value=1,
                value=int(
                    st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "macd_signal_period")]
                ),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "macd_signal_period"),
            )
        )
    values["trend_filter_enabled"] = bool(
        st.checkbox(
            "Aktifkan trend filter",
            value=bool(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "trend_filter_enabled")]),
            key=_draft_key(STRATEGY_DRAFT_PREFIX, "trend_filter_enabled"),
        )
    )
    values["trend_ma_period"] = int(
        st.number_input(
            "Periode MA Tren",
            min_value=2,
            value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "trend_ma_period")]),
            step=1,
            format="%d",
            key=_draft_key(STRATEGY_DRAFT_PREFIX, "trend_ma_period"),
        )
    )
    values["entry_mode"] = st.selectbox(
        "Mode Entry",
        MACD_ENTRY_MODES,
        index=MACD_ENTRY_MODES.index(
            str(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "entry_mode")])
        ),
        format_func=_option_label,
        key=_draft_key(STRATEGY_DRAFT_PREFIX, "entry_mode"),
    )
    values["exit_mode"] = st.selectbox(
        "Mode Exit",
        MACD_EXIT_MODES,
        index=MACD_EXIT_MODES.index(
            str(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "exit_mode")])
        ),
        format_func=_option_label,
        key=_draft_key(STRATEGY_DRAFT_PREFIX, "exit_mode"),
    )
    return values


def _render_break_ema_inputs() -> dict[str, Any]:
    """Render the Break EMA strategy-specific fields."""
    values: dict[str, Any] = {}
    st.markdown("**Parameter Break EMA**")
    ema_col, exit_col = st.columns(2)
    with ema_col:
        values["ema_period"] = int(
            st.number_input(
                "Periode EMA",
                min_value=1,
                value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "ema_period")]),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "ema_period"),
            )
        )
    with exit_col:
        values["exit_mode"] = st.selectbox(
            "Mode Exit",
            BREAK_EMA_EXIT_MODES,
            index=BREAK_EMA_EXIT_MODES.index(
                str(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "exit_mode")])
            ),
            format_func=_option_label,
            key=_draft_key(STRATEGY_DRAFT_PREFIX, "exit_mode"),
        )

    st.caption(
        "Trailing stop mengikuti parameter umum backtest. "
        "Kalau mode exit diganti ke TP/SL/Trailing saja, strategi tidak akan keluar karena breakdown EMA."
    )
    return values


def _render_parabolic_sar_inputs() -> dict[str, Any]:
    """Render the Parabolic SAR strategy-specific fields."""
    values: dict[str, Any] = {}
    st.markdown("**Parameter Parabolic SAR**")
    accel_col, max_accel_col = st.columns(2)
    with accel_col:
        values["psar_acceleration_pct"] = float(
            st.number_input(
                "Akselerasi PSAR (%)",
                min_value=0.1,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "psar_acceleration_pct")]),
                step=0.1,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "psar_acceleration_pct"),
            )
        )
    with max_accel_col:
        values["psar_max_acceleration_pct"] = float(
            st.number_input(
                "Maks. akselerasi PSAR (%)",
                min_value=0.1,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "psar_max_acceleration_pct")]),
                step=0.1,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "psar_max_acceleration_pct"),
            )
        )

    st.caption(
        "Filter trend untuk strategi ini sekarang dibuat lebih bersih: hanya pakai MA 200 di chart utama. "
        "Trendline otomatis dan paket EMA berlapis sudah dihapus dari preview backtest."
    )
    return values


def _render_volume_breakout_inputs() -> dict[str, Any]:
    """Render the Volume Breakout strategy-specific fields."""
    values: dict[str, Any] = {}
    st.markdown("**Parameter Volume Breakout**")
    bars_col, range_col = st.columns(2)
    with bars_col:
        values["consolidation_bars"] = int(
            st.number_input(
                "Bar konsolidasi",
                min_value=3,
                value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "consolidation_bars")]),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "consolidation_bars"),
            )
        )
    with range_col:
        values["max_consolidation_range_pct"] = float(
            st.number_input(
                "Rentang konsolidasi maks. (%)",
                min_value=0.1,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "max_consolidation_range_pct")]),
                step=0.1,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "max_consolidation_range_pct"),
            )
        )

    volume_col, ratio_col = st.columns(2)
    with volume_col:
        values["volume_ma_period"] = int(
            st.number_input(
                "Periode MA volume",
                min_value=3,
                value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "volume_ma_period")]),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "volume_ma_period"),
            )
        )
    with ratio_col:
        values["consolidation_volume_ratio_max"] = float(
            st.number_input(
                "Volume konsolidasi maks. (x)",
                min_value=0.1,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "consolidation_volume_ratio_max")]),
                step=0.05,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "consolidation_volume_ratio_max"),
            )
        )

    breakout_col, buffer_col, exit_col = st.columns(3)
    with breakout_col:
        values["breakout_volume_ratio_min"] = float(
            st.number_input(
                "Volume breakout min. (x)",
                min_value=1.0,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "breakout_volume_ratio_min")]),
                step=0.05,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "breakout_volume_ratio_min"),
            )
        )
    with buffer_col:
        values["breakout_buffer_pct"] = float(
            st.number_input(
                "Buffer breakout (%)",
                min_value=0.0,
                value=float(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "breakout_buffer_pct")]),
                step=0.05,
                format="%.2f",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "breakout_buffer_pct"),
            )
        )
    with exit_col:
        values["exit_after_bars"] = int(
            st.number_input(
                "Exit setelah bar",
                min_value=1,
                value=int(st.session_state[_draft_key(STRATEGY_DRAFT_PREFIX, "exit_after_bars")]),
                step=1,
                format="%d",
                key=_draft_key(STRATEGY_DRAFT_PREFIX, "exit_after_bars"),
            )
        )
    return values


def render_backtest_parameter_dialog() -> None:
    """Render the backtest parameter editor inside the existing indicator modal."""
    strategy_key = str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if strategy_key not in {"RSI", "MACD", "BREAK_EMA", "PARABOLIC_SAR", "VOLUME_BREAKOUT"}:
        st.markdown("**Parameter Backtest**")
        st.info("Pilih strategi backtest dulu sebelum membuka parameter.")
        if st.button("Tutup", use_container_width=True):
            clear_backtest_parameter_draft()
            st.session_state.backtest_parameter_modal_open = False
            st.rerun(scope="fragment")
        return

    general_params = normalize_general_backtest_params(st.session_state.backtest_params_general)
    strategy_state_key_lookup = {
        "RSI": "backtest_params_rsi",
        "MACD": "backtest_params_macd",
        "BREAK_EMA": "backtest_params_break_ema",
        "PARABOLIC_SAR": "backtest_params_parabolic_sar",
        "VOLUME_BREAKOUT": "backtest_params_volume_breakout",
    }
    strategy_state_key = strategy_state_key_lookup[strategy_key]
    strategy_params = normalize_strategy_backtest_params(
        strategy_key,
        st.session_state[strategy_state_key],
    )
    _hydrate_draft_state(general_params, strategy_params)

    st.markdown(f"**Parameter Backtest - {get_strategy_label(strategy_key)}**")
    period_text = display_backtest_period_label(st.session_state.backtest_period_label)
    st.caption(f"Periode backtest mengikuti chart aktif ({period_text}).")

    general_values = _render_general_parameter_inputs()
    st.divider()
    if strategy_key == "RSI":
        strategy_values = _render_rsi_inputs()
    elif strategy_key == "MACD":
        strategy_values = _render_macd_inputs()
    elif strategy_key == "BREAK_EMA":
        strategy_values = _render_break_ema_inputs()
    elif strategy_key == "PARABOLIC_SAR":
        strategy_values = _render_parabolic_sar_inputs()
    else:
        strategy_values = _render_volume_breakout_inputs()

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










