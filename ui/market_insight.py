from __future__ import annotations

import html
from typing import Any

import streamlit as st

from charts.chart_service import (
    describe_auto_trendline,
    describe_auto_trendlines,
    describe_major_trendline,
    describe_major_trendlines,
    describe_nearest_support_resistance,
    describe_strong_support_resistance,
)
from data.market_data_service import DataLoadResult
from indicators.candle_patterns import summarize_candle_patterns
from indicators.chart_patterns import summarize_chart_patterns
from indicators.consolidation_areas import summarize_consolidation_areas
from indicators.catalog import normalize_indicator_colors, normalize_indicator_params
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


def build_market_stat_html(
    label: str,
    value_text: str,
    tone_class: str,
) -> str:
    """Build one compact stat row for the market insight card."""
    return (
        '<div class="insight-stat-item">'
        f'<div class="insight-stat-label">{html.escape(label)}</div>'
        f'<div class="insight-stat-value {html.escape(tone_class)}">{html.escape(value_text)}</div>'
        "</div>"
    )


def build_market_stat_tone(
    value: float | None,
    previous_close: float | None,
    kind: str = "price",
) -> str:
    """Choose one text color class for the stat value."""
    if value is None:
        return "stat-neutral"
    if kind in {"limit", "count", "value"}:
        return "stat-soft"
    if previous_close is None or previous_close == 0:
        return "stat-neutral"
    if value > previous_close:
        return "stat-up"
    if value < previous_close:
        return "stat-down"
    return "stat-neutral"


def is_blank_market_stat(value: float | None) -> bool:
    """Return whether one market-stat value should be treated as empty."""
    return value is None or abs(float(value)) < 1e-9


