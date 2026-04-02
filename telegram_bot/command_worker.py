from __future__ import annotations

import sys
import threading
import time
from typing import Any

from telegram_bot.router import process_pending_telegram_commands
from ui.screener.telegram_runner import (
    TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS,
    acquire_command_poll_lock,
    clear_command_worker_state,
    current_process_owns_command_worker_state,
    initialize_telegram_command_cursor,
    load_telegram_settings,
    register_current_command_worker,
    release_command_poll_lock,
    save_command_cursor,
    sync_telegram_bot_commands,
)

_COMMAND_THREAD_LOCK = threading.Lock()
_COMMAND_THREAD: threading.Thread | None = None
_COMMAND_STOP_EVENT: threading.Event | None = None


def _sleep_until_next_poll(stop_event: threading.Event | None) -> bool:
    """Wait until the next polling cycle or stop immediately when requested."""
    if stop_event is None:
        time.sleep(TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS)
        return False
    return bool(stop_event.wait(TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS))


def _run_command_listener_loop(*, stop_event: threading.Event | None = None) -> int:
    """Poll Telegram updates until the process or caller asks this listener to stop."""
    settings = load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    if not bot_token:
        clear_command_worker_state()
        return 0

    register_current_command_worker()

    try:
        sync_telegram_bot_commands(bot_token)
    except Exception:
        pass

    next_update_id = initialize_telegram_command_cursor(bot_token)
    while stop_event is None or not stop_event.is_set():
        if not current_process_owns_command_worker_state():
            return 0
        if not acquire_command_poll_lock():
            if _sleep_until_next_poll(stop_event):
                return 0
            continue
        try:
            summary = process_pending_telegram_commands(last_command_update_id=next_update_id)
            next_update_id = max(int(summary.get("last_command_update_id", next_update_id) or next_update_id), 0)
            save_command_cursor(next_update_id)
        except KeyboardInterrupt:
            clear_command_worker_state()
            return 0
        except Exception:
            # Keep the command listener alive when Telegram polling fails temporarily.
            pass
        finally:
            release_command_poll_lock()
        if _sleep_until_next_poll(stop_event):
            return 0
    return 0


def _run_background_command_listener(stop_event: threading.Event) -> None:
    """Own the singleton background listener thread and clean its state on exit."""
    global _COMMAND_THREAD, _COMMAND_STOP_EVENT
    try:
        _run_command_listener_loop(stop_event=stop_event)
    finally:
        clear_command_worker_state()
        with _COMMAND_THREAD_LOCK:
            if _COMMAND_STOP_EVENT is stop_event:
                _COMMAND_STOP_EVENT = None
            if _COMMAND_THREAD is threading.current_thread():
                _COMMAND_THREAD = None


def background_command_worker_alive() -> bool:
    """Return whether this process currently owns a live background command listener."""
    with _COMMAND_THREAD_LOCK:
        return _COMMAND_THREAD is not None and _COMMAND_THREAD.is_alive()


def start_background_command_worker() -> dict[str, Any] | None:
    """Start the Telegram command listener as one singleton daemon thread."""
    global _COMMAND_THREAD, _COMMAND_STOP_EVENT
    settings = load_telegram_settings()
    bot_token = str(settings.get("TELEGRAM_BOT_TOKEN", "")).strip()
    if not bot_token:
        clear_command_worker_state()
        return None

    with _COMMAND_THREAD_LOCK:
        if _COMMAND_THREAD is not None and _COMMAND_THREAD.is_alive():
            return register_current_command_worker()

        try:
            sync_telegram_bot_commands(bot_token)
        except Exception:
            pass

        state = register_current_command_worker()
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_run_background_command_listener,
            args=(stop_event,),
            name="telegram-command-worker",
            daemon=True,
        )

        _COMMAND_THREAD = thread
        _COMMAND_STOP_EVENT = stop_event
        thread.start()
        return state


def stop_background_command_worker(*, join_timeout_seconds: float = 1.0) -> None:
    """Ask the singleton background listener to stop when this process owns it."""
    with _COMMAND_THREAD_LOCK:
        stop_event = _COMMAND_STOP_EVENT
        thread = _COMMAND_THREAD

    if stop_event is None:
        clear_command_worker_state()
        return

    stop_event.set()
    if thread is not None and thread.is_alive():
        thread.join(timeout=max(float(join_timeout_seconds), 0.0))


def main() -> int:
    return _run_command_listener_loop()


if __name__ == "__main__":
    sys.exit(main())
