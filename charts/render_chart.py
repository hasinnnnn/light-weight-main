from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from backtest.models import BacktestResult


class BacktestChartError(Exception):
    """Raised when Plotly is not available for backtest rendering."""


def _get_plotly_modules() -> tuple[Any, Any]:
    """Import Plotly lazily so the rest of the app can still load without it."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ModuleNotFoundError as exc:
        raise BacktestChartError(
            "Package `plotly` belum terpasang. Install dulu dengan `pip install -r requirements.txt`."
        ) from exc
    return go, make_subplots


def _trade_markers(trade_log: pd.DataFrame, side: str) -> pd.DataFrame:
    """Return one trade-log slice for entry or exit markers."""
    if trade_log.empty:
        return trade_log.iloc[0:0]
    if side == "buy":
        columns = {"entry_datetime": "time", "entry_price": "price"}
    else:
        columns = {"exit_datetime": "time", "exit_price": "price"}
    marker_frame = trade_log[list(columns)].rename(columns=columns).copy()
    marker_frame["time"] = pd.to_datetime(marker_frame["time"], errors="coerce")
    marker_frame["price"] = pd.to_numeric(marker_frame["price"], errors="coerce")
    return marker_frame.dropna(subset=["time", "price"])


def render_backtest_chart(result: BacktestResult) -> None:
    """Render the Plotly backtest chart below the main lightweight chart."""
    go, make_subplots = _get_plotly_modules()

    chart_frame = result.chart_frame.copy()
    chart_frame["time"] = pd.to_datetime(chart_frame["time"], errors="coerce")
    chart_frame = chart_frame.dropna(subset=["time"]).reset_index(drop=True)
    if chart_frame.empty:
        return

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.68, 0.32],
        subplot_titles=[f"Backtest - {result.strategy_label}", result.strategy_label],
    )

    figure.add_trace(
        go.Candlestick(
            x=chart_frame["time"],
            open=chart_frame["open"],
            high=chart_frame["high"],
            low=chart_frame["low"],
            close=chart_frame["close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    buy_markers = _trade_markers(result.trade_log, side="buy")
    if not buy_markers.empty:
        figure.add_trace(
            go.Scatter(
                x=buy_markers["time"],
                y=buy_markers["price"],
                mode="markers",
                name="Buy",
                marker={"symbol": "triangle-up", "size": 11, "color": "#22c55e"},
            ),
            row=1,
            col=1,
        )

    sell_markers = _trade_markers(result.trade_log, side="sell")
    if not sell_markers.empty:
        figure.add_trace(
            go.Scatter(
                x=sell_markers["time"],
                y=sell_markers["price"],
                mode="markers",
                name="Sell",
                marker={"symbol": "triangle-down", "size": 11, "color": "#ef4444"},
            ),
            row=1,
            col=1,
        )

    if result.strategy_key == "RSI":
        figure.add_trace(
            go.Scatter(
                x=chart_frame["time"],
                y=chart_frame["rsi"],
                mode="lines",
                name="RSI",
                line={"color": "#8b5cf6", "width": 2},
            ),
            row=2,
            col=1,
        )
        figure.add_hline(
            y=float(result.strategy_params["oversold_level"]),
            line_dash="dot",
            line_color="#22c55e",
            row=2,
            col=1,
        )
        figure.add_hline(
            y=float(result.strategy_params["overbought_level"]),
            line_dash="dot",
            line_color="#ef4444",
            row=2,
            col=1,
        )
        figure.update_yaxes(range=[0, 100], row=2, col=1)
    elif result.strategy_key == "MACD":
        histogram_color = [
            "rgba(34, 197, 94, 0.55)" if value >= 0 else "rgba(239, 68, 68, 0.55)"
            for value in chart_frame["macd_histogram"].fillna(0.0)
        ]
        figure.add_trace(
            go.Bar(
                x=chart_frame["time"],
                y=chart_frame["macd_histogram"],
                name="Histogram",
                marker={"color": histogram_color},
            ),
            row=2,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=chart_frame["time"],
                y=chart_frame["macd"],
                mode="lines",
                name="MACD",
                line={"color": "#38bdf8", "width": 2},
            ),
            row=2,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=chart_frame["time"],
                y=chart_frame["macd_signal"],
                mode="lines",
                name="Signal",
                line={"color": "#f59e0b", "width": 2},
            ),
            row=2,
            col=1,
        )

    figure.update_layout(
        height=760,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0.0},
        paper_bgcolor="#071426",
        plot_bgcolor="#071426",
        font={"color": "#d6deeb", "family": "Trebuchet MS"},
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.12)")
    st.plotly_chart(figure, use_container_width=True)
