from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from data.history_parts.download import (
    download_history_with_fallback,
    download_live_history_with_fallback,
)


class HistoryDownloadFallbackTests(unittest.TestCase):
    def test_download_history_fallback_prefers_later_candidate_with_more_rows(self) -> None:
        short_frame = pd.DataFrame({"Close": [12.33]}, index=pd.to_datetime(["2025-06-11"]))
        full_frame = pd.DataFrame(
            {"Close": [1500.0, 1510.0, 1520.0, 1530.0]},
            index=pd.date_range("2026-03-24", periods=4, freq="D"),
        )

        with patch(
            "data.history_parts.download._download_history_cached",
            side_effect=[short_frame, full_frame],
        ):
            frame, symbol = download_history_with_fallback(
                ["ENRG", "ENRG.JK"],
                interval="1d",
                native_period="1y",
                start_iso=None,
                end_iso=None,
            )

        self.assertEqual(symbol, "ENRG.JK")
        self.assertEqual(len(frame), 4)

    def test_download_history_fallback_keeps_first_candidate_when_it_is_usable(self) -> None:
        first_frame = pd.DataFrame(
            {"Close": [12.1, 12.2, 12.3]},
            index=pd.date_range("2026-03-24", periods=3, freq="D"),
        )

        with patch(
            "data.history_parts.download._download_history_cached",
            return_value=first_frame,
        ) as mocked_download:
            frame, symbol = download_history_with_fallback(
                ["AAPL", "AAPL.JK"],
                interval="1d",
                native_period="1mo",
                start_iso=None,
                end_iso=None,
            )

        self.assertEqual(symbol, "AAPL")
        self.assertEqual(len(frame), 3)
        self.assertEqual(mocked_download.call_count, 1)

    def test_download_live_history_fallback_uses_same_candidate_quality_rule(self) -> None:
        short_frame = pd.DataFrame({"Close": [25.0]}, index=pd.to_datetime(["2025-01-06"]))
        full_frame = pd.DataFrame(
            {"Close": [1600.0, 1610.0, 1620.0]},
            index=pd.date_range("2026-03-26", periods=3, freq="D"),
        )

        with patch(
            "data.history_parts.download._download_live_history_cached",
            side_effect=[short_frame, full_frame],
        ):
            frame, symbol = download_live_history_with_fallback(
                ["ENRG", "ENRG.JK"],
                interval="1d",
                native_period="5d",
                start_iso=None,
                end_iso=None,
            )

        self.assertEqual(symbol, "ENRG.JK")
        self.assertEqual(len(frame), 3)


if __name__ == "__main__":
    unittest.main()