def build_market_session_stats_html(result: DataLoadResult) -> str:
    """Build the compact daily market stats shown under the company name."""
    summary = result.session_summary
    uses_bei = bool(result.uses_bei_price_fractions)
    previous_close = summary.previous_close
    is_ihsg = (result.symbol or "").strip().upper() == "IHSG"

    if is_ihsg:
        ihsg_stats = [
            (
                "Open",
                summary.open_price,
                format_metric_value(summary.open_price, use_integer_price=False),
                build_market_stat_tone(summary.open_price, previous_close),
            ),
            (
                "High",
                summary.high_price,
                format_metric_value(summary.high_price, use_integer_price=False),
                build_market_stat_tone(summary.high_price, previous_close),
            ),
            (
                "Low",
                summary.low_price,
                format_metric_value(summary.low_price, use_integer_price=False),
                build_market_stat_tone(summary.low_price, previous_close),
            ),
            (
                "Prev",
                summary.previous_close,
                format_metric_value(summary.previous_close, use_integer_price=False),
                "stat-neutral",
            ),
            (
                "Vol",
                summary.volume,
                format_compact_metric(summary.volume),
                "stat-soft",
            ),
            (
                "Val",
                summary.value,
                format_compact_metric(summary.value),
                "stat-soft",
            ),
            (
                "Avg",
                summary.average_price,
                format_metric_value(summary.average_price, use_integer_price=False),
                build_market_stat_tone(summary.average_price, previous_close, kind="average"),
            ),
        ]

        visible_stats = [
            build_market_stat_html(label, value_text, tone_class)
            for label, raw_value, value_text, tone_class in ihsg_stats
            if not is_blank_market_stat(raw_value)
        ]
        if not visible_stats:
            return ""

        column_count = 3 if len(visible_stats) >= 6 else 2 if len(visible_stats) >= 4 else 1
        rows_per_column = max(1, (len(visible_stats) + column_count - 1) // column_count)
        columns_html = []
        for start_index in range(0, len(visible_stats), rows_per_column):
            column_items = visible_stats[start_index : start_index + rows_per_column]
            columns_html.append(
                f'<div class="insight-stats-column">{"".join(column_items)}</div>'
            )

        return (
            f'<div class="insight-stats-grid" style="--insight-stat-columns: {column_count};">'
            f'{"".join(columns_html)}'
            "</div>"
        )

    first_column = [
        build_market_stat_html(
            "Open",
            format_metric_value(summary.open_price, use_integer_price=uses_bei),
            build_market_stat_tone(summary.open_price, previous_close),
        ),
        build_market_stat_html(
            "High",
            format_metric_value(summary.high_price, use_integer_price=uses_bei),
            build_market_stat_tone(summary.high_price, previous_close),
        ),
        build_market_stat_html(
            "Low",
            format_metric_value(summary.low_price, use_integer_price=uses_bei),
            build_market_stat_tone(summary.low_price, previous_close),
        ),
    ]

    if uses_bei:
        second_column = [
            build_market_stat_html(
                "Prev",
                format_metric_value(summary.previous_close, use_integer_price=True),
                "stat-neutral",
            ),
            build_market_stat_html(
                "ARA",
                format_metric_value(summary.ara_price, use_integer_price=True),
                "stat-neutral",
            ),
            build_market_stat_html(
                "ARB",
                format_metric_value(summary.arb_price, use_integer_price=True),
                "stat-neutral",
            ),
        ]

        third_column = [
            build_market_stat_html(
                "Lot",
                format_compact_metric(summary.lot),
                "stat-soft",
            ),
            build_market_stat_html(
                "Val",
                format_compact_metric(summary.value),
                "stat-soft",
            ),
            build_market_stat_html(
                "Avg",
                format_metric_value(summary.average_price, use_integer_price=True),
                build_market_stat_tone(summary.average_price, previous_close, kind="average"),
            ),
        ]
    else:
        second_column = [
            build_market_stat_html(
                "Prev",
                format_metric_value(summary.previous_close, use_integer_price=False),
                "stat-neutral",
            ),
            build_market_stat_html(
                "Vol",
                format_compact_metric(summary.volume),
                "stat-soft",
            ),
            build_market_stat_html(
                "Avg",
                format_metric_value(summary.average_price, use_integer_price=False),
                build_market_stat_tone(summary.average_price, previous_close, kind="average"),
            ),
        ]

        third_column = [
            build_market_stat_html(
                "Val",
                format_compact_metric(summary.value),
                "stat-soft",
            ),
        ]

    return (
        '<div class="insight-stats-grid">'
        f'<div class="insight-stats-column">{"".join(first_column)}</div>'
        f'<div class="insight-stats-column">{"".join(second_column)}</div>'
        f'<div class="insight-stats-column">{"".join(third_column)}</div>'
        "</div>"
    )


def build_price_change_state(current_price: float, previous_close: float | None) -> tuple[str, str, str]:
    """Return direction, arrow, and formatted percentage change."""
    if previous_close is None or previous_close == 0:
        return "change-flat", "&#8212;", "0.00%"

    change_ratio = ((current_price - previous_close) / previous_close) * 100
    if change_ratio > 0:
        return "change-up", "&#9650;", f"+{change_ratio:.2f}%"
    if change_ratio < 0:
        return "change-down", "&#9660;", f"{change_ratio:.2f}%"
    return "change-flat", "&#8212;", "0.00%"


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


def render_indicator_explanation_card(indicator_configs: list[dict[str, Any]] | None = None) -> None:
    """Render a descriptive card below the main chart for active indicators that need context."""
    result = st.session_state.loaded_result
    if result is None:
        return

    section_html: list[str] = []
    active_indicators = indicator_configs if indicator_configs is not None else (st.session_state.active_indicators or [])

    for indicator in active_indicators:
        if not bool(indicator.get("visible", True)):
            continue

        indicator_key = str(indicator.get("key") or "").strip().upper()
        if indicator_key not in {
            "CANDLE_PATTERN",
            "CHART_PATTERN",
            "CONSOLIDATION_AREA",
            "TRENDLINE",
            "MAJOR_TRENDLINE",
            "NEAREST_SUPPORT_RESISTANCE",
            "STRONG_SUPPORT_RESISTANCE",
        }:
            continue

        params = normalize_indicator_params(indicator_key, indicator.get("params"))
        colors = normalize_indicator_colors(indicator_key, indicator.get("colors"))

        if indicator_key == "CANDLE_PATTERN":
            summary = summarize_candle_patterns(result.data, params)
            bullish_color = colors.get("bullish", "#22c55e")
            bearish_color = colors.get("bearish", "#ef4444")
            neutral_color = colors.get("neutral", "#f8fafc")
            latest_event = summary["events"][-1] if summary["events"] else None
            latest_bullish = summary["latest_by_direction"].get("bullish")
            latest_bearish = summary["latest_by_direction"].get("bearish")
            latest_neutral = summary["latest_by_direction"].get("neutral")
            candle_history_table_html = build_indicator_note_table_html(
                title="Daftar semua candle pattern di chart",
                columns=["Tanggal", "Kode", "Pattern", "Arah", "Keterangan"],
                rows=[
                    [
                        format_pattern_time_label(event.get("time"), result.interval_label),
                        str(event["short_label"]),
                        str(event["label"]),
                        format_pattern_direction_label(str(event["direction"])),
                        str(event["description"]),
                    ]
                    for event in reversed(summary["events"])
                ],
            )
            if latest_event is None:
                section_html.append(
                    build_indicator_note_section_html(
                        title="Candle Pattern",
                        summary_text="Belum ada pola candle yang cocok di range chart aktif.",
                        context_text=f"Lookback {int(params['lookback'])} candle. Centang pola tertentu di editor untuk menyembunyikan label yang tidak ingin kamu lihat.",
                        boxes_html=[
                            build_indicator_note_info_box_html(
                                label="Pattern Terbaru",
                                value=None,
                                color=neutral_color,
                                empty_message="Belum ada pattern candle yang cocok di range ini.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Bullish Terbaru",
                                value=None,
                                color=bullish_color,
                                empty_message="Belum ada pattern bullish.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Bearish Terbaru",
                                value=None,
                                color=bearish_color,
                                empty_message="Belum ada pattern bearish.",
                            ),
                        ],
                    )
                )
                continue

            section_html.append(
                build_indicator_note_section_html(
                    title="Candle Pattern",
                    summary_text=(
                        f"Pattern candle terbaru adalah {latest_event['label']} pada {latest_event['date_label']}. "
                        f"Total pola yang terdeteksi di range ini: {int(summary['total_events'])}."
                    ),
                    context_text=f"Lookback {int(params['lookback'])} candle. Label singkat seperti BE, BU, dan DJ tampil langsung di chart utama.",
                    boxes_html=[
                        build_indicator_note_info_box_html(
                            label="Pattern Terbaru",
                            value=str(latest_event["label"]),
                            color=(
                                bullish_color if latest_event["direction"] == "bullish"
                                else bearish_color if latest_event["direction"] == "bearish"
                                else neutral_color
                            ),
                            detail_lines=[
                                f"Tanggal {latest_event['date_label']}",
                                str(latest_event["description"]),
                            ],
                        ),
                        build_indicator_note_info_box_html(
                            label="Bullish Terbaru",
                            value=(str(latest_bullish["label"]) if latest_bullish else None),
                            color=bullish_color,
                            detail_lines=(
                                [
                                    f"Tanggal {latest_bullish['date_label']}",
                                    str(latest_bullish["description"]),
                                ]
                                if latest_bullish
                                else None
                            ),
                            empty_message="Belum ada pattern bullish di range ini.",
                        ),
                        build_indicator_note_info_box_html(
                            label="Bearish Terbaru",
                            value=(str(latest_bearish["label"]) if latest_bearish else None),
                            color=bearish_color,
                            detail_lines=(
                                [
                                    f"Tanggal {latest_bearish['date_label']}",
                                    str(latest_bearish["description"]),
                                ]
                                if latest_bearish
                                else None
                            ),
                            empty_message="Belum ada pattern bearish di range ini.",
                        ),
                        build_indicator_note_info_box_html(
                            label="Netral Terbaru",
                            value=(str(latest_neutral["label"]) if latest_neutral else None),
                            color=neutral_color,
                            detail_lines=(
                                [
                                    f"Tanggal {latest_neutral['date_label']}",
                                    str(latest_neutral["description"]),
                                ]
                                if latest_neutral
                                else None
                            ),
                            empty_message="Belum ada pattern netral di range ini.",
                        ),
                    ],
                    extra_html=candle_history_table_html,
                )
            )
            continue

        if indicator_key == "CHART_PATTERN":
            summary = summarize_chart_patterns(result.data, params)
            bullish_color = colors.get("bullish", "#22c55e")
            bearish_color = colors.get("bearish", "#ef4444")
            neutral_color = colors.get("neutral", "#38bdf8")
            latest_pattern = summary["patterns"][-1] if summary["patterns"] else None
            latest_bullish = summary["latest_by_direction"].get("bullish")
            latest_bearish = summary["latest_by_direction"].get("bearish")
            latest_neutral = summary["latest_by_direction"].get("neutral")
            chart_history_table_html = build_indicator_note_table_html(
                title="Daftar semua chart pattern di chart",
                columns=["Tanggal", "Kode", "Pattern", "Arah", "Keterangan"],
                rows=[
                    [
                        format_pattern_time_label(pattern.get("time") or pattern.get("end_time"), result.interval_label),
                        str(pattern["short_label"]),
                        str(pattern["label"]),
                        format_pattern_direction_label(str(pattern["direction"])),
                        " | ".join([str(pattern["description"]), *[str(line) for line in pattern.get("detail_lines") or []]]),
                    ]
                    for pattern in reversed(summary["patterns"])
                ],
            )
            if latest_pattern is None:
                section_html.append(
                    build_indicator_note_section_html(
                        title="Chart Pattern",
                        summary_text="Belum ada chart pattern besar yang cocok di range chart aktif.",
                        context_text=(
                            f"Lookback {int(params['lookback'])} candle, pivot {int(params['pivot_window'])}, "
                            f"toleransi harga {int(params['tolerance_pct'])}%."
                        ),
                        boxes_html=[
                            build_indicator_note_info_box_html(
                                label="Pattern Terbaru",
                                value=None,
                                color=neutral_color,
                                empty_message="Belum ada chart pattern yang cocok di range ini.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Bullish Terbaru",
                                value=None,
                                color=bullish_color,
                                empty_message="Belum ada chart pattern bullish.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Bearish Terbaru",
                                value=None,
                                color=bearish_color,
                                empty_message="Belum ada chart pattern bearish.",
                            ),
                        ],
                    )
                )
                continue

            section_html.append(
                build_indicator_note_section_html(
                    title="Chart Pattern",
                    summary_text=(
                        f"Chart pattern terbaru adalah {latest_pattern['label']} pada {latest_pattern['date_label']}. "
                        f"Total pola yang terbaca: {int(summary['total_patterns'])}."
                    ),
                    context_text=(
                        f"Lookback {int(params['lookback'])} candle, pivot {int(params['pivot_window'])}, "
                        f"toleransi harga {int(params['tolerance_pct'])}%. Label singkat tampil di chart utama dan garis pola digambar otomatis."
                    ),
                    boxes_html=[
                        build_indicator_note_info_box_html(
                            label="Pattern Terbaru",
                            value=str(latest_pattern["label"]),
                            color=(
                                bullish_color if latest_pattern["direction"] == "bullish"
                                else bearish_color if latest_pattern["direction"] == "bearish"
                                else neutral_color
                            ),
                            detail_lines=[
                                f"Tanggal {latest_pattern['date_label']}",
                                str(latest_pattern["description"]),
                                *[str(line) for line in latest_pattern.get("detail_lines") or []][:2],
                            ],
                        ),
                        build_indicator_note_info_box_html(
                            label="Bullish Terbaru",
                            value=(str(latest_bullish["label"]) if latest_bullish else None),
                            color=bullish_color,
                            detail_lines=(
                                [
                                    f"Tanggal {latest_bullish['date_label']}",
                                    str(latest_bullish["description"]),
                                    *[str(line) for line in latest_bullish.get("detail_lines") or []][:2],
                                ]
                                if latest_bullish
                                else None
                            ),
                            empty_message="Belum ada chart pattern bullish di range ini.",
                        ),
                        build_indicator_note_info_box_html(
                            label="Bearish Terbaru",
                            value=(str(latest_bearish["label"]) if latest_bearish else None),
                            color=bearish_color,
                            detail_lines=(
                                [
                                    f"Tanggal {latest_bearish['date_label']}",
                                    str(latest_bearish["description"]),
                                    *[str(line) for line in latest_bearish.get("detail_lines") or []][:2],
                                ]
                                if latest_bearish
                                else None
                            ),
                            empty_message="Belum ada chart pattern bearish di range ini.",
                        ),
                        build_indicator_note_info_box_html(
                            label="Netral Terbaru",
                            value=(str(latest_neutral["label"]) if latest_neutral else None),
                            color=neutral_color,
                            detail_lines=(
                                [
                                    f"Tanggal {latest_neutral['date_label']}",
                                    str(latest_neutral["description"]),
                                    *[str(line) for line in latest_neutral.get("detail_lines") or []][:2],
                                ]
                                if latest_neutral
                                else None
                            ),
                            empty_message="Belum ada chart pattern netral di range ini.",
                        ),
                    ],
                    extra_html=chart_history_table_html,
                )
            )
            continue
        if indicator_key == "CONSOLIDATION_AREA":
            summary = summarize_consolidation_areas(result.data, params)
            zone_color = colors.get("zone", "#38bdf8")
            active_color = colors.get("active", "#22c55e")
            latest_area = summary["latest_area"]
            active_area = summary["active_area"]
            latest_breakout_area = summary["latest_breakout_area"]
            normalized_params = summary["params"]
            if latest_area is None:
                section_html.append(
                    build_indicator_note_section_html(
                        title="Area Konsolidasi",
                        summary_text="Belum ada area konsolidasi valid di range chart aktif.",
                        context_text=(
                            f"Lookback {int(normalized_params['lookback'])} candle, minimal "
                            f"{int(normalized_params['consolidation_bars'])} bar, rentang maks "
                            f"{float(normalized_params['max_consolidation_range_pct']):.2f}%, volume konsolidasi maks "
                            f"{float(normalized_params['consolidation_volume_ratio_max']):.2f}x."
                        ),
                        boxes_html=[
                            build_indicator_note_info_box_html(
                                label="Zona Terbaru",
                                value=None,
                                color=zone_color,
                                empty_message="Belum ada zona konsolidasi yang valid.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Zona Aktif",
                                value=None,
                                color=active_color,
                                empty_message="Belum ada konsolidasi aktif di range ini.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Breakout Terbaru",
                                value=None,
                                color=zone_color,
                                empty_message="Belum ada zona konsolidasi yang breakout.",
                            ),
                        ],
                    )
                )
                continue

            latest_area_details = [
                f"Tanggal {format_date_label(latest_area['start_time'])} s/d {format_date_label(latest_area['end_time'])}",
                str(latest_area["status_label"]),
            ]
            if latest_area.get("range_pct") is not None:
                latest_area_details.append(f"Lebar {float(latest_area['range_pct']):.2f}%")
            if latest_area.get("consolidation_volume_ratio") is not None:
                latest_area_details.append(
                    f"Vol konsolidasi {float(latest_area['consolidation_volume_ratio']):.2f}x"
                )

            active_area_details = None
            if active_area is not None:
                active_area_details = [
                    f"Tanggal {format_date_label(active_area['start_time'])} s/d {format_date_label(active_area['end_time'])}",
                    str(active_area["status_label"]),
                ]
                if active_area.get("range_pct") is not None:
                    active_area_details.append(f"Lebar {float(active_area['range_pct']):.2f}%")

            breakout_area_details = None
            if latest_breakout_area is not None:
                breakout_area_details = [
                    f"Zona {format_date_label(latest_breakout_area['start_time'])} s/d {format_date_label(latest_breakout_area['end_time'])}",
                    str(latest_breakout_area["status_label"]),
                ]
                if latest_breakout_area.get("breakout_time") is not None:
                    breakout_area_details.append(
                        f"Breakout {format_date_label(latest_breakout_area['breakout_time'])}"
                    )
                if latest_breakout_area.get("breakout_volume_ratio") is not None:
                    breakout_area_details.append(
                        f"Volume breakout {float(latest_breakout_area['breakout_volume_ratio']):.2f}x"
                    )

            section_html.append(
                build_indicator_note_section_html(
                    title="Area Konsolidasi",
                    summary_text=(
                        f"Terdeteksi {int(summary['total_areas'])} area konsolidasi di range chart aktif. "
                        f"Zona terbaru berada di area {format_consolidation_area(latest_area)} dan {str(latest_area['status_label']).lower()}."
                    ),
                    context_text=(
                        f"Lookback {int(normalized_params['lookback'])} candle, minimal "
                        f"{int(normalized_params['consolidation_bars'])} bar, rentang maks "
                        f"{float(normalized_params['max_consolidation_range_pct']):.2f}%, volume konsolidasi maks "
                        f"{float(normalized_params['consolidation_volume_ratio_max']):.2f}x, tampil maksimal "
                        f"{int(normalized_params['max_zones'])} zona."
                    ),
                    boxes_html=[
                        build_indicator_note_info_box_html(
                            label="Zona Terbaru",
                            value=format_consolidation_area(latest_area),
                            color=(active_color if latest_area["status"] == "active" else zone_color),
                            detail_lines=latest_area_details,
                        ),
                        build_indicator_note_info_box_html(
                            label="Zona Aktif",
                            value=(format_consolidation_area(active_area) if active_area is not None else None),
                            color=active_color,
                            detail_lines=active_area_details,
                            empty_message="Saat ini belum ada konsolidasi aktif.",
                        ),
                        build_indicator_note_info_box_html(
                            label="Breakout Terbaru",
                            value=(
                                format_consolidation_area(latest_breakout_area)
                                if latest_breakout_area is not None
                                else None
                            ),
                            color=zone_color,
                            detail_lines=breakout_area_details,
                            empty_message="Belum ada zona konsolidasi yang breakout di range ini.",
                        ),
                        build_indicator_note_info_box_html(
                            label="Jumlah Zona",
                            value=str(int(summary["total_areas"])),
                            color=zone_color,
                            detail_lines=[
                                f"Maks ditampilkan {int(normalized_params['max_zones'])} zona",
                            ],
                        ),
                    ],
                )
            )
            continue

        if indicator_key == "TRENDLINE":
            summary_bundle = describe_auto_trendlines(
                result.data,
                {
                    "key": indicator_key,
                    "params": params,
                    "colors": colors,
                    "visible": True,
                },
            )
            trendline_color = colors.get("up", "#22c55e")
            if summary_bundle is None:
                section_html.append(
                    build_indicator_note_section_html(
                        title="Trendline Kecil (Minor Trend)",
                        summary_text="Data chart belum cukup untuk membentuk trendline kecil otomatis.",
                        context_text="Coba tambah lookback atau turunkan sensitivitas pivot.",
                        boxes_html=[
                            build_indicator_note_info_box_html(
                                label="Trendline",
                                value=None,
                                color=trendline_color,
                                empty_message="Belum ada trendline otomatis yang valid.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Status Break",
                                value=None,
                                color=trendline_color,
                                empty_message="Status breakout atau breakdown belum bisa dibaca.",
                            ),
                        ],
                    )
                )
                continue

            trendlines = summary_bundle["trendlines"]
            primary = summary_bundle["primary"]
            direction_label = "naik" if str(primary["direction"]) == "up" else "turun"
            role_label = "support" if str(primary["direction"]) == "up" else "resistance"
            section_html.append(
                build_indicator_note_section_html(
                    title="Trendline Kecil (Minor Trend)",
                    summary_text=(
                        f"Terdeteksi {len(trendlines)} trendline kecil. Trendline utama adalah trendline {direction_label} "
                        f"sebagai area {role_label}. {primary['status_label']}"
                    ),
                    context_text=(
                        f"Lookback {int(summary_bundle['lookback'])} candle dengan sensitivitas pivot "
                        f"{int(summary_bundle['pivot_window'])}. Ditampilkan maksimal {int(summary_bundle['max_trendlines'])} trendline. "
                        "Break valid dihitung dari candle close yang menutup di luar trendline, bukan cuma wick menyentuh garis."
                    ),
                    boxes_html=_build_trendline_boxes(
                        trendlines=trendlines,
                        colors=colors,
                        label_prefix="Trendline",
                        major=False,
                    ),
                )
            )
            continue
        if indicator_key == "MAJOR_TRENDLINE":
            summary_bundle = describe_major_trendlines(
                result.data,
                {
                    "key": indicator_key,
                    "params": params,
                    "colors": colors,
                    "visible": True,
                },
                interval_label=result.interval_label,
            )
            major_trend_color = colors.get("up", "#22c55e")
            if summary_bundle is None:
                section_html.append(
                    build_indicator_note_section_html(
                        title="Trendline Besar (Major Trend)",
                        summary_text=(
                            "Data chart belum cukup untuk membentuk major trendline dari timeframe daily atau weekly."
                        ),
                        context_text="Coba pilih period yang lebih panjang atau gunakan interval 1 hari / 1 minggu.",
                        boxes_html=[
                            build_indicator_note_info_box_html(
                                label="Major Trendline",
                                value=None,
                                color=major_trend_color,
                                empty_message="Belum ada major trendline yang valid.",
                            ),
                            build_indicator_note_info_box_html(
                                label="Status Break",
                                value=None,
                                color=major_trend_color,
                                empty_message="Status breakout atau breakdown major trend belum bisa dibaca.",
                            ),
                        ],
                    )
                )
                continue

            trendlines = summary_bundle["trendlines"]
            primary = summary_bundle["primary"]
            direction_label = "naik" if str(primary["direction"]) == "up" else "turun"
            role_label = "support" if str(primary["direction"]) == "up" else "resistance"
            section_html.append(
                build_indicator_note_section_html(
                    title="Trendline Besar (Major Trend)",
                    summary_text=(
                        f"Terdeteksi {len(trendlines)} major trendline. Trendline utama adalah trendline {direction_label} "
                        f"sebagai area {role_label}. {primary['status_label']}"
                    ),
                    context_text=(
                        f"Analisis major trend memakai timeframe {summary_bundle['analysis_timeframe']} dengan lookback "
                        f"{int(summary_bundle['lookback'])}, sensitivitas pivot {int(summary_bundle['pivot_window'])}, "
                        f"dan maksimal {int(summary_bundle['max_trendlines'])} trendline. "
                        "Break valid dihitung dari candle close yang menutup di luar trendline, bukan cuma wick menyentuh garis."
                    ),
                    boxes_html=_build_trendline_boxes(
                        trendlines=trendlines,
                        colors=colors,
                        label_prefix="Major Trend",
                        major=True,
                    ),
                )
            )
            continue
        if indicator_key == "NEAREST_SUPPORT_RESISTANCE":
            summary = describe_nearest_support_resistance(
                result.data,
                {
                    "key": indicator_key,
                    "params": params,
                    "colors": colors,
                    "visible": True,
                },
            )
            if summary is None:
                section_html.append(
                    build_indicator_note_section_html(
                        title="Support & Resistance Terdekat",
                        summary_text=(
                            "Data chart belum cukup untuk menghitung area support dan resistance "
                            "terdekat."
                        ),
                        boxes_html=[
                            build_indicator_note_level_box_html(
                                label="Support Terdekat",
                                level=None,
                                color=colors.get("support", "#ef4444"),
                                current_price=float(result.current_price),
                                empty_message="Belum ada area support terdekat yang valid.",
                            ),
                            build_indicator_note_level_box_html(
                                label="Resistance Terdekat",
                                level=None,
                                color=colors.get("resistance", "#22c55e"),
                                current_price=float(result.current_price),
                                empty_message="Belum ada area resistance terdekat yang valid.",
                            ),
                        ],
                    )
                )
                continue

            support = summary.get("support")
            resistance = summary.get("resistance")
            support_summary = (
                f"Support terdekat berada di {describe_support_resistance_area(support, '')}"
                if support is not None
                else "Support terdekat belum ditemukan"
            )
            resistance_summary = (
                f"Resistance terdekat berada di {describe_support_resistance_area(resistance, '')}"
                if resistance is not None
                else "Resistance terdekat belum ditemukan"
            )
            section_html.append(
                build_indicator_note_section_html(
                    title="Support & Resistance Terdekat",
                    summary_text=f"{support_summary}. {resistance_summary}.",
                    context_text=(
                        f"Harga terakhir {format_price_value(float(summary['current_price']))}. "
                        "Pantulan dihitung dari pivot yang masuk ke area level."
                    ),
                    boxes_html=[
                        build_indicator_note_level_box_html(
                            label="Support Terdekat",
                            level=support,
                            color=colors.get("support", "#ef4444"),
                            current_price=float(summary["current_price"]),
                            empty_message="Belum ada area support terdekat yang valid.",
                            detail_lines=(
                                [f"Pantulan {int(support['bounces'])}"] if support is not None else None
                            ),
                        ),
                        build_indicator_note_level_box_html(
                            label="Resistance Terdekat",
                            level=resistance,
                            color=colors.get("resistance", "#22c55e"),
                            current_price=float(summary["current_price"]),
                            empty_message="Belum ada area resistance terdekat yang valid.",
                            detail_lines=(
                                [f"Pantulan {int(resistance['bounces'])}"]
                                if resistance is not None
                                else None
                            ),
                        ),
                    ],
                )
            )
            continue

        summary = describe_strong_support_resistance(
            result.data,
            {
                "key": indicator_key,
                "params": params,
                "colors": colors,
                "visible": True,
            },
            interval_label=result.interval_label,
        )
        if summary is None:
            section_html.append(
                build_indicator_note_section_html(
                    title="Support & Resistance Kuat",
                    summary_text=(
                        "Data chart belum cukup untuk menemukan area support dan resistance kuat."
                    ),
                    context_text="Coba period lebih panjang atau turunkan minimal pantulan.",
                    boxes_html=[
                        build_indicator_note_level_box_html(
                            label="Support Kuat",
                            level=None,
                            color=colors.get("support", "#ef4444"),
                            current_price=float(result.current_price),
                            empty_message="Belum ada area support kuat yang lolos kriteria.",
                        ),
                        build_indicator_note_level_box_html(
                            label="Resistance Kuat",
                            level=None,
                            color=colors.get("resistance", "#22c55e"),
                            current_price=float(result.current_price),
                            empty_message="Belum ada area resistance kuat yang lolos kriteria.",
                        ),
                    ],
                )
            )
            continue

        support = summary.get("support")
        resistance = summary.get("resistance")
        support_summary = (
            f"Support kuat berada di {describe_support_resistance_area(support, '')}"
            if support is not None
            else "Support kuat belum ditemukan"
        )
        resistance_summary = (
            f"Resistance kuat berada di {describe_support_resistance_area(resistance, '')}"
            if resistance is not None
            else "Resistance kuat belum ditemukan"
        )
        section_html.append(
            build_indicator_note_section_html(
                title="Support & Resistance Kuat",
                summary_text=f"{support_summary}. {resistance_summary}.",
                context_text=(
                    f"Analisis memakai timeframe {summary['analysis_timeframe']} "
                    f"dengan minimal {int(summary['minimum_bounces'])} pantulan."
                ),
                boxes_html=[
                    build_indicator_note_level_box_html(
                        label="Support Kuat",
                        level=support,
                        color=colors.get("support", "#ef4444"),
                        current_price=float(summary["current_price"]),
                        empty_message="Belum ada area support kuat yang lolos kriteria.",
                        detail_lines=(
                            [
                                f"Pantulan {int(support['bounces'])} | Breakout {int(support['breakout_count'])}",
                                (
                                    f"Vol reversal kuat {int(support['high_volume_reversals'])} | "
                                    f"Rata-rata {float(support['average_volume_ratio']):.2f}x"
                                ),
                            ]
                            if support is not None
                            else None
                        ),
                    ),
                    build_indicator_note_level_box_html(
                        label="Resistance Kuat",
                        level=resistance,
                        color=colors.get("resistance", "#22c55e"),
                        current_price=float(summary["current_price"]),
                        empty_message="Belum ada area resistance kuat yang lolos kriteria.",
                        detail_lines=(
                            [
                                (
                                    f"Pantulan {int(resistance['bounces'])} | "
                                    f"Breakout {int(resistance['breakout_count'])}"
                                ),
                                (
                                    f"Vol reversal kuat {int(resistance['high_volume_reversals'])} | "
                                    f"Rata-rata {float(resistance['average_volume_ratio']):.2f}x"
                                ),
                            ]
                            if resistance is not None
                            else None
                        ),
                    ),
                ],
            )
        )

    if not section_html:
        return

    st.markdown(
        (
            '<div class="indicator-note-card">'
            '<div class="indicator-note-card-title">Keterangan</div>'
            f'{"".join(section_html)}'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_market_insight_card() -> None:
    """Render the trend/risk summary card above the chart."""
    result = st.session_state.loaded_result
    if result is None:
        return

    insight = result.insight
    symbol = html.escape(result.symbol)
    company_name = (result.company_name or st.session_state.selected_company_name or "").strip()
    subtitle = html.escape(company_name) if company_name else ""
    subtitle_html = f'<div class="insight-subtitle">{subtitle}</div>' if subtitle else ""
    trend_class = "trend-up" if insight.trend_label == "Uptrend" else "trend-down"
    risk_class = "risk-low" if insight.risk_label == "Low Risk" else "risk-high"
    change_class, change_arrow, change_percent = build_price_change_state(
        current_price=result.current_price,
        previous_close=result.previous_close,
    )
    formatted_price = html.escape(format_price_value(result.current_price))
    market_stats_html = build_market_session_stats_html(result)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-header">
                <div class="insight-title">{symbol}</div>
                <div class="insight-price">{formatted_price}</div>
                <div class="insight-change {change_class}">{change_arrow} {html.escape(change_percent)}</div>
            </div>
            {subtitle_html}
            {market_stats_html}
            <div class="insight-pill-row">
                <span class="insight-pill {trend_class}">Trend: {html.escape(insight.trend_label)}</span>
                <span class="insight-pill {risk_class}">Risk: {html.escape(insight.risk_label)}</span>
            </div>
            <div class="insight-reason">
                Alasan: {html.escape(insight.reason)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



























