from __future__ import annotations

import unittest

import pandas as pd
import streamlit as st

from charts.chart_core import INDICATOR_CHART_HEIGHT, MAIN_CHART_HEIGHT, VOLUME_MA_WINDOW, _build_price_dataframe, _build_volume_dataframe
from charts.renderers_parts.main import _resolve_main_chart_layout
from indicators.moving_averages import build_moving_average_dataframe
from state.parts.screener_state import close_screener_page, open_screener_page
from state.parts.session_defaults import initialize_session_state


def _build_sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=12, freq="D"),
            "open": [100 + index for index in range(12)],
            "high": [102 + index for index in range(12)],
            "low": [98 + index for index in range(12)],
            "close": [101 + index for index in range(12)],
            "volume": [1_000_000 + (index * 50_000) for index in range(12)],
        }
    )


class ChartDefaultTests(unittest.TestCase):
    def setUp(self) -> None:
        st.session_state.clear()

    def test_initialize_session_state_sets_bumi_and_visible_default_ema(self) -> None:
        initialize_session_state()
        self.assertEqual(st.session_state.symbol_input, "BUMI")
        self.assertEqual(st.session_state.current_app_page, "chart")
        self.assertEqual(st.session_state.screener_ema_period, 10)
        self.assertEqual(st.session_state.screener_interval_label, "1 hari")
        self.assertEqual(st.session_state.screener_period_label, "YTD")
        self.assertEqual(st.session_state.screener_selected_symbols, [])
        self.assertEqual(len(st.session_state.active_indicators), 1)
        self.assertEqual(st.session_state.active_indicators[0]["key"], "EMA")
        self.assertTrue(st.session_state.active_indicators[0]["visible"])

    def test_screener_page_state_can_open_and_close(self) -> None:
        initialize_session_state()
        open_screener_page()
        self.assertEqual(st.session_state.current_app_page, "screener")
        close_screener_page()
        self.assertEqual(st.session_state.current_app_page, "chart")

    def test_price_frame_keeps_volume_source_data(self) -> None:
        frame = _build_price_dataframe(_build_sample_frame())
        self.assertIn("volume", frame.columns)
        self.assertGreater(float(frame["volume"].sum()), 0.0)

    def test_volume_frame_contains_ma20_column(self) -> None:
        frame = _build_volume_dataframe(_build_sample_frame())
        line_name = f"Volume MA {VOLUME_MA_WINDOW}"
        self.assertIn(line_name, frame.columns)
        self.assertFalse(frame[line_name].dropna().empty)

    def test_default_ema_builder_returns_values(self) -> None:
        ema_frame = build_moving_average_dataframe(
            _build_sample_frame(),
            length=10,
            line_name="EMA 10",
            method="ema",
        )
        self.assertFalse(ema_frame.empty)
        self.assertIn("EMA 10", ema_frame.columns)

    def test_main_chart_layout_grows_with_visible_panel_indicators(self) -> None:
        total_height, main_ratio = _resolve_main_chart_layout(
            [
                {"key": "EMA", "visible": True},
                {"key": "RSI", "visible": True},
                {"key": "MACD", "visible": False},
                {"key": "ATR", "visible": True},
            ]
        )
        expected_total = MAIN_CHART_HEIGHT + (2 * INDICATOR_CHART_HEIGHT)
        self.assertEqual(total_height, expected_total)
        self.assertAlmostEqual(main_ratio, MAIN_CHART_HEIGHT / expected_total)


if __name__ == "__main__":
    unittest.main()
