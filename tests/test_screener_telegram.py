from __future__ import annotations

import sys
import unittest
from io import BytesIO
from datetime import datetime
from unittest.mock import patch

import pandas as pd
from PIL import Image

import telegram_bot.support_resistance as support_resistance_module
from serve_streamlit import build_streamlit_command
from telegram_bot.support_resistance import (
    build_support_resistance_chart_image_bytes,
    build_support_resistance_message_text,
)
from ui.screener.signal_engine import resolve_screening_period_label
from ui.screener.telegram_runner import (
    TELEGRAM_BOT_COMMANDS,
    build_command_help_text,
    build_screening_log_chunks,
    build_screening_log_text,
    build_shutdown_message_text,
    build_selected_screener_dataframe,
    build_signal_message_text,
    build_startup_message_text,
    ensure_telegram_command_worker,
    load_telegram_settings,
    process_pending_telegram_commands,
    run_worker_cycle,
    stop_telegram_worker,
    sync_telegram_bot_commands,
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

    def test_build_signal_message_text_uses_current_clock_for_date_only_event(self) -> None:
        signal_snapshot = {
            "row": {
                "symbol": "RLCO",
                "current_price_text": "5,800",
                "price_change_text": "800 (-12.12%)",
                "total_trades_text": "6",
                "net_profit_text": "+Rp 80.000,00",
                "win_rate_text": "50.00%",
            },
            "note_payload": self.sample_note_payload,
        }
        event = {"action": "SELL", "time_text": "2026-04-02"}

        with patch(
            "ui.screener.telegram_runner._current_local_datetime",
            return_value=datetime(2026, 4, 2, 15, 36, 12),
        ):
            text = build_signal_message_text(signal_snapshot, event, self.sample_config)

        self.assertIn("Waktu Event: 2-April-2026 15:36:12", text)

    def test_build_startup_message_text_mentions_symbols_and_interval(self) -> None:
        text = build_startup_message_text(self.sample_config)
        self.assertIn("Screener EMA 10 Aktif", text)
        self.assertRegex(text, r"Waktu: \d{1,2}-[A-Za-z]+-\d{4} \d{2}:\d{2}:\d{2}")
        self.assertIn("Screening: tiap 5 menit", text)
        self.assertIn("Status awal: worker siap kirim alert BUY/SELL baru sesuai flow backtest BREAK_EMA.", text)
        self.assertIn("Saham dipantau (2): *** BUMI ***, *** MEDC ***", text)

    def test_build_shutdown_message_text_mentions_nonaktif_state(self) -> None:
        text = build_shutdown_message_text(self.sample_config, reason_text="Worker dihentikan, screening nonaktif.")
        self.assertIn("Screener EMA 10 Nonaktif", text)
        self.assertRegex(text, r"Waktu: \d{1,2}-[A-Za-z]+-\d{4} \d{2}:\d{2}:\d{2}")
        self.assertIn("Status akhir: Worker dihentikan, screening nonaktif.", text)
        self.assertIn("Saham dipantau (2): *** BUMI ***, *** MEDC ***", text)

    def test_build_command_help_text_lists_registered_commands(self) -> None:
        text = build_command_help_text()

        self.assertIn("Bot Screener & Analisis", text)
        for command in TELEGRAM_BOT_COMMANDS:
            self.assertIn(f"/{command['command']} - {command['description']}", text)
        self.assertIn("/srd BUMI", text)
        self.assertIn("/srk BUMI", text)
        self.assertIn("TELEGRAM_USER_ID", text)

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

    def test_sync_telegram_bot_commands_calls_set_my_commands(self) -> None:
        with patch("ui.screener.telegram_runner._call_telegram_api") as call_telegram_api:
            sync_telegram_bot_commands("token")

        call_telegram_api.assert_called_once_with(
            "token",
            "setMyCommands",
            {"commands": list(TELEGRAM_BOT_COMMANDS)},
        )

    def test_ensure_telegram_command_worker_starts_background_listener(self) -> None:
        expected_state = {
            "pid": 4321,
            "interval_seconds": 5,
            "started_at": "2026-04-02T22:00:00",
        }

        with (
            patch(
                "ui.screener.telegram_runner.command_worker_state",
                side_effect=[None, None],
            ),
            patch("ui.screener.telegram_runner.acquire_command_start_lock", return_value=True),
            patch("ui.screener.telegram_runner.release_command_start_lock"),
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={"TELEGRAM_BOT_TOKEN": "token"},
            ),
            patch(
                "telegram_bot.command_worker.start_background_command_worker",
                return_value=expected_state,
            ) as start_background_command_worker,
        ):
            state = ensure_telegram_command_worker()

        self.assertEqual(state, expected_state)
        start_background_command_worker.assert_called_once_with()

    def test_build_streamlit_command_uses_platform_port(self) -> None:
        with patch.dict("os.environ", {"PORT": "9999"}, clear=False):
            command = build_streamlit_command("--server.headless=true")

        self.assertEqual(command[:6], [sys.executable, "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0"])
        self.assertIn("--server.port=9999", command)
        self.assertIn("--server.headless=true", command)

    def test_process_pending_telegram_commands_handles_help_status_and_stop(self) -> None:
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "token",
                    "TELEGRAM_USER_ID": "999",
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_runtime_state",
                return_value={
                    "startup_main_sent": True,
                    "sent_event_ids": [],
                    "cycle_count": 4,
                    "last_cycle_at": "2026-04-02T15:36:12",
                },
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 101,
                        "message": {
                            "text": "/help",
                            "chat": {"id": "777"},
                            "from": {"id": "123"},
                        },
                    },
                    {
                        "update_id": 102,
                        "message": {
                            "text": "/status",
                            "chat": {"id": "888"},
                            "from": {"id": "999"},
                        },
                    },
                    {
                        "update_id": 103,
                        "message": {
                            "text": "/stop",
                            "chat": {"id": "888"},
                            "from": {"id": "999"},
                        },
                    },
                ],
            ),
            patch("ui.screener.telegram_runner.worker_state", return_value=dict(self.sample_config)),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
            patch("ui.screener.telegram_runner.stop_telegram_worker", return_value=True) as stop_telegram_worker,
        ):
            summary = process_pending_telegram_commands(last_command_update_id=101)

        self.assertEqual(summary["processed_count"], 3)
        self.assertEqual(summary["last_command_update_id"], 104)
        self.assertEqual(len(send_calls), 3)
        self.assertEqual(send_calls[0][0], "777")
        self.assertIn("Command tersedia:", send_calls[0][1])
        self.assertIn("/help - Lihat daftar command bot", send_calls[0][1])
        self.assertEqual(send_calls[1][0], "888")
        self.assertIn("Cycle terakhir: 2-April-2026 15:36:12", send_calls[1][1])
        self.assertIn("Status cycle: 4 X", send_calls[1][1])
        self.assertEqual(send_calls[2][0], "888")
        self.assertIn("Perintah `/stop` diterima", send_calls[2][1])
        stop_telegram_worker.assert_called_once()

    def test_process_pending_telegram_commands_requires_admin_for_stop(self) -> None:
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "token",
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_runtime_state",
                return_value={
                    "startup_main_sent": True,
                    "sent_event_ids": [],
                    "cycle_count": 1,
                    "last_cycle_at": "2026-04-02T15:36:12",
                },
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 201,
                        "message": {
                            "text": "/stop",
                            "chat": {"id": "999"},
                            "from": {"id": "999"},
                        },
                    }
                ],
            ),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
            patch("ui.screener.telegram_runner.stop_telegram_worker") as stop_telegram_worker,
        ):
            summary = process_pending_telegram_commands(last_command_update_id=201)

        self.assertEqual(summary["last_command_update_id"], 202)
        self.assertEqual(len(send_calls), 1)
        self.assertEqual(send_calls[0][0], "999")
        self.assertIn("Isi `TELEGRAM_USER_ID` dulu", send_calls[0][1])
        stop_telegram_worker.assert_not_called()

    def test_process_pending_telegram_commands_reports_inactive_worker_status(self) -> None:
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "token",
                    "TELEGRAM_USER_ID": "999",
                },
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 301,
                        "message": {
                            "text": "/status",
                            "chat": {"id": "999"},
                            "from": {"id": "999"},
                        },
                    }
                ],
            ),
            patch("ui.screener.telegram_runner.worker_state", return_value=None),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
        ):
            summary = process_pending_telegram_commands(last_command_update_id=301)

        self.assertEqual(summary["processed_count"], 1)
        self.assertEqual(summary["last_command_update_id"], 302)
        self.assertEqual(len(send_calls), 1)
        self.assertEqual(send_calls[0][0], "999")
        self.assertIn("Screener belum aktif.", send_calls[0][1])

    def test_process_pending_telegram_commands_routes_srd_and_srk(self) -> None:
        send_calls: list[tuple[str, str]] = []
        photo_calls: list[str] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        def _capture_photo(bot_token: str, group_id: str, photo_bytes: bytes, **kwargs: object) -> None:
            photo_calls.append(group_id)

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={"TELEGRAM_BOT_TOKEN": "token"},
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 401,
                        "message": {
                            "text": "/srd bumi",
                            "chat": {"id": "777"},
                            "from": {"id": "123"},
                        },
                    },
                    {
                        "update_id": 402,
                        "message": {
                            "text": "/srk bumi",
                            "chat": {"id": "777"},
                            "from": {"id": "123"},
                        },
                    },
                ],
            ),
            patch(
                "telegram_bot.router.build_support_resistance_message_text",
                side_effect=["SR terdekat BUMI", "SR kuat BUMI"],
            ) as build_sr_message_text,
            patch(
                "telegram_bot.router.build_support_resistance_chart_image_bytes",
                return_value=None,
            ),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
            patch("ui.screener.telegram_runner.send_telegram_photo", side_effect=_capture_photo),
        ):
            summary = process_pending_telegram_commands(last_command_update_id=401)

        self.assertEqual(summary["processed_count"], 2)
        self.assertEqual(summary["last_command_update_id"], 403)
        self.assertEqual(len(send_calls), 2)
        self.assertEqual(photo_calls, [])
        self.assertEqual(send_calls[0], ("777", "SR terdekat BUMI"))
        self.assertEqual(send_calls[1], ("777", "SR kuat BUMI"))
        self.assertEqual(build_sr_message_text.call_count, 2)
        self.assertEqual(build_sr_message_text.call_args_list[0].args[0], "BUMI")
        self.assertFalse(bool(build_sr_message_text.call_args_list[0].kwargs["strong"]))
        self.assertEqual(build_sr_message_text.call_args_list[1].args[0], "BUMI")
        self.assertTrue(bool(build_sr_message_text.call_args_list[1].kwargs["strong"]))

    def test_process_pending_telegram_commands_treats_command_name_case_insensitively(self) -> None:
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={"TELEGRAM_BOT_TOKEN": "token"},
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 451,
                        "message": {
                            "text": "/SrK bumi",
                            "chat": {"id": "777"},
                            "from": {"id": "123"},
                        },
                    },
                ],
            ),
            patch(
                "telegram_bot.router.build_support_resistance_message_text",
                return_value="SR kuat BUMI",
            ) as build_sr_message_text,
            patch(
                "telegram_bot.router.build_support_resistance_chart_image_bytes",
                return_value=None,
            ),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
        ):
            summary = process_pending_telegram_commands(last_command_update_id=451)

        self.assertEqual(summary["processed_count"], 1)
        self.assertEqual(summary["last_command_update_id"], 452)
        self.assertEqual(send_calls, [("777", "SR kuat BUMI")])
        self.assertEqual(build_sr_message_text.call_args.args[0], "BUMI")
        self.assertTrue(bool(build_sr_message_text.call_args.kwargs["strong"]))

    def test_process_pending_telegram_commands_sends_chart_photo_when_available(self) -> None:
        send_calls: list[tuple[str, str]] = []
        photo_calls: list[tuple[str, int, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        def _capture_photo(bot_token: str, group_id: str, photo_bytes: bytes, **kwargs: object) -> None:
            photo_calls.append((group_id, len(photo_bytes), str(kwargs.get("caption", ""))))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={"TELEGRAM_BOT_TOKEN": "token"},
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 501,
                        "message": {
                            "text": "/srd bumi",
                            "chat": {"id": "777"},
                            "from": {"id": "123"},
                        },
                    },
                ],
            ),
            patch(
                "telegram_bot.router.build_support_resistance_chart_image_bytes",
                return_value=b"png-bytes",
            ),
            patch(
                "telegram_bot.router.build_support_resistance_message_text",
                return_value="SR terdekat BUMI",
            ),
            patch("ui.screener.telegram_runner.send_telegram_photo", side_effect=_capture_photo),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
        ):
            summary = process_pending_telegram_commands(last_command_update_id=501)

        self.assertEqual(summary["processed_count"], 1)
        self.assertEqual(summary["last_command_update_id"], 502)
        self.assertEqual(photo_calls, [("777", 9, "SR terdekat BUMI")])
        self.assertEqual(send_calls, [])

    def test_process_pending_telegram_commands_falls_back_to_text_when_send_photo_fails(self) -> None:
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={"TELEGRAM_BOT_TOKEN": "token"},
            ),
            patch(
                "ui.screener.telegram_runner.fetch_telegram_updates",
                return_value=[
                    {
                        "update_id": 551,
                        "message": {
                            "text": "/srd bumi",
                            "chat": {"id": "777"},
                            "from": {"id": "123"},
                        },
                    },
                ],
            ),
            patch(
                "telegram_bot.router.build_support_resistance_chart_image_bytes",
                return_value=b"png-bytes",
            ),
            patch(
                "telegram_bot.router.build_support_resistance_message_text",
                return_value="SR terdekat BUMI",
            ),
            patch(
                "ui.screener.telegram_runner.send_telegram_photo",
                side_effect=RuntimeError("sendPhoto gagal"),
            ),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
        ):
            summary = process_pending_telegram_commands(last_command_update_id=551)

        self.assertEqual(summary["processed_count"], 1)
        self.assertEqual(summary["last_command_update_id"], 552)
        self.assertEqual(
            send_calls,
            [("777", "SR terdekat BUMI\n\nChart image belum berhasil dikirim sekarang, jadi saya kirim detail teks dulu.")],
        )

    def test_build_support_resistance_message_text_formats_nearest_levels(self) -> None:
        sample_result = type(
            "SampleResult",
            (),
            {
                "data": object(),
                "symbol": "BUMI",
                "company_name": "Bumi Resources Tbk.",
                "interval_label": "1 hari",
                "period_label": "1y",
                "previous_close": 136.0,
                "uses_bei_price_fractions": True,
            },
        )()
        sample_summary = {
            "current_price": 132.0,
            "support": {
                "price": 128.0,
                "zone_bottom": 126.0,
                "zone_top": 130.0,
                "bounces": 3,
            },
            "resistance": {
                "price": 138.0,
                "zone_bottom": 136.0,
                "zone_top": 140.0,
                "bounces": 2,
            },
        }

        with (
            patch("telegram_bot.support_resistance.load_market_data", return_value=sample_result),
            patch(
                "telegram_bot.support_resistance.describe_nearest_support_resistance",
                return_value=sample_summary,
            ) as describe_nearest_support_resistance,
        ):
            text = build_support_resistance_message_text("bumi", strong=False)

        self.assertIn("SR Terdekat BUMI", text)
        self.assertIn("Nama: Bumi Resources Tbk.", text)
        self.assertIn("Harga terakhir: 132 | 4 (-2.94%)", text)
        self.assertIn("Support:\n- Titik: 128\n- Zona: 126 - 130\n- Jarak: 3.03%\n- Pantulan: 3", text)
        self.assertIn("Resistance:\n- Titik: 138\n- Zona: 136 - 140\n- Jarak: 4.55%\n- Pantulan: 2", text)
        self.assertEqual(describe_nearest_support_resistance.call_args.args[0], sample_result.data)
        self.assertEqual(describe_nearest_support_resistance.call_args.args[1]["key"], "NEAREST_SUPPORT_RESISTANCE")

    def test_build_support_resistance_message_text_formats_strong_levels(self) -> None:
        sample_result = type(
            "SampleResult",
            (),
            {
                "data": object(),
                "symbol": "BUMI",
                "company_name": "Bumi Resources Tbk.",
                "interval_label": "1 hari",
                "period_label": "1y",
                "previous_close": 128.0,
                "uses_bei_price_fractions": True,
            },
        )()
        sample_summary = {
            "current_price": 132.0,
            "analysis_timeframe": "Daily",
            "support": {
                "price": 125.0,
                "zone_bottom": 123.0,
                "zone_top": 127.0,
                "bounces": 4,
                "breakout_count": 0,
                "high_volume_reversals": 2,
                "average_volume_ratio": 1.44,
            },
            "resistance": None,
        }

        with (
            patch("telegram_bot.support_resistance.load_market_data", return_value=sample_result),
            patch(
                "telegram_bot.support_resistance.describe_strong_support_resistance",
                return_value=sample_summary,
            ) as describe_strong_support_resistance,
        ):
            text = build_support_resistance_message_text("BUMI", strong=True)

        self.assertIn("SR Kuat BUMI", text)
        self.assertIn("Harga terakhir: 132 | 4 (+3.12%)", text)
        self.assertIn("Timeframe analisis: Daily", text)
        self.assertIn("Support:\n- Titik: 125\n- Zona: 123 - 127\n- Jarak: 5.30%\n- Pantulan: 4", text)
        self.assertIn("Breakout count: 0", text)
        self.assertIn("Reversal volume kuat: 2", text)
        self.assertIn("Rata-rata volume reversal: 1.44x", text)
        self.assertIn("Resistance:\n- Belum ketemu level yang valid", text)
        self.assertEqual(describe_strong_support_resistance.call_args.args[0], sample_result.data)
        self.assertEqual(describe_strong_support_resistance.call_args.args[1]["key"], "STRONG_SUPPORT_RESISTANCE")
        self.assertEqual(describe_strong_support_resistance.call_args.kwargs["interval_label"], "1 hari")

    def test_build_support_resistance_chart_image_bytes_returns_png(self) -> None:
        sample_result = type(
            "SampleResult",
            (),
            {
                "data": pd.DataFrame(
                    {
                        "time": pd.date_range("2026-01-01", periods=40, freq="D"),
                        "open": [100 + index for index in range(40)],
                        "high": [102 + index for index in range(40)],
                        "low": [98 + index for index in range(40)],
                        "close": [101 + index for index in range(40)],
                        "volume": [1_000 + (index * 25) for index in range(40)],
                    }
                ),
                "symbol": "BUMI",
                "company_name": "Bumi Resources Tbk.",
                "interval_label": "1 hari",
                "period_label": "1y",
            },
        )()
        sample_summary = {
            "current_price": 140.0,
            "support": {
                "price": 135.0,
                "zone_bottom": 133.0,
                "zone_top": 137.0,
                "bounces": 3,
            },
            "resistance": {
                "price": 145.0,
                "zone_bottom": 143.0,
                "zone_top": 147.0,
                "bounces": 2,
            },
        }

        with (
            patch("telegram_bot.support_resistance.load_market_data", return_value=sample_result),
            patch(
                "telegram_bot.support_resistance.describe_nearest_support_resistance",
                return_value=sample_summary,
            ),
        ):
            image_bytes = build_support_resistance_chart_image_bytes("BUMI", strong=False)

        self.assertIsNotNone(image_bytes)
        self.assertTrue(bool(image_bytes))
        self.assertTrue(bytes(image_bytes).startswith(b"\x89PNG"))
        with Image.open(BytesIO(image_bytes)) as image:
            self.assertLessEqual(image.size[0], 2500)
            self.assertLessEqual(image.size[1], 1600)

    def test_format_compact_axis_value_uses_short_suffixes(self) -> None:
        self.assertEqual(support_resistance_module._format_compact_axis_value(500), "500")
        self.assertEqual(support_resistance_module._format_compact_axis_value(12_500), "12.5K")
        self.assertEqual(support_resistance_module._format_compact_axis_value(500_000), "500K")
        self.assertEqual(support_resistance_module._format_compact_axis_value(125_000_000), "125M")

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

    def test_stop_telegram_worker_sends_nonaktif_message_to_alert_and_log(self) -> None:
        send_calls: list[tuple[str, str]] = []

        def _capture_send(bot_token: str, group_id: str, text: str) -> None:
            send_calls.append((group_id, text))

        with (
            patch(
                "ui.screener.telegram_runner.worker_state",
                return_value={
                    "pid": 12345,
                    "selected_symbols": ["BUMI", "MEDC"],
                    "interval_label": "1 hari",
                    "ema_period": 10,
                    "breakdown_confirm_mode": "body_breakdown",
                    "exit_mode": "ema_breakdown",
                    "interval_seconds": 300,
                },
            ),
            patch(
                "ui.screener.telegram_runner.load_telegram_settings",
                return_value={
                    "TELEGRAM_BOT_TOKEN": "token",
                    "TELEGRAM_GROUP_ID": "alert-group",
                    "TELEGRAM_GROUP_LOG_ID": "log-group",
                },
            ),
            patch("ui.screener.telegram_runner.send_telegram_text", side_effect=_capture_send),
            patch("ui.screener.telegram_runner.os.kill"),
            patch("ui.screener.telegram_runner.clear_worker_state"),
        ):
            stopped = stop_telegram_worker()

        self.assertTrue(stopped)
        self.assertEqual(len(send_calls), 2)
        self.assertEqual(send_calls[0][0], "alert-group")
        self.assertEqual(send_calls[1][0], "log-group")
        self.assertIn("Screener EMA 10 Nonaktif", send_calls[0][1])
        self.assertIn("Status akhir: Worker dihentikan, screening nonaktif.", send_calls[0][1])


if __name__ == "__main__":
    unittest.main()
