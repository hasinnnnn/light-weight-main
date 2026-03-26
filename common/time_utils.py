from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from config.chart_options import INTERVAL_LABEL_TO_CODE, INTRADAY_INTERVALS, JAKARTA_TIMEZONE

ID_MONTH_ABBREVIATIONS = {
    1: "jan",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "mei",
    6: "jun",
    7: "jul",
    8: "agu",
    9: "sep",
    10: "okt",
    11: "nov",
    12: "des",
}


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def inclusive_request_end() -> datetime:
    """Return an end timestamp that safely includes the current trading day."""
    return utc_now() + timedelta(days=1)


def period_lookback_days(period_label: str, now: datetime | None = None) -> int | None:
    """Estimate the requested calendar-day lookback for a UI period selection."""
    lookup = {
        "1d": 1,
        "5d": 5,
        "1wk": 7,
        "2wk": 14,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
    }
    if period_label in lookup:
        return lookup[period_label]
    if period_label == "YTD":
        now = now or utc_now()
        start_of_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)
        return max(1, (now - start_of_year).days + 1)
    if period_label == "ALL":
        return None
    raise ValueError(f"Unsupported period label: {period_label}")


def is_intraday_interval(interval_code: str) -> bool:
    """Return True when the interval should be treated as intraday."""
    normalized_value = str(interval_code or "").strip()
    if not normalized_value:
        return False
    interval_code = INTERVAL_LABEL_TO_CODE.get(normalized_value, normalized_value)
    return interval_code in INTRADAY_INTERVALS


def _coerce_display_timestamp(value: Any) -> tuple[pd.Timestamp | None, bool]:
    """Convert raw values into one timestamp plus a date-only flag for UI display."""
    if value is None:
        return None, True

    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None, True

    if pd.isna(timestamp):
        return None, True

    is_date_only = (
        timestamp.hour == 0
        and timestamp.minute == 0
        and timestamp.second == 0
        and timestamp.microsecond == 0
    )

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(None)
    else:
        timestamp = timestamp.tz_convert(JAKARTA_TIMEZONE).tz_localize(None)

    return timestamp, is_date_only


def format_short_date_label(value: Any) -> str:
    """Format raw dates into Indonesian compact labels like 25 jan 2026."""
    raw_text = str(value or "").strip()
    timestamp, _ = _coerce_display_timestamp(value)
    if timestamp is None:
        return raw_text or "-"

    month_label = ID_MONTH_ABBREVIATIONS.get(int(timestamp.month), f"{int(timestamp.month):02d}")
    return f"{int(timestamp.day):02d} {month_label} {int(timestamp.year)}"


def format_short_timestamp_label(value: Any) -> str:
    """Format raw timestamps into Indonesian compact labels while keeping time when present."""
    raw_text = str(value or "").strip()
    timestamp, is_date_only = _coerce_display_timestamp(value)
    if timestamp is None:
        return raw_text or "-"

    date_label = format_short_date_label(timestamp)
    if is_date_only:
        return date_label
    return f"{date_label} {timestamp.strftime('%H:%M')}"


def format_timestamp(value: pd.Timestamp | datetime | None) -> str:
    """Format timestamps consistently for the info panel."""
    return format_short_timestamp_label(value)

