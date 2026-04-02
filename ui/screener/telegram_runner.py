from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib import parse, request

import pandas as pd

from ui.backtest.sections.parameter_forms import option_label
from ui.screener.signal_engine import build_break_ema_signal_snapshots
from ui.screener.table import SCREENER_SELECTION_COLUMN, build_screener_table_dataframe


ROOT_DIR = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT_DIR / ".runtime"
TELEGRAM_WORKER_STATE_PATH = RUNTIME_DIR / "screener_telegram_worker.json"
TELEGRAM_RUNTIME_STATE_PATH = RUNTIME_DIR / "screener_telegram_runtime.json"
TELEGRAM_MESSAGE_MAX_LENGTH = 3500
TELEGRAM_SEND_INTERVAL_SECONDS = 300
TELEGRAM_RUNTIME_EVENT_LIMIT = 300
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


def send_telegram_text(bot_token: str, group_id: str, text: str) -> None:
    """Send one plain-text message through the Telegram Bot API."""
    payload = parse.urlencode(
        {
            "chat_id": group_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request.urlopen(  # noqa: S310 - fixed Telegram API endpoint
        request.Request(
            url=f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=payload,
            method="POST",
        ),
        timeout=15,
    ).read()


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
        return {"startup_main_sent": False, "sent_event_ids": [], "cycle_count": 0}

    try:
        payload = json.loads(TELEGRAM_RUNTIME_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"startup_main_sent": False, "sent_event_ids": [], "cycle_count": 0}

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


def clear_worker_state() -> None:
    """Remove the saved worker-state and runtime files when they exist."""
    clear_runtime_state()
    try:
        TELEGRAM_WORKER_STATE_PATH.unlink(missing_ok=True)
    except OSError:
        pass


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
            settings = load_telegram_settings()
            bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
            alert_group_id = str(settings.get("TELEGRAM_GROUP_ID", "")).strip()
            log_group_id = str(settings.get("TELEGRAM_GROUP_LOG_ID", "")).strip()
            if bot_token and alert_group_id and log_group_id:
                shutdown_text = build_shutdown_message_text(
                    state,
                    reason_text="Worker dihentikan, screening nonaktif.",
                )
                send_telegram_text(bot_token, alert_group_id, shutdown_text)
                send_telegram_text(bot_token, log_group_id, shutdown_text)
        except Exception:
            pass

    pid = int(state["pid"])
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    clear_worker_state()
    return True


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
    stop_telegram_worker(send_notification=False)
    clear_runtime_state()

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
        "pid": process.pid,
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
    "TELEGRAM_SEND_INTERVAL_SECONDS",
    "build_selected_screener_dataframe",
    "build_screening_log_text",
    "build_screening_log_chunks",
    "build_shutdown_message_text",
    "build_signal_message_text",
    "build_startup_message_text",
    "clear_worker_state",
    "load_telegram_credentials",
    "load_telegram_group_log_id",
    "load_telegram_settings",
    "run_worker_cycle",
    "start_telegram_worker",
    "stop_telegram_worker",
    "telegram_credentials_ready",
    "worker_state",
]
