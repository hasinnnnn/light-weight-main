from __future__ import annotations

import html
from typing import Any

from common.time_utils import format_short_date_label

from .formatters import format_price_value

def format_price_distance_percentage(current_price: float, target_price: float) -> str:
    """Format the percentage distance between the last price and one level."""
    if current_price == 0:
        return "0.00%"
    return f"{abs((target_price - current_price) / current_price) * 100:.2f}%"


def format_break_event_dates_text(
    label: str,
    event_dates: list[str] | None,
) -> str:
    """Format breakout/breakdown event dates for the explanation card."""
    cleaned_dates = [format_short_date_label(value) for value in (event_dates or []) if str(value).strip()]
    if not cleaned_dates:
        return f"Tanggal {label}: belum ada"
    return f"Tanggal {label}: {', '.join(cleaned_dates)}"


def format_support_resistance_zone(level: dict[str, Any]) -> str:
    """Format one support/resistance zone into a compact label."""
    return (
        f"{format_price_value(float(level['zone_bottom']))} - "
        f"{format_price_value(float(level['zone_top']))}"
    )


def format_consolidation_area(area: dict[str, Any]) -> str:
    """Format one consolidation zone into a compact label."""
    return (
        f"{format_price_value(float(area['zone_bottom']))} - "
        f"{format_price_value(float(area['zone_top']))}"
    )


def format_date_label(value: Any) -> str:
    """Format one raw date-like value into Indonesian short-date style."""
    return format_short_date_label(value)

def describe_support_resistance_area(
    level: dict[str, Any] | None,
    fallback: str,
) -> str:
    """Return a natural-language description for one support/resistance level."""
    if level is None:
        return fallback
    return f"area {format_support_resistance_zone(level)}"


def build_indicator_note_level_box_html(
    label: str,
    level: dict[str, Any] | None,
    color: str,
    current_price: float,
    empty_message: str,
    detail_lines: list[str] | None = None,
) -> str:
    """Build one styled HTML box for the indicator explanation card."""
    escaped_label = html.escape(label)
    escaped_color = html.escape(color)

    if level is None:
        return (
            f'<div class="indicator-note-box indicator-note-box-empty" '
            f'style="--indicator-note-accent: {escaped_color};">'
            f'<div class="indicator-note-box-label">{escaped_label}</div>'
            f'<div class="indicator-note-box-empty-text">{html.escape(empty_message)}</div>'
            "</div>"
        )

    detail_lines = detail_lines or []
    zone_text = format_support_resistance_zone(level)
    midpoint_text = format_price_value(float(level["price"]))
    distance_text = format_price_distance_percentage(current_price, float(level["price"]))
    meta_html = "".join(
        f'<div class="indicator-note-box-meta">{html.escape(line)}</div>' for line in detail_lines
    )
    return (
        f'<div class="indicator-note-box" style="--indicator-note-accent: {escaped_color};">'
        f'<div class="indicator-note-box-label">{escaped_label}</div>'
        f'<div class="indicator-note-box-value">{html.escape(zone_text)}</div>'
        f'<div class="indicator-note-box-meta">'
        f'Titik tengah {html.escape(midpoint_text)} | Jarak {html.escape(distance_text)}'
        f"</div>{meta_html}</div>"
    )


def build_indicator_note_info_box_html(
    label: str,
    value: str | None,
    color: str,
    detail_lines: list[str] | None = None,
    empty_message: str = "",
) -> str:
    """Build one generic styled HTML box for indicator explanations."""
    escaped_label = html.escape(label)
    escaped_color = html.escape(color)

    if not value:
        return (
            f'<div class="indicator-note-box indicator-note-box-empty" '
            f'style="--indicator-note-accent: {escaped_color};">'
            f'<div class="indicator-note-box-label">{escaped_label}</div>'
            f'<div class="indicator-note-box-empty-text">{html.escape(empty_message)}</div>'
            "</div>"
        )

    detail_lines = detail_lines or []
    meta_html = "".join(
        f'<div class="indicator-note-box-meta">{html.escape(line)}</div>' for line in detail_lines
    )
    return (
        f'<div class="indicator-note-box" style="--indicator-note-accent: {escaped_color};">'
        f'<div class="indicator-note-box-label">{escaped_label}</div>'
        f'<div class="indicator-note-box-value">{html.escape(value)}</div>'
        f"{meta_html}</div>"
    )


PATTERN_DIRECTION_LABELS = {
    "bullish": "Bullish",
    "bearish": "Bearish",
    "neutral": "Netral",
}


def format_pattern_direction_label(direction: str) -> str:
    """Translate one pattern direction into Indonesian display text."""
    normalized_direction = str(direction or "").strip().lower()
    return PATTERN_DIRECTION_LABELS.get(normalized_direction, normalized_direction or "-")



