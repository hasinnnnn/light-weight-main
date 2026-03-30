from __future__ import annotations

import unittest
from types import SimpleNamespace

import pandas as pd

from indicators.candle_patterns import (
    ALL_CANDLE_PATTERN_KEYS,
    detect_candle_patterns,
    get_default_candle_pattern_params,
    summarize_candle_patterns,
)
from indicators.chart_patterns import (
    ALL_CHART_PATTERN_KEYS,
    detect_chart_patterns,
    get_default_chart_pattern_params,
    summarize_chart_patterns,
)
from indicators.fibonacci import build_fibonacci_analysis
from indicators.moving_averages import (
    build_moving_average_overlay_series_specs,
    build_pullback_moving_average_trade_markers,
)
from indicators.support_resistance import (
    describe_nearest_support_resistance,
    describe_strong_support_resistance,
)
from indicators.stochastic import build_stochastic_dataframe, build_stochastic_rsi_dataframe
from indicators.trendlines import describe_auto_trendlines
from ui.market_insight_parts.sections.moving_averages import build_ema_section, build_sma_section
from ui.market_insight_parts.sections.oscillators import build_macd_section, build_rsi_section



def _build_sample_frame() -> pd.DataFrame:
    rows = []
    closes = [100, 103, 101, 105, 102, 108, 104, 110, 107, 112, 109, 114, 111, 116, 113, 118]
    for index, close in enumerate(closes):
        rows.append(
            {
                "time": pd.Timestamp("2026-01-01") + pd.Timedelta(days=index),
                "open": close - 1,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "volume": 1000 + (index * 25),
            }
        )
    return pd.DataFrame(rows)



def _build_pullback_frame() -> pd.DataFrame:
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 106, 106, 104, 103]
    rows = []
    for index, close in enumerate(closes):
        low = close - 1.0
        high = close + 1.5
        if index == 9:
            low = 104.9
            high = 107.5
        rows.append(
            {
                "time": pd.Timestamp("2026-02-01") + pd.Timedelta(days=index),
                "open": close - 0.5,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1500 + (index * 10),
            }
        )
    return pd.DataFrame(rows)


def _build_flat_frame(length: int = 20) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-03-01", periods=length, freq="D"),
            "open": [100.0] * length,
            "high": [100.0] * length,
            "low": [100.0] * length,
            "close": [100.0] * length,
            "volume": [1000.0] * length,
        }
    )


