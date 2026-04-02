from __future__ import annotations

from telegram_bot.catalog import TELEGRAM_BOT_COMMANDS
from telegram_bot.support_resistance import (
    build_support_resistance_chart_image_bytes,
    build_support_resistance_message_text,
)


def build_command_help_text() -> str:
    """Build one compact help text matching the registered slash commands."""
    command_lines = [f"/{command['command']} - {command['description']}" for command in TELEGRAM_BOT_COMMANDS]
    return "\n".join(
        [
            "Bot Screener & Analisis",
            "",
            "Command tersedia:",
            *command_lines,
            "",
            "Contoh:",
            "- `/srd BUMI` untuk SR terdekat",
            "- `/srk BUMI` untuk SR kuat",
            "",
            "Catatan: `/stop` aman dipakai kalau `TELEGRAM_USER_ID` sudah diisi.",
        ]
    )


def build_inactive_worker_status_message_text() -> str:
    """Build one Telegram status message shown when no screener worker is active."""
    return "\n".join(
        [
            "Screener belum aktif.",
            "Buka halaman Screener di app lalu tekan `Screen` untuk mulai kirim alert otomatis.",
        ]
    )


def _extract_symbol_argument(command_text: str) -> str:
    parts = [part.strip() for part in str(command_text or "").split() if part.strip()]
    if len(parts) <= 1:
        return ""
    return str(parts[1]).strip().upper()


def _send_support_resistance_response(
    *,
    bot_token: str,
    chat_id: str,
    symbol: str,
    strong: bool,
) -> None:
    from ui.screener import telegram_runner as screener_telegram_runner

    message_text = build_support_resistance_message_text(symbol, strong=strong)
    chart_error_message = ""
    try:
        chart_bytes = build_support_resistance_chart_image_bytes(symbol, strong=strong)
        if chart_bytes:
            screener_telegram_runner.send_telegram_photo(
                bot_token,
                chat_id,
                chart_bytes,
                caption=message_text,
                filename=f"{'srk' if strong else 'srd'}_{symbol.lower() or 'chart'}.png",
            )
            return
    except Exception:
        chart_error_message = "Chart image belum berhasil dikirim sekarang, jadi saya kirim detail teks dulu."

    fallback_text = message_text
    if chart_error_message:
        fallback_text = f"{message_text}\n\n{chart_error_message}"
    screener_telegram_runner.send_telegram_text(bot_token, chat_id, fallback_text)


def process_pending_telegram_commands(*, last_command_update_id: int = 0) -> dict[str, int]:
    """Reply to simple Telegram commands sent to the bot."""
    from ui.screener import telegram_runner as screener_telegram_runner

    settings = screener_telegram_runner.load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    admin_user_id = str(settings.get("TELEGRAM_USER_ID", "")).strip()
    if not bot_token:
        return {"processed_count": 0, "last_command_update_id": 0}

    next_update_id = max(int(last_command_update_id or 0), 0)
    updates = screener_telegram_runner.fetch_telegram_updates(
        bot_token,
        offset=next_update_id if next_update_id > 0 else None,
    )
    if not updates:
        return {
            "processed_count": 0,
            "last_command_update_id": next_update_id,
        }

    processed_count = 0
    for update in updates:
        next_update_id = max(next_update_id, int(update.get("update_id", -1) or -1) + 1)
        message = update.get("message") or update.get("edited_message") or {}
        if not isinstance(message, dict):
            continue

        command_text = str(message.get("text", "") or "").strip()
        if not command_text.startswith("/"):
            continue

        processed_count += 1
        chat_id = str((message.get("chat") or {}).get("id", "") or "").strip()
        sender_id = str((message.get("from") or {}).get("id", "") or "").strip()
        if not chat_id:
            continue

        normalized_command = command_text.split()[0].split("@")[0].lower()
        if normalized_command in {"/start", "/help"}:
            screener_telegram_runner.send_telegram_text(bot_token, chat_id, build_command_help_text())
            continue
        if normalized_command == "/status":
            if admin_user_id and sender_id != admin_user_id:
                screener_telegram_runner.send_telegram_text(
                    bot_token,
                    chat_id,
                    "Command `/status` khusus admin yang ID Telegram-nya cocok dengan `TELEGRAM_USER_ID`.",
                )
            else:
                active_worker = screener_telegram_runner.worker_state()
                if active_worker is None:
                    screener_telegram_runner.send_telegram_text(
                        bot_token,
                        chat_id,
                        build_inactive_worker_status_message_text(),
                    )
                else:
                    screener_telegram_runner.send_telegram_text(
                        bot_token,
                        chat_id,
                        screener_telegram_runner.build_worker_status_message_text(active_worker),
                    )
            continue
        if normalized_command == "/stop":
            if not admin_user_id:
                screener_telegram_runner.send_telegram_text(
                    bot_token,
                    chat_id,
                    "Isi `TELEGRAM_USER_ID` dulu supaya command `/stop` aman dipakai.",
                )
                continue
            if sender_id != admin_user_id:
                screener_telegram_runner.send_telegram_text(
                    bot_token,
                    chat_id,
                    "Command `/stop` khusus admin yang ID Telegram-nya cocok dengan `TELEGRAM_USER_ID`.",
                )
                continue
            active_worker = screener_telegram_runner.worker_state()
            if active_worker is None:
                screener_telegram_runner.send_telegram_text(
                    bot_token,
                    chat_id,
                    "Worker screener belum aktif, jadi belum ada yang perlu dihentikan.",
                )
                continue
            screener_telegram_runner.stop_telegram_worker()
            screener_telegram_runner.send_telegram_text(
                bot_token,
                chat_id,
                "Perintah `/stop` diterima. Worker screener akan dimatikan.",
            )
            continue
        if normalized_command == "/srd":
            _send_support_resistance_response(
                bot_token=bot_token,
                chat_id=chat_id,
                symbol=_extract_symbol_argument(command_text),
                strong=False,
            )
            continue
        if normalized_command == "/srk":
            _send_support_resistance_response(
                bot_token=bot_token,
                chat_id=chat_id,
                symbol=_extract_symbol_argument(command_text),
                strong=True,
            )
            continue

        screener_telegram_runner.send_telegram_text(
            bot_token,
            chat_id,
            "Command belum dikenali. Ketik `/help` untuk lihat daftar command bot.",
        )

    return {
        "processed_count": processed_count,
        "last_command_update_id": next_update_id,
    }


__all__ = [
    "build_command_help_text",
    "build_inactive_worker_status_message_text",
    "process_pending_telegram_commands",
]
