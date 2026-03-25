from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from config.chart_options import INTRADAY_INTERVALS, JAKARTA_TIMEZONE


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
    return interval_code in INTRADAY_INTERVALS


def format_timestamp(value: pd.Timestamp | datetime | None) -> str:
    """Format timestamps consistently for the info panel."""
    if value is None:
        return "-"

    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return "-"

    is_date_only = (
        timestamp.hour == 0
        and timestamp.minute == 0
        and timestamp.second == 0
        and timestamp.microsecond == 0
    )

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    timestamp = timestamp.tz_convert(JAKARTA_TIMEZONE).tz_localize(None)

    if is_date_only:
        return timestamp.strftime("%Y-%m-%d")

    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
