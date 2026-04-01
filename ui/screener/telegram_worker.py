from __future__ import annotations

import argparse
import sys
import time
from typing import Any

from ui.screener.telegram_runner import TELEGRAM_SEND_INTERVAL_SECONDS, run_worker_cycle


def _parse_args() -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Telegram worker for the EMA screener.")
    parser.add_argument("--selected-symbols", required=True)
    parser.add_argument("--interval-label", required=True)
    parser.add_argument("--period-label", required=True)
    parser.add_argument("--ema-period", required=True, type=int)
    parser.add_argument("--breakdown-confirm-mode", required=True)
    parser.add_argument("--exit-mode", required=True)
    parsed = parser.parse_args()
    return {
        "selected_symbols": [
            symbol.strip().upper()
            for symbol in str(parsed.selected_symbols).split(",")
            if symbol.strip()
        ],
        "interval_label": str(parsed.interval_label),
        "period_label": str(parsed.period_label),
        "ema_period": int(parsed.ema_period),
        "breakdown_confirm_mode": str(parsed.breakdown_confirm_mode),
        "exit_mode": str(parsed.exit_mode),
    }


def main() -> int:
    config = _parse_args()
    while True:
        try:
            run_worker_cycle(config)
        except KeyboardInterrupt:
            return 0
        except Exception:
            # Keep the worker alive so transient network/data issues do not kill the schedule.
            pass
        time.sleep(TELEGRAM_SEND_INTERVAL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
