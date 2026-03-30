from __future__ import annotations

import streamlit as st

from state.app_state import close_screener_page
from config.chart_options import INTERVAL_OPTIONS, PERIOD_OPTIONS
from ui.screener.data import SCREENER_DEFAULT_INTERVAL_LABEL, build_ema_screener_rows
from ui.screener.table import render_screener_table


def render_screener_page() -> None:
    """Render the EMA Screener workspace page."""
    top_col, _ = st.columns([1.0, 5.0])
    with top_col:
        if st.button("Kembali", use_container_width=True):
            close_screener_page()
            st.rerun()

    st.title("Screener")
    st.caption("Starter screener EMA. Win rate diambil dari logic backtest EMA yang sama dengan page Backtest.")

    controls_col, interval_col, period_col, action_col = st.columns([1.0, 1.0, 1.1, 0.85])
    with controls_col:
        ema_period = int(
            st.number_input(
                "Panjang EMA",
                min_value=1,
                step=1,
                value=int(st.session_state.get("screener_ema_period", 10)),
                key="screener_ema_period",
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
        st.button(
            "Screen",
            key="screener_screen_button",
            use_container_width=True,
            disabled=True,
        )

    st.caption(
        "Tombol `Screen` baru disiapkan tampil dulu, logic kliknya belum diaktifkan. "
        "Data tabel dan win rate backtest EMA langsung mengikuti kombinasi interval dan periode yang dipilih."
    )

    with st.spinner("Menghitung data screener EMA..."):
        rows = build_ema_screener_rows(
            interval_label=interval_label,
            period_label=period_label,
            ema_period=ema_period,
        )

    render_screener_table(
        rows,
        editor_key=f"screener_table_editor_{interval_label}_{period_label}_{ema_period}",
    )


__all__ = ["render_screener_page"]
