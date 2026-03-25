from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from backtest.models import BacktestMetrics, Trade


def build_trade_log(trades: list[Trade]) -> pd.DataFrame:
    """Convert completed trades into one UI-friendly dataframe."""
    if not trades:
        return pd.DataFrame(
            columns=[
                "trade_no",
                "entry_datetime",
                "entry_price",
                "exit_datetime",
                "exit_price",
                "qty",
                "pnl_nominal",
                "pnl_pct",
                "exit_reason",
            ]
        )

    frame = pd.DataFrame(asdict(trade) for trade in trades)
    frame.insert(0, "trade_no", range(1, len(frame) + 1))
    return frame[
        [
            "trade_no",
            "entry_datetime",
            "entry_price",
            "exit_datetime",
            "exit_price",
            "qty",
            "pnl_nominal",
            "pnl_pct",
            "exit_reason",
        ]
    ].copy()


def calculate_backtest_metrics(
    equity_curve: pd.DataFrame,
    trades: list[Trade],
    initial_capital: float,
) -> BacktestMetrics:
    """Compute the summary statistics shown in the result card."""
    if equity_curve.empty:
        final_equity = float(initial_capital)
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_curve["equity"].iloc[-1])
        running_peak = equity_curve["equity"].cummax().replace(0, pd.NA)
        drawdown = equity_curve["equity"].div(running_peak).sub(1.0).fillna(0.0)
        max_drawdown_pct = abs(float(drawdown.min()) * 100.0)

    total_return_pct = ((final_equity / float(initial_capital)) - 1.0) * 100.0
    net_profit = final_equity - float(initial_capital)
    total_trades = len(trades)

    pnl_values = [float(trade.pnl_nominal) for trade in trades]
    winning_pnls = [value for value in pnl_values if value > 0]
    losing_pnls = [value for value in pnl_values if value < 0]
    winning_trades = len(winning_pnls)
    losing_trades = len(losing_pnls)
    win_rate_pct = (winning_trades / total_trades * 100.0) if total_trades else 0.0
    average_win = sum(winning_pnls) / winning_trades if winning_pnls else 0.0
    average_loss = sum(losing_pnls) / losing_trades if losing_pnls else 0.0
    expectancy = sum(pnl_values) / total_trades if total_trades else 0.0

    return BacktestMetrics(
        total_return_pct=total_return_pct,
        net_profit=net_profit,
        win_rate_pct=win_rate_pct,
        max_drawdown_pct=max_drawdown_pct,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        average_win=average_win,
        average_loss=average_loss,
        expectancy=expectancy,
    )