def build_indicator_note_table_html(
    title: str,
    columns: list[str],
    rows: list[list[str]],
) -> str:
    """Build one compact HTML table for indicator history rows."""
    if not rows:
        return ""

    header_html = "".join(
        f'<th style="padding: 0.72rem 0.78rem; text-align: left; background: rgba(15, 23, 42, 0.92); color: #cbd5e1; font-size: 0.84rem; font-weight: 700; border-bottom: 1px solid rgba(148, 163, 184, 0.18); white-space: nowrap;">{html.escape(column)}</th>'
        for column in columns
    )

    body_rows: list[str] = []
    for row_index, row_values in enumerate(rows):
        row_background = "rgba(15, 23, 42, 0.34)" if row_index % 2 == 0 else "rgba(15, 23, 42, 0.22)"
        cell_html = "".join(
            f'<td style="padding: 0.72rem 0.78rem; color: #e2e8f0; font-size: 0.84rem; border-top: 1px solid rgba(148, 163, 184, 0.10); vertical-align: top;">{html.escape(str(cell_value))}</td>'
            for cell_value in row_values
        )
        body_rows.append(f'<tr style="background: {row_background};">{cell_html}</tr>')

    return (
        '<div style="margin-top: 1rem;">'
        f'<div class="indicator-note-section-context">{html.escape(title)}</div>'
        '<div style="overflow-x: auto; border: 1px solid rgba(148, 163, 184, 0.16); border-radius: 14px; background: rgba(15, 23, 42, 0.24);">'
        '<table style="width: 100%; border-collapse: collapse; min-width: 720px;">'
        f'<thead><tr>{header_html}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table></div></div>'
    )



def build_indicator_note_section_html(
    title: str,
    summary_text: str,
    boxes_html: list[str],
    context_text: str = "",
    extra_html: str = "",
) -> str:
    """Build one section inside the indicator explanation card."""
    context_html = (
        f'<div class="indicator-note-section-context">{html.escape(context_text)}</div>'
        if context_text
        else ""
    )
    return (
        '<div class="indicator-note-section">'
        f'<div class="indicator-note-section-title">{html.escape(title)}</div>'
        f'<div class="indicator-note-section-summary">{html.escape(summary_text)}</div>'
        f"{context_html}"
        f'<div class="indicator-note-grid">{"".join(boxes_html)}</div>'
        f"{extra_html}"
        "</div>"
    )



def _trendline_break_value(summary: dict[str, Any], major: bool = False) -> str:
    """Return one compact break-status label for trendline cards."""
    label = str(summary.get("break_display_label") or "").strip()
    if label:
        return label

    direction = str(summary.get("direction") or "down")
    latest_signal = str(summary.get("latest_signal") or "")
    has_any_break = bool(summary.get("has_any_relevant_break"))
    if direction == "up":
        if latest_signal in {"fresh_breakdown", "breakdown"}:
            return "Breakdown Valid"
        if latest_signal == "reclaimed":
            return "False Breakdown"
        if latest_signal == "retest":
            return "Baru Disentuh"
        return "Pernah Breakdown" if has_any_break else "Belum Ada Breakdown"

    if latest_signal in {"fresh_breakout", "breakout"}:
        return "Breakout Valid"
    if latest_signal == "rejected":
        return "False Breakout"
    if latest_signal == "retest":
        return "Baru Disentuh"
    return "Pernah Breakout" if has_any_break else "Belum Ada Breakout"



def _trendline_break_event_text(summary: dict[str, Any]) -> str:
    """Describe the latest break event without mixing support and resistance terms."""
    direction = str(summary.get("direction") or "down")
    break_label = _trendline_break_value(summary)
    latest_break_date = summary.get("latest_break_date")
    if latest_break_date is None:
        if direction == "up":
            return "Break terakhir: belum ada breakdown valid."
        return "Break terakhir: belum ada breakout valid."
    return f"Break terakhir: {break_label} ({format_short_date_label(latest_break_date)})"



def _build_trendline_boxes(
    trendlines: list[dict[str, Any]],
    colors: dict[str, Any],
    label_prefix: str,
    major: bool = False,
) -> list[str]:
    """Build one info box per trendline so multiple lines stay readable in Keterangan."""
    boxes: list[str] = []
    for index, summary in enumerate(trendlines):
        direction = str(summary["direction"])
        direction_label = "Naik" if direction == "up" else "Turun"
        role_label = "support" if direction == "up" else "resistance"
        trendline_color = colors.get(direction, "#22c55e" if direction == "up" else "#ef4444")
        boxes.append(
            build_indicator_note_info_box_html(
                label=f"{label_prefix} {index + 1} - {direction_label}",
                value=f"{format_price_value(float(summary['line_value']))}",
                color=trendline_color,
                detail_lines=[
                    f"Role {role_label.title()} | Disentuh {int(summary['touch_count'])} kali",
                    f"Status {_trendline_break_value(summary, major=major)}",
                    _trendline_break_event_text(summary),
                    (
                        f"Anchor {format_price_value(float(summary['start_value']))} -> "
                        f"{format_price_value(float(summary['end_pivot_value']))}"
                    ),
                    (
                        f"Jarak dari harga "
                        f"{format_price_distance_percentage(float(summary['current_price']), float(summary['line_value']))}"
                    ),
                ],
            )
        )
    return boxes


