from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from backtest.models import BacktestResult
from common.time_utils import format_short_timestamp_label
from ui.backtest.sections.result_summary import (
    SUMMARY_TONES,
    format_lot,
    format_pct,
    format_rupiah,
    metric_tone,
)

EXIT_REASON_LABELS = {
    "stop_loss": "Stop loss",
    "take_profit": "Take profit",
    "trailing_stop": "Trailing stop",
    "strategy_exit": "Sinyal strategi",
    "max_holding_bars": "Batas holding",
    "end_of_data": "Akhir data",
}


def _format_trade_date_range(entry_value: object, exit_value: object) -> str:
    entry_label = format_short_timestamp_label(entry_value)
    exit_label = format_short_timestamp_label(exit_value)
    if entry_label == "-" and exit_label == "-":
        return "-"
    if entry_label == "-":
        return exit_label
    if exit_label == "-":
        return entry_label
    return f"{entry_label} - {exit_label}"



def build_trade_log_table(result: BacktestResult) -> pd.DataFrame:
    """Translate and sort the raw trade log for display."""
    table = result.trade_log.rename(
        columns={
            "trade_no": "No.",
            "entry_price": "Harga entry",
            "exit_price": "Harga exit",
            "qty": "Kuantitas",
            "pnl_nominal": "Laba/Rugi",
            "pnl_pct": "Laba/Rugi (%)",
            "exit_reason": "Alasan keluar",
        }
    ).copy()

    entry_datetimes = pd.to_datetime(result.trade_log.get("entry_datetime"), errors="coerce")
    exit_datetimes = pd.to_datetime(result.trade_log.get("exit_datetime"), errors="coerce")
    date_ranges = [
        _format_trade_date_range(entry_value, exit_value)
        for entry_value, exit_value in zip(entry_datetimes, exit_datetimes)
    ]
    insert_at = table.columns.get_loc("No.") + 1 if "No." in table.columns else 0
    table.insert(insert_at, "Tanggal", date_ranges)
    table = table.drop(columns=["entry_datetime", "exit_datetime"], errors="ignore")

    table["Alasan keluar"] = table["Alasan keluar"].map(
        lambda value: EXIT_REASON_LABELS.get(str(value), str(value).replace("_", " "))
    )

    qty_values = pd.to_numeric(table["Kuantitas"], errors="coerce").fillna(0.0)
    entry_totals = qty_values * pd.to_numeric(table["Harga entry"], errors="coerce").fillna(0.0)
    exit_totals = qty_values * pd.to_numeric(table["Harga exit"], errors="coerce").fillna(0.0)
    table.insert(table.columns.get_loc("Harga entry") + 1, "Total entry", entry_totals)
    table.insert(table.columns.get_loc("Harga exit") + 1, "Total exit", exit_totals)

    if result.uses_lot_sizing and result.lot_size > 1:
        lots = qty_values / float(result.lot_size)
        table.insert(table.columns.get_loc("Kuantitas") + 1, "Lot", lots)
        table = table.drop(columns=["Kuantitas"])

    table = (
        table.assign(_sort_key=exit_datetimes)
        .sort_values("_sort_key", ascending=False, na_position="last", kind="mergesort")
        .drop(columns=["_sort_key"])
        .reset_index(drop=True)
    )
    return table



def format_trade_log_cell(column_name: str, value: object) -> str:
    """Format one trade-log cell into readable Indonesian text."""
    if pd.isna(value):
        return "-"
    if column_name == "No.":
        return str(int(float(value)))
    if column_name in {"Harga entry", "Harga exit", "Total entry", "Total exit"}:
        return format_rupiah(float(value))
    if column_name == "Lot":
        return format_lot(float(value))
    if column_name == "Laba/Rugi":
        return format_rupiah(float(value), show_sign=True)
    if column_name == "Laba/Rugi (%)":
        return format_pct(float(value), show_sign=True)
    return str(value)



def trade_log_cell_style(column_name: str, value: object) -> str:
    """Build the inline CSS for one trade-log cell."""
    style_parts = [
        "padding: 0.72rem 0.8rem",
        "text-align: center",
        "vertical-align: middle",
        "border-top: 1px solid rgba(148, 163, 184, 0.12)",
        "color: #f8fafc",
        "font-size: 0.92rem",
        "white-space: nowrap",
    ]
    if column_name in {"Laba/Rugi", "Laba/Rugi (%)"}:
        tone = metric_tone(float(value)) if not pd.isna(value) else "neutral"
        style_parts.append(f"color: {SUMMARY_TONES[tone]['text']}")
        style_parts.append("font-weight: 700")
    elif column_name == "Alasan keluar":
        style_parts.append("font-weight: 600")
        style_parts.append("color: #e2e8f0")
    return "; ".join(style_parts)



def render_trade_log_table(result: BacktestResult) -> None:
    """Render the trade log as a centered custom HTML table."""
    table = build_trade_log_table(result)
    if table.empty:
        st.info("Belum ada transaksi yang bisa ditampilkan.")
        return

    header_cells = "".join(
        (
            f'<th style="padding: 0.82rem 0.8rem; text-align: center; white-space: nowrap; '
            f'background: rgba(30, 41, 59, 0.72); color: #cbd5e1; font-size: 0.92rem; '
            f'font-weight: 700; border-bottom: 1px solid rgba(148, 163, 184, 0.14);">'
            f'{html.escape(str(column_name))}</th>'
        )
        for column_name in table.columns
    )

    body_rows: list[str] = []
    for row_index, (_, row) in enumerate(table.iterrows()):
        row_background = "rgba(15, 23, 42, 0.30)" if row_index % 2 == 0 else "rgba(15, 23, 42, 0.18)"
        row_cells = []
        for column_name in table.columns:
            display_value = html.escape(format_trade_log_cell(column_name, row[column_name]))
            cell_style = trade_log_cell_style(column_name, row[column_name])
            row_cells.append(f'<td style="{cell_style}">{display_value}</td>')
        body_rows.append(f'<tr style="background: {row_background};">{"".join(row_cells)}</tr>')

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 12px;
            overflow-x: auto;
            background: rgba(15, 23, 42, 0.42);
        ">
            <table style="width: 100%; border-collapse: collapse; text-align: center; margin: 0;">
                <thead>
                    <tr>{header_cells}</tr>
                </thead>
                <tbody>
                    {''.join(body_rows)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["build_trade_log_table", "render_trade_log_table"]

