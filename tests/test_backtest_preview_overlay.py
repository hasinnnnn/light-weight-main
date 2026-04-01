from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import pandas as pd

from charts.renderers_parts.overlays import _render_overlay_indicator


class BacktestPreviewOverlayTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "time": pd.Timestamp("2026-03-01"),
                    "open": 100.0,
                    "high": 105.0,
                    "low": 99.0,
                    "close": 104.0,
                    "volume": 1000.0,
                },
                {
                    "time": pd.Timestamp("2026-03-02"),
                    "open": 104.0,
                    "high": 106.0,
                    "low": 103.0,
                    "close": 105.0,
                    "volume": 1200.0,
                },
            ]
        )

    def _line_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"time": pd.Timestamp("2026-03-01"), "EMA 10": 101.0},
                {"time": pd.Timestamp("2026-03-02"), "EMA 10": 102.0},
            ]
        )

    def _marker_payload(self) -> list[dict[str, object]]:
        return [
            {
                "time": pd.Timestamp("2026-03-02"),
                "position": "below",
                "shape": "arrow_up",
                "color": "#22c55e",
                "text": "BUY EMA",
            }
        ]

    def test_backtest_preview_ma_does_not_render_preview_trade_markers(self) -> None:
        chart = Mock()
        line = Mock()
        chart.create_line.return_value = line

        with patch("charts.renderers_parts.overlays._build_moving_average_dataframe", return_value=self._line_frame()), patch(
            "charts.renderers_parts.overlays._build_pullback_moving_average_trade_markers",
            return_value=self._marker_payload(),
        ):
            _render_overlay_indicator(
                chart,
                self._frame(),
                {
                    "key": "MA",
                    "params": {"length": 200},
                    "colors": {},
                    "visible": True,
                    "source": "backtest",
                },
            )

        chart.marker.assert_not_called()
        line.set.assert_called_once()
        line.marker_list.assert_not_called()

    def test_regular_ema_indicator_keeps_trade_markers(self) -> None:
        chart = Mock()
        line = Mock()
        chart.create_line.return_value = line

        with patch("charts.renderers_parts.overlays._build_moving_average_dataframe", return_value=self._line_frame()), patch(
            "charts.renderers_parts.overlays._build_pullback_moving_average_trade_markers",
            return_value=self._marker_payload(),
        ):
            _render_overlay_indicator(
                chart,
                self._frame(),
                {
                    "key": "EMA",
                    "params": {"length": 10},
                    "colors": {},
                    "visible": True,
                },
            )

        chart.marker.assert_not_called()
        line.marker_list.assert_called_once_with(self._marker_payload())


if __name__ == "__main__":
    unittest.main()
