from __future__ import annotations

from typing import Any

import pandas as pd


def _render_backtest_trade_markers(chart: Any, trade_log: pd.DataFrame | None) -> None:
    """Render buy and sell markers directly on the main candle series."""
    if trade_log is None or trade_log.empty:
        return

    for row in trade_log.itertuples(index=False):
        entry_time = getattr(row, "entry_datetime", None)
        if entry_time is not None and str(entry_time).strip():
            chart.marker(
                time=entry_time,
                position="below",
                shape="arrow_up",
                color="#22c55e",
                text="BUY",
            )

        exit_time = getattr(row, "exit_datetime", None)
        if exit_time is not None and str(exit_time).strip():
            chart.marker(
                time=exit_time,
                position="above",
                shape="arrow_down",
                color="#ef4444",
                text="SELL",
            )


__all__ = ["_render_backtest_trade_markers"]
