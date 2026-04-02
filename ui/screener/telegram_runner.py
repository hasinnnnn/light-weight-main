from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib import parse, request

import pandas as pd

from telegram_bot.catalog import TELEGRAM_BOT_COMMANDS
from telegram_bot.router import (
    build_command_help_text as build_root_command_help_text,
    build_inactive_worker_status_message_text as build_root_inactive_worker_status_message_text,
    process_pending_telegram_commands as process_root_pending_telegram_commands,
)
from ui.backtest.sections.parameter_forms import option_label
from ui.screener.signal_engine import build_break_ema_signal_snapshots
from ui.screener.table import SCREENER_SELECTION_COLUMN, build_screener_table_dataframe


ROOT_DIR = Path(__file__).resolve().parents[2]
CUSTOM_RUNTIME_DIR = str(os.environ.get("CHART_HASIN_RUNTIME_DIR", "") or "").strip()
RUNTIME_DIR = (
    Path(CUSTOM_RUNTIME_DIR).expanduser()
    if CUSTOM_RUNTIME_DIR
    else (Path(tempfile.gettempdir()) / "chart-hasin-runtime")
)
TELEGRAM_COMMAND_WORKER_STATE_PATH = RUNTIME_DIR / "screener_telegram_command_worker.json"
TELEGRAM_WORKER_STATE_PATH = RUNTIME_DIR / "screener_telegram_worker.json"
TELEGRAM_RUNTIME_STATE_PATH = RUNTIME_DIR / "screener_telegram_runtime.json"
TELEGRAM_COMMAND_CURSOR_PATH = RUNTIME_DIR / "screener_telegram_command_cursor.json"
TELEGRAM_COMMAND_POLL_LOCK_PATH = RUNTIME_DIR / "screener_telegram_command_poll.lock"
TELEGRAM_COMMAND_START_LOCK_PATH = RUNTIME_DIR / "screener_telegram_command_start.lock"
TELEGRAM_MESSAGE_MAX_LENGTH = 3500
TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS = 5
TELEGRAM_SEND_INTERVAL_SECONDS = 300
TELEGRAM_RUNTIME_EVENT_LIMIT = 300
TELEGRAM_COMMAND_LOCK_STALE_SECONDS = 30
VISIBLE_TELEGRAM_COLUMNS = [
    "Kode Saham",
    "Harga Sekarang",
    "Price Change",
    "Jumlah Trade",
    "Laba Bersih",
    "Win Rate Backtest EMA",
]
INDONESIAN_MONTH_NAMES = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def ensure_runtime_dir() -> None:
    """Create one local runtime directory for worker metadata."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def load_env_values(env_path: Path | None = None) -> dict[str, str]:
    """Parse one simple .env file into a key/value mapping."""
    resolved_env_path = env_path or (ROOT_DIR / ".env")
    if not resolved_env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in resolved_env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def load_os_env_values() -> dict[str, str]:
    """Read Telegram credentials from process environment variables."""
    values: dict[str, str] = {}
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID", "TELEGRAM_GROUP_LOG_ID", "TELEGRAM_USER_ID"):
        raw_value = os.environ.get(key, "")
        if str(raw_value).strip():
            values[key] = str(raw_value).strip()
    return values


def load_streamlit_secrets_values() -> dict[str, str]:
    """Read Telegram credentials from Streamlit secrets when available."""
    try:
        import streamlit as st
    except Exception:
        return {}

    try:
        secrets = st.secrets
    except Exception:
        return {}

    values: dict[str, str] = {}
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID", "TELEGRAM_GROUP_LOG_ID", "TELEGRAM_USER_ID"):
        try:
            raw_value = secrets.get(key, "")
        except Exception:
            try:
                raw_value = secrets[key]
            except Exception:
                raw_value = ""
        if str(raw_value).strip():
            values[key] = str(raw_value).strip()
    return values


def load_telegram_settings() -> dict[str, str]:
    """Load Telegram settings with deploy-friendly precedence."""
    values = load_env_values()
    values.update(load_os_env_values())
    values.update(load_streamlit_secrets_values())
    return values


def load_telegram_credentials() -> tuple[str, str]:
    """Read the bot token and main alert group id."""
    env_values = load_telegram_settings()
    return (
        str(env_values.get("TELEGRAM_BOT_TOKEN", "")).strip(),
        str(env_values.get("TELEGRAM_GROUP_ID", "")).strip(),
    )


def load_telegram_group_log_id() -> str:
    """Read the log-group destination used for every screening cycle."""
    env_values = load_telegram_settings()
    return str(env_values.get("TELEGRAM_GROUP_LOG_ID", "")).strip()


def load_telegram_admin_user_id() -> str:
    """Read one optional admin user id used to secure worker commands."""
    env_values = load_telegram_settings()
    return str(env_values.get("TELEGRAM_USER_ID", "")).strip()


def telegram_credentials_ready() -> bool:
    """Return whether the bot token, main group, and log group are all available."""
    bot_token, group_id = load_telegram_credentials()
    log_group_id = load_telegram_group_log_id()
    return bool(bot_token and group_id and log_group_id)


def build_selected_screener_dataframe(
    rows: list[dict[str, Any]],
    selected_symbols: Iterable[str],
) -> pd.DataFrame:
    """Build one filtered dataframe that keeps only the selected screener rows."""
    table_frame = build_screener_table_dataframe(rows, selected_symbols=selected_symbols)
    if table_frame.empty:
        return table_frame

    selected_frame = table_frame.loc[table_frame[SCREENER_SELECTION_COLUMN].fillna(False)].copy()
    if selected_frame.empty:
        return selected_frame
    return selected_frame[VISIBLE_TELEGRAM_COLUMNS].reset_index(drop=True)


def _call_telegram_api(
    bot_token: str,
    method_name: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call one Telegram Bot API method and return the decoded JSON payload."""
    encoded_payload: bytes | None = None
    request_method = "GET"
    if payload is not None:
        normalized_payload: dict[str, str] = {}
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, (dict, list, tuple)):
                normalized_payload[str(key)] = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
            else:
                normalized_payload[str(key)] = str(value)
        encoded_payload = parse.urlencode(normalized_payload).encode("utf-8")
        request_method = "POST"

    raw_response = request.urlopen(  # noqa: S310 - fixed Telegram API endpoint
        request.Request(
            url=f"https://api.telegram.org/bot{bot_token}/{method_name}",
            data=encoded_payload,
            method=request_method,
        ),
        timeout=15,
    ).read()
    decoded_response = json.loads(raw_response.decode("utf-8"))
    if not bool(decoded_response.get("ok", False)):
        description = str(decoded_response.get("description", "") or "").strip()
        raise RuntimeError(description or f"Telegram API `{method_name}` gagal dijalankan.")
    return decoded_response


