from __future__ import annotations

import unittest
from unittest.mock import patch

from ui.screener.signal_engine import resolve_screening_period_label
from ui.screener.telegram_runner import (
    build_screening_log_chunks,
    build_screening_log_text,
    build_selected_screener_dataframe,
    build_signal_message_text,
    build_startup_message_text,
    load_telegram_settings,
    run_worker_cycle,
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
            "selected_symbols": ["BUMI", "MEDC"],
            "interval_label": "1 hari",
            "ema_period": 10,
            "breakdown_confirm_mode": "body_breakdown",
            "exit_mode": "ema_breakdown",
            "interval_seconds": 300,
        }
        self.sample_note_payload = {
            "summary_text": "Harga sekarang berada di atas EMA 10. Close terakhir 238 sedangkan EMA 10 ada di 223.66.",
            "entry_context_text": "Aturan entry: Buy saat harga pullback ke EMA 10, low menyentuh EMA 10 dan close tetap di atas EMA 10.",
            "exit_context_text": "Trigger exit: waspadai keluar saat harga breakdown di bawah EMA 10.",
            "boxes": [
                {
                    "label": "Posisi harga",
                    "value": "Harga di atas EMA 10",
                    "detail_lines": ["Close 238 | EMA 10 223.66", "Jarak harga 6.02%"],
                },
                {
                    "label": "Status pullback",
                    "value": "Low menyentuh EMA 10",
                    "detail_lines": ["Low 222 | High 238", "Kemiringan EMA 10 naik"],
                },
                {
                    "label": "Kelayakan entry",
                    "value": "Cocok untuk entry pullback EMA 10",
                    "detail_lines": [
                        "Low 222 sudah menyentuh EMA 10 223.66",
                        "Close 238 tetap bertahan di atas EMA 10",
                    ],
                },
                {
                    "label": "Trigger entry",
                    "value": "Bisa entry sekarang",
                    "detail_lines": [
                        "Semua syarat pullback EMA 10 terpenuhi di candle terakhir",
                        "Low sentuh area EMA 10 dan close tetap kuat di atas garis",
                    ],
                },
                {
                    "label": "Trigger exit",
                    "value": "Belum ada trigger exit EMA 10",
                    "detail_lines": [
                        "Close 238 masih bertahan di atas EMA 10",
                        "Waspadai exit kalau nanti ada candle breakdown dan close menutup di bawah EMA 10.",
                    ],
                },
            ],
        }

    def test_build_selected_screener_dataframe_returns_checked_rows_only(self) -> None:
        frame = build_selected_screener_dataframe(self.sample_rows, ["MEDC", "DEWA"])
        self.assertEqual(frame["Kode Saham"].tolist(), ["MEDC", "DEWA"])
        self.assertEqual(
            frame.columns.tolist(),
            ["Kode Saham", "Harga Sekarang", "Price Change", "Jumlah Trade", "Laba Bersih", "Win Rate Backtest EMA"],
        )

    def test_resolve_screening_period_label_follows_interval_not_ui_period(self) -> None:
        self.assertEqual(resolve_screening_period_label("1 hari"), "1y")
        self.assertEqual(resolve_screening_period_label("4 jam"), "6mo")
        self.assertEqual(resolve_screening_period_label("15 menit"), "1mo")

    def test_build_signal_message_text_hides_trigger_exit_for_buy(self) -> None:
        signal_snapshot = {
            "row": {
                "symbol": "BUMI",
                "current_price_text": "238",
                "price_change_text": "8 (+5.61%)",
                "total_trades_text": "12",
                "net_profit_text": "+Rp 1.525.000,00",
                "win_rate_text": "58.25%",
            },
            "note_payload": self.sample_note_payload,
        }
        event = {"action": "BUY", "time_text": "2026-04-02 09:00:00"}

        text = build_signal_message_text(signal_snapshot, event, self.sample_config)

        self.assertIn("SINYAL BUY EMA 10", text)
        self.assertIn("Waktu Event: 2-April-2026 09:00:00", text)
        self.assertIn("*** BUMI | 238 | 8 (+5.61%) ***", text)
        self.assertIn("Backtest:\n- Jumlah Trade: 12\n- Laba Bersih: +Rp 1.525.000,00\n- Win Rate: 58.25%", text)
        self.assertIn("Keterangan:", text)
        self.assertIn("Posisi harga:\n- Harga di atas EMA 10\n- Close 238 | EMA 10 223.66\n- Jarak harga 6.02%", text)
        self.assertIn(
            "Trigger entry:\n- Bisa entry sekarang\n- Semua syarat pullback EMA 10 terpenuhi di candle terakhir\n- Low sentuh area EMA 10 dan close tetap kuat di atas garis",
            text,
        )
        self.assertNotIn("Trigger exit:", text)
        self.assertNotIn("Aturan entry:", text)

    def test_build_signal_message_text_hides_trigger_entry_for_sell(self) -> None:
        signal_snapshot = {
            "row": {
                "symbol": "BUMI",
                "current_price_text": "220",
                "price_change_text": "-5 (-2.22%)",
                "total_trades_text": "12",
                "net_profit_text": "+Rp 1.525.000,00",
                "win_rate_text": "58.25%",
            },
            "note_payload": self.sample_note_payload,
        }
        event = {"action": "SELL", "time_text": "2026-04-02 09:00:00"}

        text = build_signal_message_text(signal_snapshot, event, self.sample_config)

        self.assertIn("SINYAL SELL EMA 10", text)
        self.assertIn("Waktu Event: 2-April-2026 09:00:00", text)
        self.assertIn("*** BUMI | 220 | -5 (-2.22%) ***", text)
        self.assertIn("Backtest:\n- Jumlah Trade: 12\n- Laba Bersih: +Rp 1.525.000,00\n- Win Rate: 58.25%", text)
        self.assertIn(
            "Trigger exit:\n- Belum ada trigger exit EMA 10\n- Close 238 masih bertahan di atas EMA 10\n- Waspadai exit kalau nanti ada candle breakdown dan close menutup di bawah EMA 10.",
            text,
        )
        self.assertNotIn("Trigger entry:", text)

    def test_build_startup_message_text_mentions_symbols_and_interval(self) -> None:
        text = build_startup_message_text(self.sample_config)
        self.assertIn("Screener EMA 10 Aktif", text)
        self.assertRegex(text, r"Waktu: \d{1,2}-[A-Za-z]+-\d{4} \d{2}:\d{2}:\d{2}")
        self.assertIn("Screening: tiap 5 menit", text)
        self.assertIn("Status awal: worker siap kirim alert BUY/SELL baru sesuai flow backtest BREAK_EMA.", text)
        self.assertIn("Saham dipantau (2): *** BUMI ***, *** MEDC ***", text)

    def test_build_screening_log_text_formats_detailed_stock_blocks(self) -> None:
        snapshots = [
            {
                "symbol": "BUMI",
                "row": {
                    "symbol": "BUMI",
                    "current_price_text": "214",
                    "price_change_text": "34 (+18.89%)",
                },
                "note_payload": self.sample_note_payload,
                "error": "",
            },
            {
                "symbol": "VKTR",
                "row": {
                    "symbol": "VKTR",
                    "current_price_text": "815",
                    "price_change_text": "120 (+17.27%)",
                },
                "note_payload": self.sample_note_payload,
                "error": "",
            },
        ]
        text = build_screening_log_text(self.sample_config, snapshots, is_startup_cycle=False, cycle_count=5)
        chunks = build_screening_log_chunks(self.sample_config, snapshots, is_startup_cycle=False, cycle_count=5)

        self.assertIn("Waktu Cycle:", text)
        self.assertRegex(text, r"Waktu Cycle: \d{1,2}-[A-Za-z]+-\d{4} \d{2}:\d{2}:\d{2}")
        self.assertIn("Status Cycle: 5 X", text)
        self.assertIn("Interval chart: 1 hari", text)
        self.assertIn("EMA: 10 | Entry: Body candle bearish breakdown | Exit: Breakdown di bawah EMA saja", text)
        self.assertEqual(len(chunks), 1)
        self.assertIn("*** BUMI | 214 | 34 (+18.89%) ***", chunks[0])
        self.assertIn("Posisi harga:\n- Harga di atas EMA 10\n- Close 238 | EMA 10 223.66\n- Jarak harga 6.02%", chunks[0])
        self.assertIn("Status pullback:\n- Low menyentuh EMA 10\n- Low 222 | High 238\n- Kemiringan EMA 10 naik", chunks[0])
        self.assertIn(
            "Trigger exit:\n- Belum ada trigger exit EMA 10\n- Close 238 masih bertahan di atas EMA 10\n- Waspadai exit kalau nanti ada candle breakdown dan close menutup di bawah EMA 10.",
            chunks[0],
        )
        self.assertIn("*** VKTR | 815 | 120 (+17.27%) ***", chunks[0])
        self.assertIn("----------", chunks[0])

    def test_load_telegram_settings_prioritizes_streamlit_then_env_then_dotenv(self) -> None:
        with (
            patch("ui.screener.telegram_runner.load_env_values", return_value={"TELEGRAM_BOT_TOKEN": "dotenv-token"}),
            patch(
                "ui.screener.telegram_runner.load_os_env_values",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "env-token",
                    "TELEGRAM_GROUP_ID": "env-group",
                    "TELEGRAM_GROUP_LOG_ID": "env-log-group",
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_streamlit_secrets_values",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "streamlit-token",
                    "TELEGRAM_GROUP_ID": "streamlit-group",
                    "TELEGRAM_GROUP_LOG_ID": "streamlit-log-group",
                },
            ),
        ):
            settings = load_telegram_settings()

        self.assertEqual(settings["TELEGRAM_BOT_TOKEN"], "streamlit-token")
        self.assertEqual(settings["TELEGRAM_GROUP_ID"], "streamlit-group")
        self.assertEqual(settings["TELEGRAM_GROUP_LOG_ID"], "streamlit-log-group")

    def test_run_worker_cycle_sends_startup_alert_signal_and_log_once(self) -> None:
        sample_snapshot = {
            "symbol": "BUMI",
            "row": {
                "symbol": "BUMI",
                "current_price_text": "238",
                "price_change_text": "8 (+5.61%)",
                "total_trades_text": "12",
                "net_profit_text": "+Rp 1.525.000,00",
                "win_rate_text": "58.25%",
            },
            "note_payload": self.sample_note_payload,
            "fresh_events": [
                {
                    "event_id": "BUMI|BUY|2026-04-02 09:00:00|0",
                    "symbol": "BUMI",
                    "action": "BUY",
                    "time_text": "2026-04-02 09:00:00",
                    "reason": "entry",
                }
            ],
            "error": "",
        }
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "token",
                    "TELEGRAM_GROUP_ID": "alert-group",
                    "TELEGRAM_GROUP_LOG_ID": "log-group",
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_runtime_state",
                return_value={"startup_main_sent": False, "sent_event_ids": [], "cycle_count": 0},
            ),
            patch("ui.screener.telegram_runner.save_runtime_state") as save_runtime_state,
            patch("ui.screener.telegram_runner.build_break_ema_signal_snapshots", return_value=[sample_snapshot]),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
        ):
            summary = run_worker_cycle(self.sample_config)

        self.assertEqual(summary["signals_sent"], 1)
        self.assertEqual(len(send_calls), 3)
        self.assertEqual(send_calls[0][0], "alert-group")
        self.assertIn("Screener EMA 10 Aktif", send_calls[0][1])
        self.assertEqual(send_calls[1][0], "alert-group")
        self.assertIn("SINYAL BUY EMA", send_calls[1][1])
        self.assertEqual(send_calls[2][0], "log-group")
        self.assertIn("Status Cycle: Startup", send_calls[2][1])
        self.assertIn("*** BUMI | 238 | 8 (+5.61%) ***", send_calls[2][1])
        save_payload = save_runtime_state.call_args.args[0]
        self.assertTrue(save_payload["startup_main_sent"])
        self.assertEqual(save_payload["cycle_count"], 0)
        self.assertIn("BUMI|BUY|2026-04-02 09:00:00|0", save_payload["sent_event_ids"])

    def test_run_worker_cycle_deduplicates_existing_signal_ids(self) -> None:
        sample_snapshot = {
            "symbol": "BUMI",
            "row": {
                "symbol": "BUMI",
                "current_price_text": "238",
                "price_change_text": "8 (+5.61%)",
                "total_trades_text": "12",
                "net_profit_text": "+Rp 1.525.000,00",
                "win_rate_text": "58.25%",
            },
            "note_payload": self.sample_note_payload,
            "fresh_events": [
                {
                    "event_id": "BUMI|BUY|2026-04-02 09:00:00|0",
                    "symbol": "BUMI",
                    "action": "BUY",
                    "time_text": "2026-04-02 09:00:00",
                    "reason": "entry",
                }
            ],
            "error": "",
        }
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "token",
                    "TELEGRAM_GROUP_ID": "alert-group",
                    "TELEGRAM_GROUP_LOG_ID": "log-group",
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_runtime_state",
                return_value={
                    "startup_main_sent": True,
                    "sent_event_ids": ["BUMI|BUY|2026-04-02 09:00:00|0"],
                    "cycle_count": 4,
                },
            ),
            patch("ui.screener.telegram_runner.save_runtime_state") as save_runtime_state,
            patch("ui.screener.telegram_runner.build_break_ema_signal_snapshots", return_value=[sample_snapshot]),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
        ):
            summary = run_worker_cycle(self.sample_config)

        self.assertEqual(summary["signals_sent"], 0)
        self.assertEqual(summary["cycle_count"], 5)
        self.assertEqual(len(send_calls), 1)
        self.assertEqual(send_calls[0][0], "log-group")
        self.assertIn("Status Cycle: 5 X", send_calls[0][1])
        self.assertIn("*** BUMI | 238 | 8 (+5.61%) ***", send_calls[0][1])
        save_payload = save_runtime_state.call_args.args[0]
        self.assertEqual(save_payload["cycle_count"], 5)


if __name__ == "__main__":
    unittest.main()