class IndicatorFacadeTests(unittest.TestCase):
    def test_candle_pattern_defaults_cover_all_pattern_toggles(self) -> None:
        defaults = get_default_candle_pattern_params()
        for pattern_key in ALL_CANDLE_PATTERN_KEYS:
            self.assertIn(f"show_{pattern_key}", defaults)

    def test_chart_pattern_defaults_cover_all_pattern_toggles(self) -> None:
        defaults = get_default_chart_pattern_params()
        for pattern_key in ALL_CHART_PATTERN_KEYS:
            self.assertIn(f"show_{pattern_key}", defaults)

    def test_candle_pattern_summary_returns_expected_shape(self) -> None:
        frame = _build_sample_frame()
        events = detect_candle_patterns(frame, {"lookback": 120})
        summary = summarize_candle_patterns(frame, {"lookback": 120})
        self.assertTrue(hasattr(events, "empty"))
        self.assertIn("events", summary)
        self.assertIn("latest_by_direction", summary)

    def test_chart_pattern_summary_returns_expected_shape(self) -> None:
        frame = _build_sample_frame()
        patterns = detect_chart_patterns(frame, {"lookback": 120})
        summary = summarize_chart_patterns(frame, {"lookback": 120})
        self.assertIsInstance(patterns, list)
        self.assertIn("patterns", summary)
        self.assertIn("latest_by_direction", summary)

    def test_fibonacci_analysis_returns_none_or_payload(self) -> None:
        frame = _build_sample_frame()
        analysis = build_fibonacci_analysis(
            frame,
            params={"lookback": 120, "swing_direction": "low_to_high", "swing_mode": "balanced"},
            colors={},
        )
        self.assertTrue(analysis is None or isinstance(analysis, dict))

    def test_moving_average_specs_return_overlay_definitions(self) -> None:
        specs = build_moving_average_overlay_series_specs(
            indicator_key="EMA_CROSS",
            params={"fast_length": 9, "slow_length": 21},
            colors={},
            ema_colors=["#1", "#2", "#3"],
            ma_colors=["#4", "#5", "#6"],
        )
        self.assertEqual(len(specs), 2)

    def test_pullback_moving_average_markers_follow_backtest_rule_flow(self) -> None:
        markers = build_pullback_moving_average_trade_markers(
            _build_pullback_frame(),
            length=5,
            method="ema",
            label="EMA",
        )
        marker_texts = [str(marker["text"]) for marker in markers]
        self.assertEqual(marker_texts, ["BUY EMA"])

    def test_ema_section_reports_pullback_entry_setup(self) -> None:
        result = SimpleNamespace(data=_build_pullback_frame(), current_price=103.0)
        html = build_ema_section(result, {"length": 5}, {"line": "#38bdf8"})
        self.assertIsNotNone(html)
        self.assertIn("Belum pas buat entry", html)
        self.assertIn("Belum ada trigger entry", html)

    def test_ema_section_reports_entry_trigger_when_pullback_is_ready(self) -> None:
        ready_frame = _build_pullback_frame().iloc[:10].copy()
        result = SimpleNamespace(data=ready_frame, current_price=float(ready_frame.iloc[-1]["close"]))
        html = build_ema_section(result, {"length": 5}, {"line": "#38bdf8"})
        self.assertIsNotNone(html)
        self.assertIn("Bisa entry sekarang", html)

    def test_sma_section_reports_waiting_when_pullback_is_not_ready(self) -> None:
        result = SimpleNamespace(data=_build_sample_frame(), current_price=118.0)
        html = build_sma_section(result, {"length": 5}, {"line": "#f59e0b"})
        self.assertIsNotNone(html)
        self.assertIn("Belum pas buat entry", html)

    def test_rsi_section_builds_indicator_note(self) -> None:
        result = SimpleNamespace(data=_build_sample_frame(), current_price=118.0)
        html = build_rsi_section(result, {"length": 14}, {"line": "#a78bfa"})
        self.assertIsNotNone(html)
        self.assertIn("RSI", html)
        self.assertIn("RSI Saat Ini", html)

    def test_macd_section_builds_indicator_note(self) -> None:
        result = SimpleNamespace(data=_build_sample_frame(), current_price=118.0)
        html = build_macd_section(
            result,
            {"fast_length": 12, "slow_length": 26, "signal_length": 9},
            {"macd": "#38bdf8", "histogram_up": "#22c55e", "histogram_down": "#ef4444"},
        )
        self.assertIsNotNone(html)
        self.assertIn("MACD", html)
        self.assertIn("MACD vs Signal", html)

    def test_stochastic_dataframe_handles_flat_prices(self) -> None:
        frame = _build_flat_frame()
        result = build_stochastic_dataframe(frame, k_length=14, k_smoothing=3, d_length=3)
        self.assertTrue(hasattr(result, "empty"))

    def test_stochastic_rsi_dataframe_handles_flat_prices(self) -> None:
        frame = _build_flat_frame()
        result = build_stochastic_rsi_dataframe(frame, rsi_length=14, stoch_length=14, k_smoothing=3, d_length=3)
        self.assertTrue(hasattr(result, "empty"))

    def test_nearest_support_resistance_does_not_crash(self) -> None:
        frame = _build_sample_frame()
        summary = describe_nearest_support_resistance(frame, {"params": {"lookback": 120, "swing_window": 3}})
        self.assertTrue(summary is None or isinstance(summary, dict))

    def test_strong_support_resistance_does_not_crash(self) -> None:
        frame = _build_sample_frame()
        summary = describe_strong_support_resistance(
            frame,
            {"params": {"lookback": 160, "swing_window": 3, "min_bounces": 2}},
            interval_label="1 hari",
        )
        self.assertTrue(summary is None or isinstance(summary, dict))

    def test_trendline_summary_does_not_crash_for_basic_frame(self) -> None:
        frame = _build_sample_frame()
        summary = describe_auto_trendlines(frame, {"params": {"lookback": 80, "swing_window": 3, "max_trendlines": 3}})
        self.assertTrue(summary is None or isinstance(summary, dict))


if __name__ == "__main__":
    unittest.main()


