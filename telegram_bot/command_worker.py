from __future__ import annotations

import sys
import time

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


def main() -> int:
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
    while True:
        if not current_process_owns_command_worker_state():
            return 0
        if not acquire_command_poll_lock():
            time.sleep(TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS)
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
        time.sleep(TELEGRAM_COMMAND_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
