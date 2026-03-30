from __future__ import annotations

from typing import Any

from common.time_utils import format_short_date_label, format_short_timestamp_label, is_intraday_interval


def format_price_value(value: float) -> str:
    """Format the latest price compactly for the insight card."""
    absolute_value = abs(value)
    if absolute_value >= 100 and abs(value - round(value)) < 1e-9:
        return f"{value:,.0f}"
    if absolute_value >= 1:
        return f"{value:,.2f}"
    return f"{value:,.4f}"


def format_pattern_time_label(value: Any, interval_label: str | None) -> str:
    """Show time for intraday pattern tables and date-only for daily-or-higher charts."""
    if interval_label and is_intraday_interval(interval_label):
        return format_short_timestamp_label(value)
    return format_short_date_label(value)


def format_metric_value(value: float | None, use_integer_price: bool = False) -> str:
    """Format one small metric value for the quote summary area."""
    if value is None:
        return "-"
    if use_integer_price:
        return f"{value:,.0f}"
    return format_price_value(float(value))


def format_signed_percent(value: float) -> str:
    """Format one percentage with an explicit sign only when it moves."""
    if value > 0:
        return f"+{value:.2f}%"
    if value < 0:
        return f"{value:.2f}%"
    return "0.00%"


def format_price_change_value(
    value: float,
    use_integer_price: bool = False,
    *,
    include_sign: bool = True,
) -> str:
    """Format one absolute price change using market-appropriate precision."""
    absolute_value = abs(float(value))
    if absolute_value < 1e-9:
        return "0" if use_integer_price else "0.00"

    if use_integer_price:
        formatted_value = f"{absolute_value:,.0f}"
    else:
        formatted_value = format_price_value(absolute_value)

    if not include_sign:
        return formatted_value
    if value < 0:
        return f"-{formatted_value}"
    return formatted_value


def format_price_change_with_percent(
    change_value: float,
    change_percent: float,
    *,
    use_integer_price: bool = False,
    include_sign: bool = True,
) -> str:
    """Format one combined price-change block like `15 (+0.93%)`."""
    return (
        f"{format_price_change_value(change_value, use_integer_price=use_integer_price, include_sign=include_sign)} "
        f"({format_signed_percent(change_percent)})"
    )


def format_compact_metric(value: float | None) -> str:
    """Format one large count/value into K/M/B/T notation."""
    if value is None:
        return "-"

    absolute_value = abs(float(value))
    suffixes = [
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]
    for threshold, suffix in suffixes:
        if absolute_value >= threshold:
            return f"{value / threshold:.2f}{suffix}"
    if abs(value - round(value)) < 1e-9:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def format_date_label(value: Any) -> str:
    """Format one raw date-like value into Indonesian short-date style."""
    return format_short_date_label(value)