def send_telegram_text(bot_token: str, group_id: str, text: str) -> None:
    """Send one plain-text message through the Telegram Bot API."""
    _call_telegram_api(
        bot_token,
        "sendMessage",
        {
            "chat_id": group_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    )


def send_telegram_photo(
    bot_token: str,
    group_id: str,
    photo_bytes: bytes,
    *,
    caption: str = "",
    filename: str = "chart.png",
) -> None:
    """Send one chart image through the Telegram Bot API."""
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise RuntimeError("Package `requests` belum tersedia untuk kirim foto Telegram.") from exc

    payload_data = {"chat_id": group_id}
    if caption:
        payload_data["caption"] = caption

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendPhoto",
        data=payload_data,
        files={"photo": (filename, photo_bytes, "image/png")},
        timeout=30,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if response.status_code >= 400 or not bool(payload.get("ok", False)):
        description = str(payload.get("description", "") or "").strip()
        if not description:
            description = str(response.text or "").strip()
        raise RuntimeError(description or "Telegram API `sendPhoto` gagal dijalankan.")


def sync_telegram_bot_commands(bot_token: str) -> None:
    """Register the Telegram slash-command menu shown in the chat UI."""
    _call_telegram_api(
        bot_token,
        "setMyCommands",
        {"commands": list(TELEGRAM_BOT_COMMANDS)},
    )


def sync_telegram_bot_commands_from_settings() -> None:
    """Sync Telegram commands using the bot token available in settings."""
    settings = load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    if not bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN wajib tersedia di Streamlit secrets, environment variable, atau .env."
        )
    sync_telegram_bot_commands(bot_token)


def fetch_telegram_updates(bot_token: str, *, offset: int | None = None) -> list[dict[str, Any]]:
    """Fetch pending Telegram updates used for simple bot commands."""
    payload = {"offset": max(int(offset or 0), 0)} if offset is not None else None
    response = _call_telegram_api(bot_token, "getUpdates", payload)
    raw_updates = response.get("result", [])
    if not isinstance(raw_updates, list):
        return []
    return [dict(update) for update in raw_updates]


