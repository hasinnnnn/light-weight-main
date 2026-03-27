from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from backtest.engine import run_backtest
from backtest.strategies.base_strategy import StrategyPreparation
from backtest.strategies.break_ma_strategy import prepare_break_ma_strategy
from backtest.strategies.macd_strategy import prepare_macd_strategy
from backtest.strategies.rsi_strategy import prepare_rsi_strategy


class BacktestIntrabarExitTests(unittest.TestCase):
    def _general_params(self) -> dict[str, float | int | bool | str]:
        return {
            "initial_capital": 10_000_000.0,
            "position_sizing_mode": "fixed_nominal",
            "position_size_value": 1_000_000.0,
            "buy_fee_pct": 0.0,
            "sell_fee_pct": 0.0,
            "slippage_pct": 0.0,
            "stop_loss_pct": 3.0,
            "take_profit_pct": 0.0,
            "trailing_stop_pct": 0.0,
            "max_holding_bars": 0,
            "cooldown_bars": 0,
            "show_indicator_preview": True,
        }

    def test_stop_loss_executes_at_stop_level_on_same_candle(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "time": "2026-02-17",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1_000.0,
                    "entry_signal": True,
                    "exit_signal": False,
                    "indicator_ready": True,
                },
                {
                    "time": "2026-02-18",
                    "open": 100.0,
                    "high": 100.5,
                    "low": 96.0,
                    "close": 98.0,
                    "volume": 1_200.0,
                    "entry_signal": False,
                    "exit_signal": False,
                    "indicator_ready": True,
                },
                {
                    "time": "2026-02-19",
                    "open": 98.0,
                    "high": 99.0,
                    "low": 97.0,
                    "close": 98.0,
                    "volume": 900.0,
                    "entry_signal": False,
                    "exit_signal": False,
                    "indicator_ready": True,
                },
            ]
        )

        def _dummy_preparer(_source_frame: pd.DataFrame, _params: dict[str, object]) -> StrategyPreparation:
            return StrategyPreparation(
                frame=frame.copy(),
                warmup_bars=0,
                entry_rule_summary="entry",
                exit_rule_summary="exit",
                risk_management_enabled=True,
            )

        with patch.dict("backtest.engine.PREPARERS", {"BREAK_EMA": _dummy_preparer}, clear=False):
            result = run_backtest(
                data=frame[["time", "open", "high", "low", "close", "volume"]].copy(),
                strategy_key="BREAK_EMA",
                general_params=self._general_params(),
                strategy_params={"ema_period": 10, "exit_mode": "tp_sl_trailing_only"},
                symbol="TEST",
                interval_label="1 hari",
                period_label="YTD",
                use_lot_sizing=False,
            )

        self.assertEqual(len(result.trade_log), 1)
        trade = result.trade_log.iloc[0]
        self.assertEqual(trade["exit_reason"], "stop_loss")
        self.assertAlmostEqual(float(trade["entry_price"]), 100.0, places=6)
        self.assertAlmostEqual(float(trade["exit_price"]), 97.0, places=6)
        self.assertAlmostEqual(float(trade["pnl_pct"]), -3.0, places=6)

    def test_strategy_exit_level_executes_on_same_candle(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "time": "2026-02-17",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1_000.0,
                    "entry_signal": True,
                    "exit_signal": False,
                    "strategy_exit_price": pd.NA,
                    "indicator_ready": True,
                },
                {
                    "time": "2026-02-18",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 98.0,
                    "close": 98.5,
                    "volume": 1_200.0,
                    "entry_signal": False,
                    "exit_signal": True,
                    "strategy_exit_price": 99.0,
                    "indicator_ready": True,
                },
                {
                    "time": "2026-02-19",
                    "open": 98.0,
                    "high": 99.0,
                    "low": 97.0,
                    "close": 98.0,
                    "volume": 900.0,
                    "entry_signal": False,
                    "exit_signal": False,
                    "strategy_exit_price": pd.NA,
                    "indicator_ready": True,
                },
            ]
        )

        def _dummy_preparer(_source_frame: pd.DataFrame, _params: dict[str, object]) -> StrategyPreparation:
            return StrategyPreparation(
                frame=frame.copy(),
                warmup_bars=0,
                entry_rule_summary="entry",
                exit_rule_summary="exit",
                risk_management_enabled=False,
                strategy_exit_price_column="strategy_exit_price",
            )

        with patch.dict("backtest.engine.PREPARERS", {"BREAK_EMA": _dummy_preparer}, clear=False):
            result = run_backtest(
                data=frame[["time", "open", "high", "low", "close", "volume"]].copy(),
                strategy_key="BREAK_EMA",
                general_params=self._general_params(),
                strategy_params={"ema_period": 10, "exit_mode": "ema_breakdown"},
                symbol="TEST",
                interval_label="1 hari",
                period_label="YTD",
                use_lot_sizing=False,
            )

        self.assertEqual(len(result.trade_log), 1)
        trade = result.trade_log.iloc[0]
        self.assertEqual(trade["exit_reason"], "strategy_exit")
        self.assertAlmostEqual(float(trade["entry_price"]), 100.0, places=6)
        self.assertAlmostEqual(float(trade["exit_price"]), 99.0, places=6)
        self.assertAlmostEqual(float(trade["pnl_pct"]), -1.0, places=6)

    def test_tp_sl_mode_keeps_strategy_signal_active(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "time": "2026-02-17",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1_000.0,
                    "entry_signal": True,
                    "exit_signal": False,
                    "strategy_exit_price": pd.NA,
                    "indicator_ready": True,
                },
                {
                    "time": "2026-02-18",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 98.0,
                    "close": 98.5,
                    "volume": 1_200.0,
                    "entry_signal": False,
                    "exit_signal": True,
                    "strategy_exit_price": 99.0,
                    "indicator_ready": True,
                },
                {
                    "time": "2026-02-19",
                    "open": 98.0,
                    "high": 99.0,
                    "low": 97.0,
                    "close": 98.0,
                    "volume": 900.0,
                    "entry_signal": False,
                    "exit_signal": False,
                    "strategy_exit_price": pd.NA,
                    "indicator_ready": True,
                },
            ]
        )
        params = self._general_params()
        params["stop_loss_pct"] = 0.0

        def _dummy_preparer(_source_frame: pd.DataFrame, _params: dict[str, object]) -> StrategyPreparation:
            return StrategyPreparation(
                frame=frame.copy(),
                warmup_bars=0,
                entry_rule_summary="entry",
                exit_rule_summary="exit",
                risk_management_enabled=True,
                strategy_exit_price_column="strategy_exit_price",
            )

        with patch.dict("backtest.engine.PREPARERS", {"BREAK_EMA": _dummy_preparer}, clear=False):
            result = run_backtest(
                data=frame[["time", "open", "high", "low", "close", "volume"]].copy(),
                strategy_key="BREAK_EMA",
                general_params=params,
                strategy_params={"ema_period": 10, "exit_mode": "tp_sl_trailing_only"},
                symbol="TEST",
                interval_label="1 hari",
                period_label="YTD",
                use_lot_sizing=False,
            )

        self.assertEqual(len(result.trade_log), 1)
        trade = result.trade_log.iloc[0]
        self.assertEqual(trade["exit_reason"], "strategy_exit")
        self.assertAlmostEqual(float(trade["exit_price"]), 99.0, places=6)


