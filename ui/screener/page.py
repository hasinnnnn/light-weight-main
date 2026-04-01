from __future__ import annotations

import streamlit as st

from backtest.config import BREAK_EMA_CONFIRMATION_MODES, BREAK_EMA_EXIT_MODES, get_default_break_ema_params
from state.app_state import close_screener_page
from config.chart_options import INTERVAL_OPTIONS, PERIOD_OPTIONS
from ui.screener.data import SCREENER_DEFAULT_INTERVAL_LABEL, build_ema_screener_rows
from ui.backtest.sections.parameter_forms import option_label
from ui.screener.table import render_screener_table
from ui.screener.telegram_runner import (
    TELEGRAM_SEND_INTERVAL_SECONDS,
    start_telegram_worker,
    stop_telegram_worker,
    telegram_credentials_ready,
    worker_state,
)


def render_screener_page() -> None:
    """Render the EMA Screener workspace page."""
    top_col, _ = st.columns([1.0, 5.0])
    with top_col:
        if st.button("Kembali", use_container_width=True):
            close_screener_page()
            st.rerun()

    st.title("Screener")
    st.caption("Starter screener EMA. Win rate diambil dari logic backtest EMA yang sama dengan page Backtest.")

    break_ema_defaults = get_default_break_ema_params()
    ema_col, entry_col, exit_col, interval_col, period_col, action_col = st.columns([1.0, 1.45, 1.45, 1.0, 1.1, 0.85])
    with ema_col:
        ema_period = int(
            st.number_input(
                "Panjang EMA",
                min_value=1,
                step=1,
                value=int(st.session_state.get("screener_ema_period", 10)),
                key="screener_ema_period",
            )
        )
    with entry_col:
        entry_mode = str(
            st.selectbox(
                "Mode Entry",
                BREAK_EMA_CONFIRMATION_MODES,
                index=BREAK_EMA_CONFIRMATION_MODES.index(
                    str(
                        st.session_state.get(
                            "screener_breakdown_confirm_mode",
                            break_ema_defaults["breakdown_confirm_mode"],
                        )
                    )
                ),
                format_func=option_label,
                key="screener_breakdown_confirm_mode",
            )
        )
    with exit_col:
        exit_mode = str(
            st.selectbox(
                "Mode Exit",
                BREAK_EMA_EXIT_MODES,
                index=BREAK_EMA_EXIT_MODES.index(
                    str(st.session_state.get("screener_exit_mode", break_ema_defaults["exit_mode"]))
                ),
                format_func=option_label,
                key="screener_exit_mode",
            )
        )
    with interval_col:
        interval_index = (
            INTERVAL_OPTIONS.index(SCREENER_DEFAULT_INTERVAL_LABEL)
            if SCREENER_DEFAULT_INTERVAL_LABEL in INTERVAL_OPTIONS
            else 0
        )
        interval_label = str(
            st.selectbox(
                "Interval",
                INTERVAL_OPTIONS,
                index=interval_index,
                key="screener_interval_label",
            )
        )
    with period_col:
        period_index = PERIOD_OPTIONS.index("YTD") if "YTD" in PERIOD_OPTIONS else 0
        period_label = str(
            st.selectbox(
                "Periode",
                PERIOD_OPTIONS,
                index=period_index,
                key="screener_period_label",
            )
        )
    with action_col:
        start_requested = st.button(
            "Screen",
            key="screener_screen_button",
            use_container_width=True,
            type="primary",
        )

    st.caption(
        "Mode entry dan mode exit di screener memakai parameter Break EMA yang sudah ada di backtest. "
        f"Tombol `Screen` akan menyalakan worker Telegram tiap {TELEGRAM_SEND_INTERVAL_SECONDS // 60} menit "
        "untuk saham yang sedang diceklis. Worker screening real mengikuti Panjang EMA, Mode Entry, Mode Exit, dan Interval. "
        "Dropdown Periode tetap dipakai untuk tabel screener, tapi tidak dipakai sebagai parameter alert screening."
    )

    with st.spinner("Menghitung data screener EMA..."):
        rows = build_ema_screener_rows(
            interval_label=interval_label,
            period_label=period_label,
            ema_period=ema_period,
            breakdown_confirm_mode=entry_mode,
            exit_mode=exit_mode,
        )

    selected_symbols = list(st.session_state.get("screener_selected_symbols", []))
    active_worker = worker_state()
    if start_requested:
        if not selected_symbols:
            st.error("Centang dulu minimal satu saham sebelum menyalakan Screen ke Telegram.")
        elif not telegram_credentials_ready():
            st.error(
                "Isi `TELEGRAM_BOT_TOKEN`, `TELEGRAM_GROUP_ID`, dan `TELEGRAM_GROUP_LOG_ID` dulu di Streamlit secrets, environment variable, atau `.env`."
            )
        else:
            active_worker = start_telegram_worker(
                selected_symbols=selected_symbols,
                interval_label=interval_label,
                ema_period=ema_period,
                breakdown_confirm_mode=entry_mode,
                exit_mode=exit_mode,
            )
            st.success(
                f"Worker Telegram aktif tiap {TELEGRAM_SEND_INTERVAL_SECONDS // 60} menit untuk {len(selected_symbols)} saham."
            )
            st.rerun()

    if active_worker is not None:
        active_interval_minutes = max(1, int(active_worker["interval_seconds"]) // 60)
        st.success(
            f"Telegram worker aktif setiap {active_interval_minutes} menit "
            f"untuk {len(active_worker['selected_symbols'])} saham terpilih."
        )
        if st.button("Stop Telegram Worker", key="screener_stop_telegram_worker", use_container_width=False):
            stop_telegram_worker()
            st.success("Worker Telegram dimatikan.")
            st.rerun()
    else:
        st.caption("Worker Telegram belum aktif. Centang saham lalu tekan `Screen` untuk mulai kirim otomatis.")

    render_screener_table(
        rows,
        editor_key=(
            f"screener_table_editor_{interval_label}_{period_label}_{ema_period}_{entry_mode}_{exit_mode}"
        ),
    )


__all__ = ["render_screener_page"]