def load_command_cursor() -> int:
    """Load the next Telegram update id shared across command-worker restarts."""
    if not TELEGRAM_COMMAND_CURSOR_PATH.exists():
        return 0
    try:
        payload = json.loads(TELEGRAM_COMMAND_CURSOR_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return max(int(payload.get("last_command_update_id", 0) or 0), 0)


def save_command_cursor(last_command_update_id: int) -> int:
    """Persist the next Telegram update id so duplicate replies are less likely."""
    ensure_runtime_dir()
    normalized_update_id = max(int(last_command_update_id or 0), 0)
    TELEGRAM_COMMAND_CURSOR_PATH.write_text(
        json.dumps({"last_command_update_id": normalized_update_id}, indent=2),
        encoding="utf-8",
    )
    return normalized_update_id


def _runtime_lock_is_stale(lock_path: Path) -> bool:
    """Return whether one runtime lock can be safely replaced."""
    if not lock_path.exists():
        return False

    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True

    pid = int(payload.get("pid", 0) or 0)
    if pid > 0 and not is_process_running(pid):
        return True

    try:
        lock_age_seconds = max((datetime.now().timestamp() - lock_path.stat().st_mtime), 0.0)
    except OSError:
        return True
    return lock_age_seconds >= float(TELEGRAM_COMMAND_LOCK_STALE_SECONDS)


def _acquire_runtime_lock(lock_path: Path) -> bool:
    """Acquire one short-lived runtime lock shared across Telegram workers."""
    ensure_runtime_dir()
    for _ in range(2):
        try:
            file_descriptor = os.open(
                str(lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError:
            if not _runtime_lock_is_stale(lock_path):
                return False
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                return False
            continue
        else:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                json.dump(
                    {
                        "pid": os.getpid(),
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                    },
                    lock_file,
                    indent=2,
                )
            return True
    return False


def _release_runtime_lock(lock_path: Path) -> None:
    """Release one runtime lock when this process currently owns it."""
    if not lock_path.exists():
        return

    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}

    lock_pid = int(payload.get("pid", 0) or 0)
    if lock_pid not in {0, os.getpid()}:
        return

    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def acquire_command_poll_lock() -> bool:
    """Acquire one short-lived lock so only one worker polls Telegram at a time."""
    return _acquire_runtime_lock(TELEGRAM_COMMAND_POLL_LOCK_PATH)


def release_command_poll_lock() -> None:
    """Release the shared Telegram polling lock when this worker owns it."""
    _release_runtime_lock(TELEGRAM_COMMAND_POLL_LOCK_PATH)


def acquire_command_start_lock() -> bool:
    """Acquire one short-lived lock so only one process starts the command worker."""
    return _acquire_runtime_lock(TELEGRAM_COMMAND_START_LOCK_PATH)


def release_command_start_lock() -> None:
    """Release the shared command-worker start lock when this process owns it."""
    _release_runtime_lock(TELEGRAM_COMMAND_START_LOCK_PATH)


def _current_local_datetime() -> datetime:
    """Return the current local datetime used for user-facing Telegram messages."""
    return datetime.now()


def _format_telegram_datetime(value: Any) -> str:
    """Format one user-facing Telegram timestamp like 2-April-2026 10:35:12."""
    if isinstance(value, pd.Timestamp):
        timestamp = value.to_pydatetime()
    elif isinstance(value, datetime):
        timestamp = value
    else:
        raw_text = str(value or "").strip()
        if not raw_text:
            return "-"
        try:
            timestamp = pd.Timestamp(raw_text).to_pydatetime()
        except Exception:
            return raw_text

    month_name = INDONESIAN_MONTH_NAMES.get(int(timestamp.month), f"{timestamp.month:02d}")
    return f"{timestamp.day}-{month_name}-{timestamp.year} {timestamp.strftime('%H:%M:%S')}"


def _resolve_event_display_datetime(event: dict[str, Any]) -> Any:
    """Prefer one human-friendly event time for alert messages.

    Daily/weekly event timestamps often arrive as date-only values from the backtest engine.
    In that case, keep the event date but replace the clock with the current local time so the
    Telegram alert reflects when the signal was actually detected.
    """
    time_text = str(event.get("time_text", "") or "").strip()
    if time_text and ":" not in time_text:
        try:
            base_datetime = pd.Timestamp(time_text).to_pydatetime()
            current_datetime = _current_local_datetime()
            return base_datetime.replace(
                hour=current_datetime.hour,
                minute=current_datetime.minute,
                second=current_datetime.second,
                microsecond=0,
            )
        except Exception:
            return time_text
    return event.get("time") or time_text


def load_runtime_state() -> dict[str, Any]:
    """Load one compact runtime state used to deduplicate live alerts."""
    if not TELEGRAM_RUNTIME_STATE_PATH.exists():
        return {
            "startup_main_sent": False,
            "sent_event_ids": [],
            "cycle_count": 0,
        }

    try:
        payload = json.loads(TELEGRAM_RUNTIME_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "startup_main_sent": False,
            "sent_event_ids": [],
            "cycle_count": 0,
        }

    sent_event_ids = [
        str(event_id).strip()
        for event_id in payload.get("sent_event_ids", [])
        if str(event_id).strip()
    ]
    return {
        "startup_main_sent": bool(payload.get("startup_main_sent", False)),
        "sent_event_ids": sent_event_ids[-TELEGRAM_RUNTIME_EVENT_LIMIT:],
        "cycle_count": max(int(payload.get("cycle_count", 0) or 0), 0),
        "last_cycle_at": str(payload.get("last_cycle_at", "")).strip(),
    }


def save_runtime_state(state: dict[str, Any]) -> None:
    """Persist one compact runtime state for the detached worker."""
    ensure_runtime_dir()
    normalized_ids: list[str] = []
    for event_id in state.get("sent_event_ids", []):
        cleaned_id = str(event_id).strip()
        if cleaned_id and cleaned_id not in normalized_ids:
            normalized_ids.append(cleaned_id)
    payload = {
        "startup_main_sent": bool(state.get("startup_main_sent", False)),
        "sent_event_ids": normalized_ids[-TELEGRAM_RUNTIME_EVENT_LIMIT:],
        "cycle_count": max(int(state.get("cycle_count", 0) or 0), 0),
        "last_cycle_at": str(state.get("last_cycle_at", "")).strip(),
    }
    TELEGRAM_RUNTIME_STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_runtime_state() -> None:
    """Remove the runtime state file when it exists."""
    try:
        TELEGRAM_RUNTIME_STATE_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _format_stock_rows(row: dict[str, Any]) -> list[str]:
    return [
        f"Kode Saham: {row.get('symbol') or '-'}",
        f"Harga Sekarang: {row.get('current_price_text') or '-'}",
        f"Price Change: {row.get('price_change_text') or '-'}",
        f"Jumlah Trade: {row.get('total_trades_text') or '-'}",
        f"Laba Bersih: {row.get('net_profit_text') or '-'}",
        f"Win Rate Backtest EMA: {row.get('win_rate_text') or '-'}",
    ]


def _iter_visible_note_boxes(note_payload: dict[str, Any] | None, action: str | None = None) -> Iterable[dict[str, Any]]:
    if not note_payload:
        return []
    normalized_action = str(action or "").strip().upper()
    for box in note_payload.get("boxes", []):
        label = str(box.get("label", "")).strip()
        if normalized_action == "BUY" and label == "Trigger exit":
            continue
        if normalized_action == "SELL" and label == "Trigger entry":
            continue
        yield dict(box)


def _build_note_box_lines(note_payload: dict[str, Any] | None, action: str | None = None) -> list[str]:
    lines: list[str] = []
    for box in _iter_visible_note_boxes(note_payload, action):
        label = str(box.get("label", "")).strip()
        value = str(box.get("value", "")).strip()
        detail_lines = [
            str(detail_line).strip()
            for detail_line in box.get("detail_lines", [])
            if str(detail_line).strip()
        ]
        if not label and not value and not detail_lines:
            continue

        if label:
            lines.append(f"{label}:")
        if value:
            lines.append(f"- {value}")
        lines.extend(f"- {detail_line}" for detail_line in detail_lines)
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _format_monitored_symbols(symbols: Iterable[str]) -> str:
    normalized_symbols = [
        str(symbol).strip().upper()
        for symbol in symbols
        if str(symbol).strip()
    ]
    return ", ".join(f"*** {symbol} ***" for symbol in normalized_symbols) if normalized_symbols else "-"


def build_command_help_text() -> str:
    """Build one compact help text matching the registered slash commands."""
    return build_root_command_help_text()


def build_worker_status_message_text(config: dict[str, Any], runtime_state: dict[str, Any] | None = None) -> str:
    """Build one admin-facing status message for Telegram bot commands."""
    active_runtime_state = runtime_state or load_runtime_state()
    last_cycle_text = _format_telegram_datetime(active_runtime_state.get("last_cycle_at", "") or "-")
    cycle_count = max(int(active_runtime_state.get("cycle_count", 0) or 0), 0)
    cycle_status_text = "Belum jalan"
    if bool(active_runtime_state.get("startup_main_sent", False)):
        cycle_status_text = "Startup" if cycle_count <= 0 else f"{cycle_count} X"

    selected_symbols = [
        str(symbol).strip().upper()
        for symbol in config.get("selected_symbols", [])
        if str(symbol).strip()
    ]
    return "\n".join(
        [
            f"Screener EMA {int(config['ema_period'])} Aktif",
            f"Waktu cek: {_format_telegram_datetime(_current_local_datetime())}",
            f"Cycle terakhir: {last_cycle_text}",
            f"Status cycle: {cycle_status_text}",
            f"Screening: tiap {int(config.get('interval_seconds', TELEGRAM_SEND_INTERVAL_SECONDS)) // 60} menit",
            f"Interval chart: {config['interval_label']}",
            (
                f"EMA: {int(config['ema_period'])} | Entry: {option_label(str(config['breakdown_confirm_mode']))} | "
                f"Exit: {option_label(str(config['exit_mode']))}"
            ),
            "",
            f"Saham dipantau ({len(selected_symbols)}): {_format_monitored_symbols(selected_symbols)}",
        ]
    )


def build_inactive_worker_status_message_text() -> str:
    """Build one Telegram status message shown when no screener worker is active."""
    return build_root_inactive_worker_status_message_text()


def _build_log_stock_block(signal_snapshot: dict[str, Any]) -> str:
    row = dict(signal_snapshot.get("row") or {})
    symbol = str(row.get("symbol") or signal_snapshot.get("symbol") or "-").strip().upper()
    current_price_text = str(row.get("current_price_text") or "-").strip()
    price_change_text = str(row.get("price_change_text") or "-").strip()
    error_text = str(signal_snapshot.get("error", "") or "").strip()

    lines = [f"*** {symbol} | {current_price_text} | {price_change_text} ***", ""]
    if error_text:
        lines.append(f"Error data: {error_text}")
        return "\n".join(lines)

    note_payload = signal_snapshot.get("note_payload") or {}
    summary_text = str(note_payload.get("summary_text", "")).strip()
    if summary_text:
        lines.extend([summary_text, ""])
    lines.extend(_build_note_box_lines(note_payload))
    return "\n".join(lines)


def build_startup_message_text(config: dict[str, Any]) -> str:
    """Build one immediate confirmation message sent when the worker starts."""
    selected_symbols = [
        str(symbol).strip().upper()
        for symbol in config.get("selected_symbols", [])
        if str(symbol).strip()
    ]
    timestamp_text = _format_telegram_datetime(_current_local_datetime())
    interval_seconds = int(config.get("interval_seconds", TELEGRAM_SEND_INTERVAL_SECONDS))
    monitored_symbols = _format_monitored_symbols(selected_symbols)
    return "\n".join(
        [
            f"Screener EMA {int(config['ema_period'])} Aktif",
            f"Waktu: {timestamp_text}",
            f"Screening: tiap {interval_seconds // 60} menit",
            f"Interval chart: {config['interval_label']}",
            (
                f"EMA: {int(config['ema_period'])} | Entry: {option_label(str(config['breakdown_confirm_mode']))} | "
                f"Exit: {option_label(str(config['exit_mode']))}"
            ),
            "Status awal: worker siap kirim alert BUY/SELL baru sesuai flow backtest BREAK_EMA.",
            "",
            f"Saham dipantau ({len(selected_symbols)}): {monitored_symbols}",
        ]
    )


def build_shutdown_message_text(config: dict[str, Any], *, reason_text: str = "Screening nonaktif.") -> str:
    """Build one stop message sent when the screener worker is intentionally turned off."""
    selected_symbols = [
        str(symbol).strip().upper()
        for symbol in config.get("selected_symbols", [])
        if str(symbol).strip()
    ]
    monitored_symbols = _format_monitored_symbols(selected_symbols)
    return "\n".join(
        [
            f"Screener EMA {int(config['ema_period'])} Nonaktif",
            f"Waktu: {_format_telegram_datetime(_current_local_datetime())}",
            f"Interval chart: {config['interval_label']}",
            (
                f"EMA: {int(config['ema_period'])} | Entry: {option_label(str(config['breakdown_confirm_mode']))} | "
                f"Exit: {option_label(str(config['exit_mode']))}"
            ),
            f"Status akhir: {reason_text}",
            "",
            f"Saham dipantau ({len(selected_symbols)}): {monitored_symbols}",
        ]
    )


def build_signal_message_text(
    signal_snapshot: dict[str, Any],
    event: dict[str, Any],
    config: dict[str, Any],
) -> str:
    """Build one detailed BUY/SELL Telegram message for the selected stock."""
    action = str(event["action"]).strip().upper()
    row = signal_snapshot["row"]
    note_payload = signal_snapshot.get("note_payload") or {}
    summary_text = str(note_payload.get("summary_text", "")).strip()
    symbol = str(row.get("symbol") or signal_snapshot.get("symbol") or "-").strip().upper()
    current_price_text = str(row.get("current_price_text") or "-").strip()
    price_change_text = str(row.get("price_change_text") or "-").strip()
    lines = [
        f"SINYAL {action} EMA {int(config['ema_period'])}",
        f"Waktu Event: {_format_telegram_datetime(_resolve_event_display_datetime(event))}",
        f"Interval chart: {config['interval_label']}",
        (
            f"EMA: {int(config['ema_period'])} | Entry: {option_label(str(config['breakdown_confirm_mode']))} | "
            f"Exit: {option_label(str(config['exit_mode']))}"
        ),
        "",
        f"*** {symbol} | {current_price_text} | {price_change_text} ***",
        "",
        "Backtest:",
        f"- Jumlah Trade: {row.get('total_trades_text') or '-'}",
        f"- Laba Bersih: {row.get('net_profit_text') or '-'}",
        f"- Win Rate: {row.get('win_rate_text') or '-'}",
    ]
    note_box_lines = _build_note_box_lines(note_payload, action)
    if summary_text or note_box_lines:
        lines.extend(["", "Keterangan:", ""])
        if summary_text:
            lines.extend([summary_text, ""])
        lines.extend(note_box_lines)
    return "\n".join(lines)


def build_screening_log_text(
    config: dict[str, Any],
    signal_snapshots: list[dict[str, Any]],
    *,
    is_startup_cycle: bool,
    cycle_count: int = 0,
) -> str:
    """Build one cycle log header sent to the dedicated screening log group."""
    timestamp_text = _format_telegram_datetime(_current_local_datetime())
    lines = [
        f"Waktu Cycle: {timestamp_text}",
        f"Status Cycle: {'Startup' if is_startup_cycle else f'{max(int(cycle_count), 1)} X'}",
        "",
        f"Interval chart: {config['interval_label']}",
        (
            f"EMA: {int(config['ema_period'])} | Entry: {option_label(str(config['breakdown_confirm_mode']))} | "
            f"Exit: {option_label(str(config['exit_mode']))}"
        ),
    ]
    return "\n".join(lines)


def build_screening_log_chunks(
    config: dict[str, Any],
    signal_snapshots: list[dict[str, Any]],
    *,
    is_startup_cycle: bool,
    cycle_count: int = 0,
) -> list[str]:
    """Split one detailed screening log into Telegram-safe chunks."""
    header_text = build_screening_log_text(
        config,
        signal_snapshots,
        is_startup_cycle=is_startup_cycle,
        cycle_count=cycle_count,
    )
    stock_blocks = [_build_log_stock_block(snapshot) for snapshot in signal_snapshots]
    if not stock_blocks:
        return [header_text]

    chunks: list[str] = []
    current_chunk = header_text
    for index, stock_block in enumerate(stock_blocks):
        separator = "\n\n----------\n\n" if index > 0 else "\n\n"
        if len(current_chunk) + len(separator) + len(stock_block) > TELEGRAM_MESSAGE_MAX_LENGTH:
            chunks.append(current_chunk)
            current_chunk = f"{header_text}\n\n{stock_block}"
        else:
            current_chunk = f"{current_chunk}{separator}{stock_block}"

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def worker_state() -> dict[str, Any] | None:
    """Load one active worker-state file when the process is still alive."""
    if not TELEGRAM_WORKER_STATE_PATH.exists():
        return None

    try:
        state = json.loads(TELEGRAM_WORKER_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    pid = int(state.get("pid", 0) or 0)
    if pid <= 0 or not is_process_running(pid):
        clear_worker_state()
        return None
    return state


def command_worker_state() -> dict[str, Any] | None:
    """Load one active Telegram command-worker state when the process is still alive."""
    if not TELEGRAM_COMMAND_WORKER_STATE_PATH.exists():
        return None

    try:
        state = json.loads(TELEGRAM_COMMAND_WORKER_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    pid = int(state.get("pid", 0) or 0)
    if pid <= 0 or not is_process_running(pid):
        clear_command_worker_state()
        return None
    return state


def command_worker_state_payload() -> dict[str, Any] | None:
    """Read the raw Telegram command-worker state payload without liveness checks."""
    if not TELEGRAM_COMMAND_WORKER_STATE_PATH.exists():
        return None

    try:
        state = json.loads(TELEGRAM_COMMAND_WORKER_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return state


def _worker_state_payload(path: Path) -> dict[str, Any] | None:
    """Read one raw worker state payload without liveness checks."""
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return state


def clear_worker_state() -> None:
    """Remove the saved worker-state and runtime files when they exist."""
    clear_runtime_state()
    try:
        TELEGRAM_WORKER_STATE_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def clear_command_worker_state() -> None:
    """Remove the saved Telegram command-worker state file when it exists."""
    try:
        TELEGRAM_COMMAND_WORKER_STATE_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def current_process_owns_command_worker_state() -> bool:
    """Return whether the saved command-worker state currently points to this process."""
    state = command_worker_state_payload()
    if not state:
        return False
    return int(state.get("pid", 0) or 0) == os.getpid()


def register_current_command_worker() -> dict[str, Any]:
    """Persist the actual pid of the running command worker process."""
    ensure_runtime_dir()
    existing_state = _worker_state_payload(TELEGRAM_COMMAND_WORKER_STATE_PATH) or {}
    state = {
        "pid": os.getpid(),
        "interval_seconds": int(
            existing_state.get("interval_seconds", TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS)
            or TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS
        ),
        "started_at": str(existing_state.get("started_at", "")).strip() or datetime.now().isoformat(timespec="seconds"),
    }
    TELEGRAM_COMMAND_WORKER_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def register_current_telegram_worker(config: dict[str, Any]) -> dict[str, Any]:
    """Persist the actual pid of the running screener worker process."""
    ensure_runtime_dir()
    existing_state = _worker_state_payload(TELEGRAM_WORKER_STATE_PATH) or {}
    state = {
        "pid": os.getpid(),
        "selected_symbols": [
            str(symbol).strip().upper()
            for symbol in config.get("selected_symbols", [])
            if str(symbol).strip()
        ],
        "interval_label": str(config.get("interval_label", "")).strip(),
        "ema_period": int(config.get("ema_period", 0) or 0),
        "breakdown_confirm_mode": str(config.get("breakdown_confirm_mode", "")).strip(),
        "exit_mode": str(config.get("exit_mode", "")).strip(),
        "interval_seconds": int(existing_state.get("interval_seconds", TELEGRAM_SEND_INTERVAL_SECONDS) or TELEGRAM_SEND_INTERVAL_SECONDS),
        "started_at": str(existing_state.get("started_at", "")).strip() or datetime.now().isoformat(timespec="seconds"),
    }
    TELEGRAM_WORKER_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def is_process_running(pid: int) -> bool:
    """Return whether one process id still exists."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_telegram_worker(*, send_notification: bool = True) -> bool:
    """Terminate the active Telegram worker when it is still running."""
    state = worker_state()
    if state is None:
        clear_worker_state()
        return False

    if send_notification:
        try:
            send_worker_shutdown_notifications(state, reason_text="Worker dihentikan, screening nonaktif.")
        except Exception:
            pass

    pid = int(state["pid"])
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    clear_worker_state()
    return True


def ensure_telegram_command_worker() -> dict[str, Any] | None:
    """Start one detached Telegram command listener when a bot token is available."""
    ensure_runtime_dir()
    active_state = command_worker_state()
    if active_state is not None:
        return active_state

    if not acquire_command_start_lock():
        return command_worker_state()

    try:
        active_state = command_worker_state()
        if active_state is not None:
            return active_state

        settings = load_telegram_settings()
        bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
        if not bot_token:
            return None

        try:
            sync_telegram_bot_commands(bot_token)
        except Exception:
            pass

        command = [
            sys.executable,
            "-m",
            "telegram_bot.command_worker",
        ]
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
        process = subprocess.Popen(
            command,
            cwd=str(ROOT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        state = {
            "pid": 0,
            "launcher_pid": process.pid,
            "interval_seconds": TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS,
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        TELEGRAM_COMMAND_WORKER_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state
    finally:
        release_command_start_lock()


def start_telegram_worker(
    *,
    selected_symbols: Iterable[str],
    interval_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> dict[str, Any]:
    """Start one detached worker process that checks fresh BUY/SELL signals every 5 minutes."""
    ensure_runtime_dir()
    ensure_telegram_command_worker()
    stop_telegram_worker(send_notification=False)
    clear_runtime_state()
    settings = load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    if bot_token:
        try:
            sync_telegram_bot_commands(bot_token)
        except Exception:
            pass

    normalized_symbols = [
        str(symbol).strip().upper()
        for symbol in selected_symbols
        if str(symbol).strip()
    ]
    command = [
        sys.executable,
        "-m",
        "ui.screener.telegram_worker",
        "--selected-symbols",
        ",".join(normalized_symbols),
        "--interval-label",
        str(interval_label),
        "--ema-period",
        str(int(ema_period)),
        "--breakdown-confirm-mode",
        str(breakdown_confirm_mode),
        "--exit-mode",
        str(exit_mode),
    ]

    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    process = subprocess.Popen(
        command,
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creation_flags,
    )

    state = {
        "pid": 0,
        "launcher_pid": process.pid,
        "selected_symbols": normalized_symbols,
        "interval_label": str(interval_label),
        "ema_period": int(ema_period),
        "breakdown_confirm_mode": str(breakdown_confirm_mode),
        "exit_mode": str(exit_mode),
        "interval_seconds": TELEGRAM_SEND_INTERVAL_SECONDS,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    TELEGRAM_WORKER_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def send_worker_shutdown_notifications(config: dict[str, Any], *, reason_text: str) -> None:
    """Send one worker stop message to both alert and log destinations."""
    settings = load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    alert_group_id = str(settings.get("TELEGRAM_GROUP_ID", "")).strip()
    log_group_id = str(settings.get("TELEGRAM_GROUP_LOG_ID", "")).strip()
    if not bot_token or not alert_group_id or not log_group_id:
        return

    shutdown_text = build_shutdown_message_text(config, reason_text=reason_text)
    send_telegram_text(bot_token, alert_group_id, shutdown_text)
    send_telegram_text(bot_token, log_group_id, shutdown_text)


def initialize_telegram_command_cursor(bot_token: str) -> int:
    """Return the next Telegram update id so stale commands are ignored on startup."""
    next_update_id = load_command_cursor()
    updates = fetch_telegram_updates(
        bot_token,
        offset=next_update_id if next_update_id > 0 else None,
    )
    for update in updates:
        next_update_id = max(next_update_id, int(update.get("update_id", -1) or -1) + 1)
    return save_command_cursor(next_update_id)


def process_pending_telegram_commands(*, last_command_update_id: int = 0) -> dict[str, Any]:
    """Reply to simple Telegram commands sent to the bot."""
    return process_root_pending_telegram_commands(last_command_update_id=last_command_update_id)


def run_worker_cycle(config: dict[str, Any]) -> dict[str, Any]:
    """Scan the selected symbols, send fresh alerts, and write one screening log entry."""
    settings = load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    alert_group_id = str(settings.get("TELEGRAM_GROUP_ID", "")).strip()
    log_group_id = str(settings.get("TELEGRAM_GROUP_LOG_ID", "")).strip()
    if not bot_token or not alert_group_id or not log_group_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID, dan TELEGRAM_GROUP_LOG_ID wajib tersedia di Streamlit secrets, environment variable, atau .env."
        )

    runtime_state = load_runtime_state()
    is_startup_cycle = not bool(runtime_state.get("startup_main_sent", False))
    if is_startup_cycle:
        send_telegram_text(bot_token, alert_group_id, build_startup_message_text(config))
        runtime_state["startup_main_sent"] = True
        log_cycle_count = 0
    else:
        log_cycle_count = max(int(runtime_state.get("cycle_count", 0) or 0), 0) + 1

    signal_snapshots = build_break_ema_signal_snapshots(
        config["selected_symbols"],
        interval_label=str(config["interval_label"]),
        ema_period=int(config["ema_period"]),
        breakdown_confirm_mode=str(config["breakdown_confirm_mode"]),
        exit_mode=str(config["exit_mode"]),
    )
    sent_event_ids = {
        str(event_id).strip()
        for event_id in runtime_state.get("sent_event_ids", [])
        if str(event_id).strip()
    }
    new_events: list[dict[str, Any]] = []
    for snapshot in signal_snapshots:
        for event in snapshot.get("fresh_events", []):
            event_id = str(event.get("event_id", "")).strip()
            if not event_id or event_id in sent_event_ids:
                continue
            send_telegram_text(bot_token, alert_group_id, build_signal_message_text(snapshot, event, config))
            sent_event_ids.add(event_id)
            new_events.append(event)

    for log_chunk in build_screening_log_chunks(
        config,
        signal_snapshots,
        is_startup_cycle=is_startup_cycle,
        cycle_count=log_cycle_count,
    ):
        send_telegram_text(bot_token, log_group_id, log_chunk)
    runtime_state["sent_event_ids"] = list(sent_event_ids)
    runtime_state["cycle_count"] = log_cycle_count
    runtime_state["last_cycle_at"] = datetime.now().isoformat(timespec="seconds")
    save_runtime_state(runtime_state)
    return {
        "startup_cycle": is_startup_cycle,
        "cycle_count": log_cycle_count,
        "signals_sent": len(new_events),
        "selected_symbols": len(signal_snapshots),
    }


__all__ = [
    "TELEGRAM_BOT_COMMANDS",
    "TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS",
    "TELEGRAM_SEND_INTERVAL_SECONDS",
    "build_command_help_text",
    "build_inactive_worker_status_message_text",
    "build_selected_screener_dataframe",
    "build_screening_log_text",
    "build_screening_log_chunks",
    "build_shutdown_message_text",
    "build_signal_message_text",
    "build_startup_message_text",
    "build_worker_status_message_text",
    "acquire_command_poll_lock",
    "acquire_command_start_lock",
    "clear_command_worker_state",
    "clear_worker_state",
    "command_worker_state_payload",
    "command_worker_state",
    "current_process_owns_command_worker_state",
    "ensure_telegram_command_worker",
    "fetch_telegram_updates",
    "initialize_telegram_command_cursor",
    "load_command_cursor",
    "load_telegram_admin_user_id",
    "load_telegram_credentials",
    "load_telegram_group_log_id",
    "load_telegram_settings",
    "process_pending_telegram_commands",
    "register_current_command_worker",
    "register_current_telegram_worker",
    "release_command_poll_lock",
    "release_command_start_lock",
    "run_worker_cycle",
    "save_command_cursor",
    "send_telegram_photo",
    "send_worker_shutdown_notifications",
    "start_telegram_worker",
    "stop_telegram_worker",
    "sync_telegram_bot_commands",
    "sync_telegram_bot_commands_from_settings",
    "telegram_credentials_ready",
    "worker_state",
]
