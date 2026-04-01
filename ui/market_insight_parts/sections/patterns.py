from __future__ import annotations

from typing import Any

from indicators.candle_patterns import summarize_candle_patterns
from indicators.chart_patterns import summarize_chart_patterns

from ui.market_insight_parts.formatters import format_pattern_time_label
from ui.market_insight_parts.note_builders import (
    build_indicator_note_info_box_html,
    build_indicator_note_section_html,
    build_indicator_note_table_html,
    format_pattern_direction_label,
)


def build_candle_pattern_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
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
        return build_indicator_note_section_html(
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=bearish_color,
                    empty_message="Trigger exit baru bisa dibaca setelah ada pola lawan arah.",
                ),
            ],
        )

    return build_indicator_note_section_html(
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
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value=(
                    f"Waspadai exit saat muncul {latest_bearish['label']}"
                    if latest_bearish
                    else "Belum ada trigger exit candle pattern"
                ),
                color=(bearish_color if latest_bearish else neutral_color),
                detail_lines=(
                    [
                        f"Tanggal {latest_bearish['date_label']}",
                        str(latest_bearish["description"]),
                        "Pola bearish lawan arah sering dipakai sebagai sinyal ambil untung atau kurangi posisi.",
                    ]
                    if latest_bearish
                    else ["Selama belum ada pola bearish lawan arah, exit candle pattern belum terkonfirmasi."]
                ),
            ),
        ],
        extra_html=candle_history_table_html,
    )


def build_chart_pattern_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
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
        return build_indicator_note_section_html(
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=bearish_color,
                    empty_message="Trigger exit baru bisa dibaca setelah ada pola bearish atau breakout gagal.",
                ),
            ],
        )

    return build_indicator_note_section_html(
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
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value=(
                    f"Waspadai exit saat muncul {latest_bearish['label']}"
                    if latest_bearish
                    else "Belum ada trigger exit chart pattern"
                ),
                color=(bearish_color if latest_bearish else neutral_color),
                detail_lines=(
                    [
                        f"Tanggal {latest_bearish['date_label']}",
                        str(latest_bearish["description"]),
                        "Chart pattern bearish atau breakout gagal biasanya jadi sinyal keluar yang lebih kuat.",
                    ]
                    if latest_bearish
                    else ["Selama pola lawan arah belum muncul, exit chart pattern belum terkonfirmasi."]
                ),
            ),
        ],
        extra_html=chart_history_table_html,
    )


__all__ = [
    "build_candle_pattern_section",
    "build_chart_pattern_section",
]
