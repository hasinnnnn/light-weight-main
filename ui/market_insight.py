from __future__ import annotations

import html
from typing import Any

import streamlit as st

from charts.chart_service import (
    describe_auto_trendline,
    describe_major_trendline,
    describe_nearest_support_resistance,
    describe_strong_support_resistance,
)
from data.market_data_service import DataLoadResult
from indicators.catalog import normalize_indicator_colors, normalize_indicator_params

def format_price_value(value: float) -> str:
    """Format the latest price compactly for the insight card."""
    absolute_value = abs(value)
    if absolute_value >= 100 and abs(value - round(value)) < 1e-9:
        return f"{value:,.0f}"
    if absolute_value >= 1:
        return f"{value:,.2f}"
    return f"{value:,.4f}"


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
    cleaned_dates = [str(value).strip() for value in (event_dates or []) if str(value).strip()]
    if not cleaned_dates:
        return f"Tanggal {label}: belum ada"
    return f"Tanggal {label}: {', '.join(cleaned_dates)}"


def format_support_resistance_zone(level: dict[str, Any]) -> str:
    """Format one support/resistance zone into a compact label."""
    return (
        f"{format_price_value(float(level['zone_bottom']))} - "
        f"{format_price_value(float(level['zone_top']))}"
    )


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


def build_indicator_note_section_html(
    title: str,
    summary_text: str,
    boxes_html: list[str],
    context_text: str = "",
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
        "</div>"
    )


def render_indicator_explanation_card() -> None:
    """Render a descriptive card below the main chart for active indicators that need context."""
    result = st.session_state.loaded_result
    if result is None:
        return

    section_html: list[str] = []
    active_indicators = st.session_state.active_indicators or []

    for indicator in active_indicators:
        if not bool(indicator.get("visible", True)):
            continue

        indicator_key = str(indicator.get("key") or "").strip().upper()
        if indicator_key not in {
            "TRENDLINE",
            "MAJOR_TRENDLINE",
            "NEAREST_SUPPORT_RESISTANCE",
            "STRONG_SUPPORT_RESISTANCE",
        }:
            continue

        params = normalize_indicator_params(indicator_key, indicator.get("params"))
        colors = normalize_indicator_colors(indicator_key, indicator.get("colors"))

        if indicator_key == "TRENDLINE":
            summary = describe_auto_trendline(
                result.data,
                {
                    "key": indicator_key,
                    "params": params,
                    "colors": colors,
                    "visible": True,
                },
            )
            trendline_color = colors.get("up", "#22c55e")
            if summary is None:
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

            direction = str(summary["direction"])
            role_label = "support" if direction == "up" else "resistance"
            direction_label = "Naik" if direction == "up" else "Turun"
            trendline_color = colors.get(direction, "#22c55e" if direction == "up" else "#ef4444")
            if bool(summary.get("is_breakout_active")):
                break_value = "Breakout Aktif"
            elif bool(summary.get("is_breakdown_active")):
                break_value = "Breakdown Aktif"
            elif int(summary.get("breakout_count", 0)) > 0 or int(summary.get("breakdown_count", 0)) > 0:
                break_value = "Pernah Break"
            else:
                break_value = "Belum Ada Break"

            section_html.append(
                build_indicator_note_section_html(
                    title="Trendline Kecil (Minor Trend)",
                    summary_text=(
                        f"Trendline kecil yang aktif adalah trendline {direction_label.lower()} "
                        f"sebagai area {role_label}. {summary['status_label']}"
                    ),
                    context_text=(
                        f"Lookback {int(summary['lookback'])} candle dengan sensitivitas pivot "
                        f"{int(summary['pivot_window'])}."
                    ),
                    boxes_html=[
                        build_indicator_note_info_box_html(
                            label=f"Trendline {direction_label}",
                            value=f"{format_price_value(float(summary['line_value']))}",
                            color=trendline_color,
                            detail_lines=[
                                f"Role {role_label.title()} | Disentuh {int(summary['touch_count'])} kali",
                                (
                                    f"Anchor {format_price_value(float(summary['start_value']))} -> "
                                    f"{format_price_value(float(summary['end_pivot_value']))}"
                                ),
                                (
                                    f"Jarak dari harga "
                                    f"{format_price_distance_percentage(float(summary['current_price']), float(summary['line_value']))}"
                                ),
                            ],
                        ),
                        build_indicator_note_info_box_html(
                            label="Status Break",
                            value=break_value,
                            color=trendline_color,
                            detail_lines=[
                                f"Breakout {int(summary['breakout_count'])}x | Breakdown {int(summary['breakdown_count'])}x",
                                str(summary["status_label"]),
                                format_break_event_dates_text("breakout", summary.get("breakout_dates")),
                                format_break_event_dates_text("breakdown", summary.get("breakdown_dates")),
                            ],
                        ),
                    ],
                )
            )
            continue

        if indicator_key == "MAJOR_TRENDLINE":
            summary = describe_major_trendline(
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
            if summary is None:
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

            direction = str(summary["direction"])
            role_label = "support" if direction == "up" else "resistance"
            direction_label = "Naik" if direction == "up" else "Turun"
            major_trend_color = colors.get(direction, "#22c55e" if direction == "up" else "#ef4444")
            if bool(summary.get("is_breakout_active")):
                break_value = "Breakout Besar Aktif"
            elif bool(summary.get("is_breakdown_active")):
                break_value = "Breakdown Besar Aktif"
            elif int(summary.get("breakout_count", 0)) > 0 or int(summary.get("breakdown_count", 0)) > 0:
                break_value = "Pernah Break Besar"
            else:
                break_value = "Belum Ada Break Besar"

            section_html.append(
                build_indicator_note_section_html(
                    title="Trendline Besar (Major Trend)",
                    summary_text=(
                        f"Major trendline yang aktif adalah trendline {direction_label.lower()} "
                        f"sebagai area {role_label}. {summary['status_label']}"
                    ),
                    context_text=(
                        f"Analisis major trend memakai timeframe {summary['analysis_timeframe']} "
                        f"dengan lookback {int(summary['lookback'])} dan sensitivitas pivot {int(summary['pivot_window'])}."
                    ),
                    boxes_html=[
                        build_indicator_note_info_box_html(
                            label=f"Major Trend {direction_label}",
                            value=f"{format_price_value(float(summary['line_value']))}",
                            color=major_trend_color,
                            detail_lines=[
                                f"Role {role_label.title()} | Disentuh {int(summary['touch_count'])} kali",
                                (
                                    f"Anchor {format_price_value(float(summary['start_value']))} -> "
                                    f"{format_price_value(float(summary['end_pivot_value']))}"
                                ),
                                (
                                    f"Jarak dari harga "
                                    f"{format_price_distance_percentage(float(summary['current_price']), float(summary['line_value']))}"
                                ),
                            ],
                        ),
                        build_indicator_note_info_box_html(
                            label="Status Break",
                            value=break_value,
                            color=major_trend_color,
                            detail_lines=[
                                f"Breakout {int(summary['breakout_count'])}x | Breakdown {int(summary['breakdown_count'])}x",
                                str(summary["status_label"]),
                                format_break_event_dates_text("breakout", summary.get("breakout_dates")),
                                format_break_event_dates_text("breakdown", summary.get("breakdown_dates")),
                            ],
                        ),
                    ],
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


