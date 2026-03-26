from __future__ import annotations

import streamlit as st

from state.app_state import (
    build_effective_indicator_configs,
    close_backtest_parameter_editor,
    close_indicator_editor,
    request_data_reload,
)
from data.market_data_service import DataLoadResult
from ui.indicator_dialog import render_indicator_dialog
from config.chart_options import INTERVAL_OPTIONS, PERIOD_OPTIONS

def sanitize_export_filename_part(value: str) -> str:
    """Convert one filename part into a compact, filesystem-friendly token."""
    cleaned = "".join(character if character.isalnum() else "_" for character in (value or "").strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "data"


def build_export_filename(result: DataLoadResult) -> str:
    """Build one export filename from the active chart selection."""
    symbol_part = sanitize_export_filename_part(result.symbol)
    interval_part = sanitize_export_filename_part(result.interval_label)
    period_part = sanitize_export_filename_part(result.period_label)
    return f"{symbol_part}_{interval_part}_{period_part}.txt"


def build_export_payload(result: DataLoadResult) -> bytes:
    """Serialize the visible chart data into a tab-separated text export."""
    export_frame = result.data[["time", "close", "high", "low", "open", "volume"]].copy()
    export_frame = export_frame.rename(
        columns={
            "time": "Datetime",
            "close": "Close",
            "high": "High",
            "low": "Low",
            "open": "Open",
            "volume": "Volume",
        }
    )
    return export_frame.to_csv(sep="\t", index=False, lineterminator="\n").encode("utf-8-sig")


def render_top_toolbar(result: DataLoadResult | None) -> None:
    """Render the search and filter controls above the chart."""
    search_col, interval_col, period_col, indicator_col, export_col = st.columns(
        [2.2, 1.0, 1.0, 0.85, 0.85]
    )

    with search_col:
        st.text_input(
            "Cari saham",
            key="symbol_input",
            placeholder="Ketik kode saham, misalnya IHSG, BBCA, atau PADI",
            help="Masukkan kode saham lalu tekan Enter untuk memuat chart.",
            label_visibility="collapsed",
            on_change=request_data_reload,
        )

    with interval_col:
        st.selectbox(
            "Interval",
            INTERVAL_OPTIONS,
            key="interval_option",
            label_visibility="collapsed",
            on_change=request_data_reload,
        )

    with period_col:
        st.selectbox(
            "Period",
            PERIOD_OPTIONS,
            key="period_option",
            label_visibility="collapsed",
            on_change=request_data_reload,
        )

    with indicator_col:
        indicator_count = len([indicator for indicator in build_effective_indicator_configs() if str(indicator.get("source") or "").strip().lower() != "backtest_helper"])
        indicator_label = f"Indikator ({indicator_count})" if indicator_count else "Indikator"
        if st.button(indicator_label, use_container_width=True):
            close_indicator_editor()
            close_backtest_parameter_editor()
            st.session_state.indicator_search_query = ""
            render_indicator_dialog()

    with export_col:
        if result is None:
            st.button("Export", use_container_width=True, disabled=True)
        else:
            st.download_button(
                "Export",
                data=build_export_payload(result),
                file_name=build_export_filename(result),
                mime="text/plain",
                use_container_width=True,
            )



