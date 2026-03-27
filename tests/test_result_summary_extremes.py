from __future__ import annotations

import unittest

import pandas as pd

from backtest.models import BacktestMetrics, BacktestResult
from ui.backtest.sections.result_summary import trade_outcome_extremes


class ResultSummaryTradeExtremesTests(unittest.TestCase):
    def _build_result(self, trade_log: pd.DataFrame) -> BacktestResult:
        metrics = BacktestMetrics(
            total_return_pct=5.0,
            net_profit=1000.0,
            win_rate_pct=50.0,
            max_drawdown_pct=2.5,
            total_trades=len(trade_log),
            winning_trades=1,
            losing_trades=1,
            average_win=1500.0,
            average_loss=-500.0,
            expectancy=500.0,
        )
        return BacktestResult(
            strategy_key="BREAK_EMA",
            strategy_label="Break EMA",
            symbol="BUMI",
            interval_label="1 hari",
            period_label="YTD",
            uses_lot_sizing=True,
            lot_size=100,
            general_params={},
            strategy_params={},
            metrics=metrics,
            trade_log=trade_log,
            equity_curve=pd.DataFrame(),
            chart_frame=pd.DataFrame(),
            entry_rule_summary="entry",
            exit_rule_summary="exit",
            initial_capital=10_000_000.0,
            final_equity=10_001_000.0,
        )

    def test_trade_outcome_extremes_reads_biggest_profit_and_loss(self) -> None:
        trade_log = pd.DataFrame(
            [
                {"pnl_nominal": 125000.0},
                {"pnl_nominal": -42000.0},
                {"pnl_nominal": 98000.0},
                {"pnl_nominal": -175000.0},
            ]
        )
        max_profit, max_loss = trade_outcome_extremes(self._build_result(trade_log))
        self.assertEqual(max_profit, 125000.0)
        self.assertEqual(max_loss, -175000.0)

    def test_trade_outcome_extremes_returns_zero_when_trade_log_has_no_matching_side(self) -> None:
        trade_log = pd.DataFrame([{"pnl_nominal": -50000.0}, {"pnl_nominal": -10000.0}])
        max_profit, max_loss = trade_outcome_extremes(self._build_result(trade_log))
        self.assertEqual(max_profit, 0.0)
        self.assertEqual(max_loss, -50000.0)


if __name__ == "__main__":
    unittest.main()
