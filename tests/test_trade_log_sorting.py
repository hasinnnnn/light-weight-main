from __future__ import annotations

import unittest

import pandas as pd

from backtest.models import BacktestMetrics, BacktestResult
from ui.backtest.sections.trade_log import build_trade_log_table


class TradeLogTableTests(unittest.TestCase):
    def _build_result(self) -> BacktestResult:
        trade_log = pd.DataFrame(
            [
                {
                    "trade_no": 1,
                    "entry_datetime": "2026-02-10",
                    "entry_price": 100.0,
                    "exit_datetime": "2026-02-12",
                    "exit_price": 110.0,
                    "qty": 1000.0,
                    "pnl_nominal": 10000.0,
                    "pnl_pct": 10.0,
                    "exit_reason": "take_profit",
                },
                {
                    "trade_no": 2,
                    "entry_datetime": "2026-02-13",
                    "entry_price": 120.0,
                    "exit_datetime": "2026-02-15",
                    "exit_price": 108.0,
                    "qty": 1000.0,
                    "pnl_nominal": -12000.0,
                    "pnl_pct": -10.0,
                    "exit_reason": "stop_loss",
                },
                {
                    "trade_no": 3,
                    "entry_datetime": "2026-02-16",
                    "entry_price": 130.0,
                    "exit_datetime": "2026-02-18",
                    "exit_price": 137.8,
                    "qty": 1000.0,
                    "pnl_nominal": 7800.0,
                    "pnl_pct": 6.0,
                    "exit_reason": "strategy_exit",
                },
            ]
        )
        metrics = BacktestMetrics(
            total_return_pct=5.8,
            net_profit=5800.0,
            win_rate_pct=66.67,
            max_drawdown_pct=10.0,
            total_trades=3,
            winning_trades=2,
            losing_trades=1,
            average_win=8900.0,
            average_loss=-12000.0,
            expectancy=1933.33,
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
            final_equity=10_005_800.0,
        )

    def test_trade_log_uses_latest_exit_first(self) -> None:
        table = build_trade_log_table(self._build_result())
        self.assertEqual(list(table["No."]), [3, 2, 1])

    def test_trade_log_shows_lot_without_quantity_when_lot_sizing_is_used(self) -> None:
        table = build_trade_log_table(self._build_result())
        self.assertIn("Lot", table.columns)
        self.assertNotIn("Kuantitas", table.columns)

    def test_trade_log_adds_total_entry_and_total_exit_columns(self) -> None:
        table = build_trade_log_table(self._build_result())
        self.assertIn("Total entry", table.columns)
        self.assertIn("Total exit", table.columns)
        latest_trade = table.iloc[0]
        self.assertEqual(latest_trade["Total entry"], 130000.0)
        self.assertEqual(latest_trade["Total exit"], 137800.0)

    def test_trade_log_combines_entry_and_exit_dates_into_single_column(self) -> None:
        table = build_trade_log_table(self._build_result())
        self.assertIn("Tanggal", table.columns)
        self.assertNotIn("Waktu entry", table.columns)
        self.assertNotIn("Waktu exit", table.columns)
        self.assertNotIn("entry_datetime", table.columns)
        self.assertNotIn("exit_datetime", table.columns)
        self.assertEqual(table.iloc[0]["Tanggal"], "16 feb 2026 - 18 feb 2026")


if __name__ == "__main__":
    unittest.main()