class StrategyModePreparationTests(unittest.TestCase):
    def _strategy_frame(self) -> pd.DataFrame:
        close_values = [100 + ((index % 6) - 3) * 2 + index * 0.4 for index in range(80)]
        return pd.DataFrame(
            {
                "time": pd.date_range("2026-01-01", periods=len(close_values), freq="D"),
                "open": close_values,
                "high": [value + 2 for value in close_values],
                "low": [value - 2 for value in close_values],
                "close": close_values,
                "volume": [1_000 + (index * 10) for index in range(len(close_values))],
            }
        )

    def test_rsi_fixed_tp_sl_keeps_risk_management_enabled(self) -> None:
        prepared = prepare_rsi_strategy(
            self._strategy_frame(),
            {
                "rsi_period": 14,
                "oversold_level": 30.0,
                "overbought_level": 70.0,
                "exit_rsi_level": 60.0,
                "trend_filter_enabled": True,
                "trend_ma_period": 50,
                "entry_mode": "cross_up_oversold",
                "exit_mode": "fixed_tp_sl",
            },
        )
        self.assertTrue(prepared.risk_management_enabled)
        self.assertIn("stop loss", prepared.exit_rule_summary.lower())

    def test_macd_fixed_tp_sl_keeps_risk_management_enabled(self) -> None:
        prepared = prepare_macd_strategy(
            self._strategy_frame(),
            {
                "macd_fast_period": 12,
                "macd_slow_period": 26,
                "macd_signal_period": 9,
                "trend_filter_enabled": True,
                "trend_ma_period": 50,
                "entry_mode": "macd_cross_up_signal",
                "exit_mode": "fixed_tp_sl",
            },
        )
        self.assertTrue(prepared.risk_management_enabled)
        self.assertIn("stop loss", prepared.exit_rule_summary.lower())

    def test_break_ma_default_mode_uses_ma_rule_summary(self) -> None:
        prepared = prepare_break_ma_strategy(
            self._strategy_frame(),
            {
                "ma_period": 200,
                "exit_mode": "ma_breakdown",
                "breakdown_confirm_mode": "body_breakdown",
            },
        )
        self.assertFalse(prepared.risk_management_enabled)
        self.assertEqual(prepared.strategy_exit_price_column, "strategy_exit_price")
        self.assertIn("MA 200", prepared.entry_rule_summary)
        self.assertIn("MA 200", prepared.exit_rule_summary)


if __name__ == "__main__":
    unittest.main()


