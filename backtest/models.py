from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Trade:
    """One completed backtest trade."""

    entry_datetime: str
    entry_price: float
    exit_datetime: str
    exit_price: float
    qty: float
    pnl_nominal: float
    pnl_pct: float
    exit_reason: str
    bars_held: int
    buy_fee: float
    sell_fee: float


@dataclass(frozen=True)
class BacktestMetrics:
    """Compact summary metrics derived from one backtest run."""

    total_return_pct: float
    net_profit: float
    win_rate_pct: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    expectancy: float


@dataclass
class BacktestResult:
    """Serializable container for everything needed by the UI layer."""

    strategy_key: str
    strategy_label: str
    symbol: str
    interval_label: str
    period_label: str
    uses_lot_sizing: bool
    lot_size: int
    general_params: dict[str, object]
    strategy_params: dict[str, object]
    metrics: BacktestMetrics
    trade_log: pd.DataFrame
    equity_curve: pd.DataFrame
    chart_frame: pd.DataFrame
    entry_rule_summary: str
    exit_rule_summary: str
    initial_capital: float
    final_equity: float

