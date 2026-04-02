from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from telegram_bot.command_worker import stop_background_command_worker
from ui.screener.telegram_runner import clear_command_worker_state, ensure_telegram_command_worker

ROOT_DIR = Path(__file__).resolve().parent


def build_streamlit_command(*extra_args: str) -> list[str]:
    """Build one deploy-friendly Streamlit command with the platform port when provided."""
    port = str(os.environ.get("PORT", "8501") or "8501").strip() or "8501"
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address=0.0.0.0",
        f"--server.port={port}",
    ]
    command.extend(str(argument) for argument in extra_args if str(argument).strip())
    return command


def main() -> int:
    ensure_telegram_command_worker()
    process = subprocess.Popen(
        build_streamlit_command(*sys.argv[1:]),
        cwd=str(ROOT_DIR),
    )
    try:
        return int(process.wait())
    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        return int(process.wait())
    finally:
        stop_background_command_worker(join_timeout_seconds=0.5)
        clear_command_worker_state()


if __name__ == "__main__":
    raise SystemExit(main())
