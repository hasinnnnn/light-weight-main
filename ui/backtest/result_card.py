from __future__ import annotations

import pandas as pd
import streamlit as st

from backtest.config import display_backtest_period_label
from backtest.models import BacktestResult
from ui.backtest.sections.result_summary import (
    entry_target_label,
    format_lot,
    format_pct,
    format_rupiah,
    metric_tone,
    parameter_rows,
    render_metric_card,
    resolve_entry_lot,
    trade_outcome_extremes,
)
from ui.backtest.sections.trade_log import render_trade_log_table


def render_backtest_result_card(result: BacktestResult) -> None:
    """Render the translated backtest summary and trade log without extra charts."""
    entry_lot = resolve_entry_lot(result)
    max_profit, max_loss = trade_outcome_extremes(result)
    summary_metrics = [
        (
            "Return total",
            format_pct(result.metrics.total_return_pct, show_sign=True),
            metric_tone(result.metrics.total_return_pct),
        ),
        (
            "Laba bersih",
            format_rupiah(result.metrics.net_profit, show_sign=True),
            metric_tone(result.metrics.net_profit),
        ),
        (
            "Target entry",
            entry_target_label(result),
            "neutral",
        ),
        (
            "Persentase menang",
            format_pct(result.metrics.win_rate_pct),
            "positive"
            if result.metrics.win_rate_pct > 50
            else "negative"
            if result.metrics.win_rate_pct < 50
            else "neutral",
        ),
        (
            "Drawdown maksimum",
            format_pct(-result.metrics.max_drawdown_pct),
            metric_tone(-result.metrics.max_drawdown_pct),
        ),
        (
            "Total transaksi",
            str(result.metrics.total_trades),
            "neutral",
        ),
        (
            "Transaksi profit",
            str(result.metrics.winning_trades),
            "positive" if result.metrics.winning_trades > 0 else "neutral",
        ),
        (
            "Transaksi loss",
            str(result.metrics.losing_trades),
            "negative" if result.metrics.losing_trades > 0 else "neutral",
        ),
        (
            "Rata-rata profit",
            format_rupiah(result.metrics.average_win, show_sign=True),
            metric_tone(result.metrics.average_win),
        ),
        (
            "Rata-rata rugi",
            format_rupiah(result.metrics.average_loss, show_sign=True),
            metric_tone(result.metrics.average_loss),
        ),
        (
            "Ekspektansi",
            format_rupiah(result.metrics.expectancy, show_sign=True),
            metric_tone(result.metrics.expectancy),
        ),
        (
            "Max profit",
            format_rupiah(max_profit, show_sign=True),
            metric_tone(max_profit),
        ),
        (
            "Max loss",
            format_rupiah(max_loss, show_sign=True),
            metric_tone(max_loss),
        ),
    ]
    if entry_lot is not None:
        summary_metrics.insert(
            3,
            (
                "Lot per entry",
                format_lot(entry_lot),
                "neutral",
            ),
        )

    with st.container(border=True):
        st.subheader(f"Keterangan Backtest - {result.strategy_label}")
        st.caption(
            f"{result.symbol}  |  {result.interval_label}  |  "
            f"Periode mengikuti chart aktif ({display_backtest_period_label(result.period_label)})"
        )

        for row_start in range(0, len(summary_metrics), 4):
            metric_columns = st.columns(4)
            for column, metric in zip(metric_columns, summary_metrics[row_start : row_start + 4]):
                render_metric_card(column, metric[0], metric[1], metric[2])

        capital_columns = st.columns(2)
        render_metric_card(capital_columns[0], "Modal awal", format_rupiah(result.initial_capital), "neutral")
        render_metric_card(
            capital_columns[1],
            "Ekuitas akhir",
            format_rupiah(result.final_equity),
            metric_tone(result.final_equity - result.initial_capital),
        )

        st.markdown(f"**Aturan entry:** {result.entry_rule_summary}")
        st.markdown(f"**Aturan exit:** {result.exit_rule_summary}")

        parameter_frame = pd.concat(
            [
                parameter_rows(result.general_params, "Umum"),
                parameter_rows(result.strategy_params, result.strategy_label),
            ],
            ignore_index=True,
        )
        with st.expander("Parameter aktif", expanded=False):
            st.dataframe(parameter_frame, use_container_width=True, hide_index=True)

    st.markdown("**Log transaksi**")
    if result.trade_log.empty:
        st.info("Belum ada transaksi yang terbentuk pada periode ini.")
    else:
        render_trade_log_table(result)


__all__ = ["render_backtest_result_card"]



