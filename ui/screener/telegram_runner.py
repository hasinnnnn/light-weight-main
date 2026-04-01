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
from ui.screener.data import build_ema_screener_rows
from ui.screener.table import SCREENER_SELECTION_COLUMN, build_screener_table_dataframe


ROOT_DIR = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT_DIR / ".runtime"
TELEGRAM_WORKER_STATE_PATH = RUNTIME_DIR / "screener_telegram_worker.json"
TELEGRAM_MESSAGE_MAX_LENGTH = 3500
TELEGRAM_SEND_INTERVAL_SECONDS = 30
VISIBLE_TELEGRAM_COLUMNS = [
    "Kode Saham",
    "Harga Sekarang",
    "Price Change",
    "Jumlah Trade",
    "Laba Bersih",
    "Win Rate Backtest EMA",
]


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
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID", "TELEGRAM_USER_ID"):
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
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID", "TELEGRAM_USER_ID"):
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
    """Read Telegram bot credentials from Streamlit secrets, env vars, or .env."""
    env_values = load_telegram_settings()
    return (
        str(env_values.get("TELEGRAM_BOT_TOKEN", "")).strip(),
        str(env_values.get("TELEGRAM_GROUP_ID", "")).strip(),
    )


def telegram_credentials_ready() -> bool:
    """Return whether both Telegram token and group id are available."""
    bot_token, group_id = load_telegram_credentials()
    return bool(bot_token and group_id)


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


def _build_message_header(config: dict[str, Any], selected_count: int) -> str:
    timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        "Screener EMA\n"
        f"Waktu: {timestamp_text}\n"
        f"Interval: {config['interval_label']} | Periode: {config['period_label']}\n"
        f"EMA: {int(config['ema_period'])} | Entry: {option_label(str(config['breakdown_confirm_mode']))} | "
        f"Exit: {option_label(str(config['exit_mode']))}\n"
        f"Jumlah saham terpilih: {selected_count}"
    )


def _build_stock_block(row: pd.Series) -> str:
    lines = [f"Kode Saham: {row['Kode Saham']}"]
    for column_name in VISIBLE_TELEGRAM_COLUMNS[1:]:
        lines.append(f"{column_name}: {row[column_name]}")
    return "\n".join(lines)


def build_telegram_message_chunks(
    rows: list[dict[str, Any]],
    selected_symbols: Iterable[str],
    config: dict[str, Any],
) -> list[str]:
    """Format the selected screener rows into Telegram-sized message chunks."""
    selected_frame = build_selected_screener_dataframe(rows, selected_symbols)
    header_text = _build_message_header(config, len(selected_frame))
    if selected_frame.empty:
        return [f"{header_text}\n\nBelum ada saham yang diceklis."]

    chunks: list[str] = []
    current_chunk = header_text
    for _, row in selected_frame.iterrows():
        stock_block = _build_stock_block(row)
        separator = "\n\n" if current_chunk else ""
        if len(current_chunk) + len(separator) + len(stock_block) > TELEGRAM_MESSAGE_MAX_LENGTH:
            chunks.append(current_chunk)
            current_chunk = f"{header_text}\n\n{stock_block}"
        else:
            current_chunk = f"{current_chunk}{separator}{stock_block}"

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


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
    """Remove the saved worker-state file when it exists."""
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


def stop_telegram_worker() -> bool:
    """Terminate the active Telegram worker when it is still running."""
    state = worker_state()
    if state is None:
        clear_worker_state()
        return False

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
    period_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> dict[str, Any]:
    """Start one detached worker process that sends the selected screener rows every 30 seconds."""
    ensure_runtime_dir()
    stop_telegram_worker()

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
        "--period-label",
        str(period_label),
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
        "period_label": str(period_label),
        "ema_period": int(ema_period),
        "breakdown_confirm_mode": str(breakdown_confirm_mode),
        "exit_mode": str(exit_mode),
        "interval_seconds": TELEGRAM_SEND_INTERVAL_SECONDS,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    TELEGRAM_WORKER_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def run_worker_cycle(config: dict[str, Any]) -> None:
    """Build the latest screener data and send it to Telegram for one cycle."""
    bot_token, group_id = load_telegram_credentials()
    if not bot_token or not group_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN atau TELEGRAM_GROUP_ID belum tersedia di Streamlit secrets, environment variable, atau .env."
        )

    rows = build_ema_screener_rows(
        interval_label=str(config["interval_label"]),
        period_label=str(config["period_label"]),
        ema_period=int(config["ema_period"]),
        breakdown_confirm_mode=str(config["breakdown_confirm_mode"]),
        exit_mode=str(config["exit_mode"]),
    )
    for message_chunk in build_telegram_message_chunks(rows, config["selected_symbols"], config):
        send_telegram_text(bot_token, group_id, message_chunk)


__all__ = [
    "TELEGRAM_SEND_INTERVAL_SECONDS",
    "build_selected_screener_dataframe",
    "build_telegram_message_chunks",
    "clear_worker_state",
    "load_telegram_credentials",
    "load_telegram_settings",
    "run_worker_cycle",
    "start_telegram_worker",
    "stop_telegram_worker",
    "telegram_credentials_ready",
    "worker_state",
]
