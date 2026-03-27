from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from data.loader import load_market_data
from data.models import MarketInsight, PeriodRequest


class LoaderSessionSummaryTests(unittest.TestCase):
    def _daily_frame(self, rows: list[dict[str, float]]) -> pd.DataFrame:
        index = pd.date_range('2026-03-25', periods=len(rows), freq='D')
        return pd.DataFrame(rows, index=index)

    def _intraday_frame(self, rows: list[dict[str, object]]) -> pd.DataFrame:
        index = pd.to_datetime([row['time'] for row in rows])
        frame = pd.DataFrame(
            [
                {
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                }
                for row in rows
            ],
            index=index,
        )
        return frame

    def test_loader_uses_shared_market_card_snapshot_for_daily_interval(self) -> None:
        chart_history = self._daily_frame(
            [
                {'open': 460.0, 'high': 474.0, 'low': 438.0, 'close': 460.0, 'volume': 7_800_000.0},
                {'open': 460.0, 'high': 474.0, 'low': 438.0, 'close': 440.0, 'volume': 7_800_000.0},
            ]
        )
        market_card_history = self._intraday_frame(
            [
                {'time': '2026-03-27 15:00:00', 'open': 440.0, 'high': 440.0, 'low': 440.0, 'close': 440.0, 'volume': 100_000.0},
                {'time': '2026-03-28 09:15:00', 'open': 450.0, 'high': 455.0, 'low': 445.0, 'close': 452.0, 'volume': 120_000.0},
                {'time': '2026-03-28 10:00:00', 'open': 452.0, 'high': 468.0, 'low': 440.0, 'close': 448.0, 'volume': 300_000.0},
            ]
        )
        chart_frame = pd.DataFrame(
            {
                'time': ['2026-03-27', '2026-03-28'],
                'open': [460.0, 460.0],
                'high': [474.0, 474.0],
                'low': [438.0, 438.0],
                'close': [460.0, 440.0],
                'volume': [7_800_000.0, 7_800_000.0],
            }
        )

        with patch('data.loader.sanitize_symbol', return_value='DEWA'), \
            patch('data.loader.candidate_provider_symbols', return_value=['DEWA.JK']), \
            patch('data.loader.display_symbol', side_effect=lambda value: 'DEWA' if value else ''), \
            patch('data.loader.resolve_company_name', return_value='PT Darma Henwa Tbk'), \
            patch('data.loader.translate_period_selection', return_value=PeriodRequest('YTD', native_period='ytd')), \
            patch('data.loader.apply_intraday_guard', return_value=(PeriodRequest('YTD', native_period='ytd'), [])), \
            patch('data.loader.download_history_with_fallback', return_value=(chart_history, 'DEWA.JK')) as mocked_download, \
            patch('data.loader.download_live_history_with_fallback', return_value=(market_card_history, 'DEWA.JK')) as mocked_live_download, \
            patch('data.loader.normalize_history_dataframe', side_effect=lambda frame: frame.copy()), \
            patch('data.loader.finalize_chart_dataframe', return_value=chart_frame), \
            patch('data.loader.build_market_insight', return_value=MarketInsight('Sideways', 'Low Risk', 'stub')):
            result = load_market_data('DEWA', '1 hari', 'YTD')

        self.assertEqual(mocked_download.call_count, 1)
        self.assertEqual(mocked_live_download.call_count, 1)
        self.assertEqual(result.current_price, 448.0)
        self.assertEqual(result.previous_close, 440.0)
        self.assertEqual(result.session_summary.previous_close, 440.0)
        self.assertEqual(result.session_summary.open_price, 450.0)
        self.assertEqual(result.session_summary.ara_price, 560.0)
        self.assertEqual(result.session_summary.arb_price, 382.0)
        self.assertEqual(result.session_summary.high_price, 468.0)
        self.assertEqual(result.session_summary.low_price, 440.0)
        self.assertEqual(result.session_summary.lot, 4_200.0)
        self.assertAlmostEqual(result.session_summary.value or 0.0, 189_660_000.0)
        self.assertEqual(result.session_summary.ara_price, 560.0)
        self.assertEqual(result.session_summary.arb_price, 382.0)
        self.assertAlmostEqual(result.session_summary.average_price or 0.0, 451.5714285714, places=4)
        self.assertEqual(result.session_summary.ara_price, 560.0)
        self.assertEqual(result.session_summary.arb_price, 382.0)

    def test_loader_uses_shared_market_card_snapshot_for_intraday_interval(self) -> None:
        intraday_history = self._intraday_frame(
            [
                {'time': '2026-03-27 15:00:00', 'open': 440.0, 'high': 440.0, 'low': 440.0, 'close': 440.0, 'volume': 100_000.0},
                {'time': '2026-03-28 09:15:00', 'open': 450.0, 'high': 455.0, 'low': 445.0, 'close': 452.0, 'volume': 120_000.0},
                {'time': '2026-03-28 10:00:00', 'open': 452.0, 'high': 468.0, 'low': 440.0, 'close': 448.0, 'volume': 300_000.0},
            ]
        )
        chart_frame = pd.DataFrame(
            {
                'time': ['2026-03-27 15:00:00', '2026-03-28 09:15:00', '2026-03-28 10:00:00'],
                'open': [440.0, 450.0, 452.0],
                'high': [440.0, 455.0, 468.0],
                'low': [440.0, 445.0, 440.0],
                'close': [440.0, 452.0, 448.0],
                'volume': [100_000.0, 120_000.0, 300_000.0],
            }
        )

        with patch('data.loader.sanitize_symbol', return_value='DEWA'), \
            patch('data.loader.candidate_provider_symbols', return_value=['DEWA.JK']), \
            patch('data.loader.display_symbol', side_effect=lambda value: 'DEWA' if value else ''), \
            patch('data.loader.resolve_company_name', return_value='PT Darma Henwa Tbk'), \
            patch('data.loader.translate_period_selection', return_value=PeriodRequest('YTD', native_period='ytd')), \
            patch('data.loader.apply_intraday_guard', return_value=(PeriodRequest('YTD', native_period='ytd'), [])), \
            patch('data.loader.download_history_with_fallback', return_value=(intraday_history, 'DEWA.JK')) as mocked_download, \
            patch('data.loader.download_live_history_with_fallback', return_value=(intraday_history, 'DEWA.JK')) as mocked_live_download, \
            patch('data.loader.normalize_history_dataframe', side_effect=lambda frame: frame.copy()), \
            patch('data.loader.finalize_chart_dataframe', return_value=chart_frame), \
            patch('data.loader.build_market_insight', return_value=MarketInsight('Sideways', 'Low Risk', 'stub')):
            result = load_market_data('DEWA', '15 menit', 'YTD')

        self.assertEqual(mocked_download.call_count, 1)
        self.assertEqual(mocked_live_download.call_count, 1)
        self.assertEqual(result.current_price, 448.0)
        self.assertEqual(result.previous_close, 440.0)
        self.assertEqual(result.session_summary.previous_close, 440.0)
        self.assertEqual(result.session_summary.open_price, 450.0)
        self.assertEqual(result.session_summary.ara_price, 560.0)
        self.assertEqual(result.session_summary.arb_price, 382.0)
        self.assertEqual(result.session_summary.high_price, 468.0)
        self.assertEqual(result.session_summary.low_price, 440.0)
        self.assertEqual(result.session_summary.lot, 4_200.0)
        self.assertAlmostEqual(result.session_summary.value or 0.0, 189_660_000.0)
        self.assertEqual(result.session_summary.ara_price, 560.0)
        self.assertEqual(result.session_summary.arb_price, 382.0)

    def test_loader_falls_back_to_selected_history_when_live_snapshot_unavailable(self) -> None:
        chart_history = self._intraday_frame(
            [
                {'time': '2026-03-27 15:00:00', 'open': 440.0, 'high': 440.0, 'low': 440.0, 'close': 440.0, 'volume': 100_000.0},
                {'time': '2026-03-28 09:15:00', 'open': 450.0, 'high': 455.0, 'low': 445.0, 'close': 452.0, 'volume': 120_000.0},
                {'time': '2026-03-28 10:00:00', 'open': 452.0, 'high': 468.0, 'low': 440.0, 'close': 448.0, 'volume': 300_000.0},
            ]
        )
        chart_frame = pd.DataFrame(
            {
                'time': ['2026-03-27 15:00:00', '2026-03-28 09:15:00', '2026-03-28 10:00:00'],
                'open': [440.0, 450.0, 452.0],
                'high': [440.0, 455.0, 468.0],
                'low': [440.0, 445.0, 440.0],
                'close': [440.0, 452.0, 448.0],
                'volume': [100_000.0, 120_000.0, 300_000.0],
            }
        )

        with patch('data.loader.sanitize_symbol', return_value='DEWA'), \
            patch('data.loader.candidate_provider_symbols', return_value=['DEWA.JK']), \
            patch('data.loader.display_symbol', side_effect=lambda value: 'DEWA' if value else ''), \
            patch('data.loader.resolve_company_name', return_value='PT Darma Henwa Tbk'), \
            patch('data.loader.translate_period_selection', return_value=PeriodRequest('YTD', native_period='ytd')), \
            patch('data.loader.apply_intraday_guard', return_value=(PeriodRequest('YTD', native_period='ytd'), [])), \
            patch('data.loader.download_history_with_fallback', return_value=(chart_history, 'DEWA.JK')) as mocked_download, \
            patch('data.loader.download_live_history_with_fallback', side_effect=Exception('live failed')) as mocked_live_download, \
            patch('data.loader.normalize_history_dataframe', side_effect=lambda frame: frame.copy()), \
            patch('data.loader.finalize_chart_dataframe', return_value=chart_frame), \
            patch('data.loader.build_market_insight', return_value=MarketInsight('Sideways', 'Low Risk', 'stub')):
            result = load_market_data('DEWA', '15 menit', 'YTD')

        self.assertEqual(mocked_download.call_count, 1)
        self.assertEqual(mocked_live_download.call_count, 3)
        self.assertEqual(result.current_price, 448.0)
        self.assertEqual(result.previous_close, 440.0)
        self.assertEqual(result.session_summary.previous_close, 440.0)
        self.assertEqual(result.session_summary.open_price, 450.0)
        self.assertEqual(result.session_summary.ara_price, 560.0)
        self.assertEqual(result.session_summary.arb_price, 382.0)


if __name__ == '__main__':
    unittest.main()





