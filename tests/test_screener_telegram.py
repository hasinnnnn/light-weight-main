from __future__ import annotations

import unittest
from unittest.mock import patch

from ui.screener.telegram_runner import (
    build_selected_screener_dataframe,
    build_telegram_message_chunks,
    load_telegram_settings,
)


class ScreenerTelegramTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_rows = [
            {
                "no": 1,
                "company_name": "Bumi Resources Tbk.",
                "symbol": "BUMI",
                "current_price_text": "132",
                "price_change_pct": 5.61,
                "price_change_text": "8 (+5.61%)",
                "total_trades_text": "12",
                "net_profit_text": "+Rp 1.525.000,00",
                "win_rate_text": "58.25%",
            },
            {
                "no": 2,
                "company_name": "PT Medco Energi Internasional Tbk.",
                "symbol": "MEDC",
                "current_price_text": "1,930",
                "price_change_pct": 1.35,
                "price_change_text": "26 (+1.35%)",
                "total_trades_text": "9",
                "net_profit_text": "+Rp 275.000,00",
                "win_rate_text": "58.25%",
            },
            {
                "no": 3,
                "company_name": "PT Darma Henwa Tbk.",
                "symbol": "DEWA",
                "current_price_text": "456",
                "price_change_pct": -2.10,
                "price_change_text": "10 (-2.10%)",
                "total_trades_text": "7",
                "net_profit_text": "-Rp 315.000,00",
                "win_rate_text": "41.10%",
            },
        ]
        self.sample_config = {
            "interval_label": "1 hari",
            "period_label": "YTD",
            "ema_period": 10,
            "breakdown_confirm_mode": "body_breakdown",
            "exit_mode": "ema_breakdown",
        }

    def test_build_selected_screener_dataframe_returns_checked_rows_only(self) -> None:
        frame = build_selected_screener_dataframe(self.sample_rows, ["MEDC", "DEWA"])
        self.assertEqual(frame["Kode Saham"].tolist(), ["MEDC", "DEWA"])
        self.assertEqual(
            frame.columns.tolist(),
            ["Kode Saham", "Harga Sekarang", "Price Change", "Jumlah Trade", "Laba Bersih", "Win Rate Backtest EMA"],
        )

    def test_build_telegram_message_chunks_contains_all_visible_columns(self) -> None:
        chunks = build_telegram_message_chunks(self.sample_rows, ["BUMI"], self.sample_config)
        self.assertEqual(len(chunks), 1)
        text = chunks[0]
        self.assertIn("Screener EMA", text)
        self.assertIn("Kode Saham: BUMI", text)
        self.assertIn("Harga Sekarang: 132", text)
        self.assertIn("Price Change: 8 (+5.61%)", text)
        self.assertIn("Jumlah Trade: 12", text)
        self.assertIn("Laba Bersih: +Rp 1.525.000,00", text)
        self.assertIn("Win Rate Backtest EMA: 58.25%", text)
        self.assertNotIn("MEDC", text)

    def test_build_telegram_message_chunks_handles_empty_selection(self) -> None:
        chunks = build_telegram_message_chunks(self.sample_rows, [], self.sample_config)
        self.assertEqual(len(chunks), 1)
        self.assertIn("Belum ada saham yang diceklis.", chunks[0])

    def test_load_telegram_settings_prioritizes_streamlit_then_env_then_dotenv(self) -> None:
        with (
            patch("ui.screener.telegram_runner.load_env_values", return_value={"TELEGRAM_BOT_TOKEN": "dotenv-token"}),
            patch(
                "ui.screener.telegram_runner.load_os_env_values",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "env-token",
                    "TELEGRAM_GROUP_ID": "env-group",
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_streamlit_secrets_values",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "streamlit-token",
                    "TELEGRAM_GROUP_ID": "streamlit-group",
                },
            ),
        ):
            settings = load_telegram_settings()

        self.assertEqual(settings["TELEGRAM_BOT_TOKEN"], "streamlit-token")
        self.assertEqual(settings["TELEGRAM_GROUP_ID"], "streamlit-group")


if __name__ == "__main__":
    unittest.main()
