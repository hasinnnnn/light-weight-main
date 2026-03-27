from __future__ import annotations

import unittest
from unittest.mock import Mock

import pandas as pd

from charts.renderers_parts.backtest import _render_backtest_trade_markers


class BacktestMarkerTests(unittest.TestCase):
    def test_backtest_marker_renderer_attaches_markers_to_main_chart(self) -> None:
        trade_log = pd.DataFrame(
            [
                {
                    "entry_datetime": "2026-03-10",
                    "entry_price": 210.0,
                    "exit_datetime": "2026-03-12",
                    "exit_price": 225.0,
                }
            ]
        )
        chart = Mock()

        _render_backtest_trade_markers(chart=chart, trade_log=trade_log)

        self.assertEqual(chart.marker.call_count, 2)
        buy_call = chart.marker.call_args_list[0].kwargs
        sell_call = chart.marker.call_args_list[1].kwargs

        self.assertEqual(buy_call["time"], "2026-03-10")
        self.assertEqual(buy_call["position"], "below")
        self.assertEqual(buy_call["shape"], "arrow_up")
        self.assertEqual(buy_call["text"], "BUY")

        self.assertEqual(sell_call["time"], "2026-03-12")
        self.assertEqual(sell_call["position"], "above")
        self.assertEqual(sell_call["shape"], "arrow_down")
        self.assertEqual(sell_call["text"], "SELL")


if __name__ == "__main__":
    unittest.main()
