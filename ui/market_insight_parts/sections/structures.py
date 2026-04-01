from __future__ import annotations

from typing import Any

from charts.chart_service import (
    describe_auto_trendlines,
    describe_major_trendlines,
    describe_nearest_support_resistance,
    describe_strong_support_resistance,
)
from indicators.consolidation_areas import summarize_consolidation_areas

from ui.market_insight_parts.formatters import format_price_value
from ui.market_insight_parts.note_builders import (
    _build_trendline_boxes,
    build_indicator_note_info_box_html,
    build_indicator_note_level_box_html,
    build_indicator_note_section_html,
    describe_support_resistance_area,
    format_consolidation_area,
    format_date_label,
)


def build_consolidation_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    summary = summarize_consolidation_areas(result.data, params)
    zone_color = colors.get("zone", "#38bdf8")
    active_color = colors.get("active", "#22c55e")
    latest_area = summary["latest_area"]
    active_area = summary["active_area"]
    latest_breakout_area = summary["latest_breakout_area"]
    normalized_params = summary["params"]
    if latest_area is None:
        return build_indicator_note_section_html(
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=zone_color,
                    empty_message="Trigger exit konsolidasi baru terbaca setelah breakout gagal atau area bawah jebol.",
                ),
            ],
        )

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

    return build_indicator_note_section_html(
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
                value=(format_consolidation_area(latest_breakout_area) if latest_breakout_area is not None else None),
                color=zone_color,
                detail_lines=breakout_area_details,
                empty_message="Belum ada zona konsolidasi yang breakout di range ini.",
            ),
            build_indicator_note_info_box_html(
                label="Jumlah Zona",
                value=str(int(summary["total_areas"])),
                color=zone_color,
                detail_lines=[f"Maks ditampilkan {int(normalized_params['max_zones'])} zona"],
            ),
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value=(
                    "Exit saat harga balik masuk area konsolidasi"
                    if latest_breakout_area is not None
                    else "Waspadai exit kalau area bawah konsolidasi jebol"
                ),
                color=zone_color,
                detail_lines=[
                    "Breakout yang gagal dan kembali masuk box biasanya menandakan momentum melemah.",
                    "Kalau area bawah konsolidasi pecah, setup breakout biasanya dianggap invalid.",
                ],
            ),
        ],
    )


def build_trendline_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    summary_bundle = describe_auto_trendlines(
        result.data,
        {
            "key": "TRENDLINE",
            "params": params,
            "colors": colors,
            "visible": True,
        },
    )
    trendline_color = colors.get("up", "#22c55e")
    if summary_bundle is None:
        return build_indicator_note_section_html(
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=trendline_color,
                    empty_message="Trigger exit trendline muncul saat candle close breakdown dari area support trendline.",
                ),
            ],
        )

    trendlines = summary_bundle["trendlines"]
    primary = summary_bundle["primary"]
    direction_label = "naik" if str(primary["direction"]) == "up" else "turun"
    role_label = "support" if str(primary["direction"]) == "up" else "resistance"
    return build_indicator_note_section_html(
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
        boxes_html=[
            *_build_trendline_boxes(
                trendlines=trendlines,
                colors=colors,
                label_prefix="Trendline",
                major=False,
            ),
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value="Exit saat support trendline breakdown",
                color=colors.get("down", "#ef4444"),
                detail_lines=[
                    "Candle close yang menutup valid di bawah trendline support sering dipakai sebagai trigger keluar.",
                    "Kalau trendline yang dipegang berperan sebagai resistance, exit makin relevan saat harga ditolak lagi dari area itu.",
                ],
            ),
        ],
    )


def build_major_trendline_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    summary_bundle = describe_major_trendlines(
        result.data,
        {
            "key": "MAJOR_TRENDLINE",
            "params": params,
            "colors": colors,
            "visible": True,
        },
        interval_label=result.interval_label,
    )
    major_trend_color = colors.get("up", "#22c55e")
    if summary_bundle is None:
        return build_indicator_note_section_html(
            title="Trendline Besar (Major Trend)",
            summary_text="Data chart belum cukup untuk membentuk major trendline dari timeframe daily atau weekly.",
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=major_trend_color,
                    empty_message="Trigger exit major trend muncul saat harga close breakdown dari trendline utama.",
                ),
            ],
        )

    trendlines = summary_bundle["trendlines"]
    primary = summary_bundle["primary"]
    direction_label = "naik" if str(primary["direction"]) == "up" else "turun"
    role_label = "support" if str(primary["direction"]) == "up" else "resistance"
    return build_indicator_note_section_html(
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
        boxes_html=[
            *_build_trendline_boxes(
                trendlines=trendlines,
                colors=colors,
                label_prefix="Major Trend",
                major=True,
            ),
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value="Exit saat major trendline breakdown",
                color=colors.get("down", "#ef4444"),
                detail_lines=[
                    "Kalau candle close valid di bawah major trendline support, bias naik menengah biasanya ikut rusak.",
                    "Semakin besar timeframe analisisnya, sinyal exit ini biasanya makin penting.",
                ],
            ),
        ],
    )


def build_nearest_support_resistance_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    summary = describe_nearest_support_resistance(
        result.data,
        {
            "key": "NEAREST_SUPPORT_RESISTANCE",
            "params": params,
            "colors": colors,
            "visible": True,
        },
    )
    if summary is None:
        return build_indicator_note_section_html(
            title="Support & Resistance Terdekat",
            summary_text="Data chart belum cukup untuk menghitung area support dan resistance terdekat.",
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=colors.get("resistance", "#22c55e"),
                    empty_message="Trigger exit biasanya muncul saat harga mendekati resistance atau support jebol.",
                ),
            ],
        )

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
    return build_indicator_note_section_html(
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
                detail_lines=([f"Pantulan {int(support['bounces'])}"] if support is not None else None),
            ),
            build_indicator_note_level_box_html(
                label="Resistance Terdekat",
                level=resistance,
                color=colors.get("resistance", "#22c55e"),
                current_price=float(summary["current_price"]),
                empty_message="Belum ada area resistance terdekat yang valid.",
                detail_lines=([f"Pantulan {int(resistance['bounces'])}"] if resistance is not None else None),
            ),
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value=(
                    f"Pertimbangkan exit dekat resistance {format_price_value(float(resistance['price']))}"
                    if resistance is not None
                    else "Waspadai exit kalau support terdekat jebol"
                ),
                color=colors.get("resistance", "#22c55e"),
                detail_lines=[
                    "Resistance terdekat sering jadi area ambil untung pertama.",
                    "Kalau support terdekat gagal bertahan, exit defensif biasanya lebih aman.",
                ],
            ),
        ],
    )


def build_strong_support_resistance_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    summary = describe_strong_support_resistance(
        result.data,
        {
            "key": "STRONG_SUPPORT_RESISTANCE",
            "params": params,
            "colors": colors,
            "visible": True,
        },
        interval_label=result.interval_label,
    )
    if summary is None:
        return build_indicator_note_section_html(
            title="Support & Resistance Kuat",
            summary_text="Data chart belum cukup untuk menemukan area support dan resistance kuat.",
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
                build_indicator_note_info_box_html(
                    label="Trigger exit",
                    value=None,
                    color=colors.get("resistance", "#22c55e"),
                    empty_message="Trigger exit kuat biasanya muncul saat harga ditolak resistance kuat atau support kuat breakdown.",
                ),
            ],
        )

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
    return build_indicator_note_section_html(
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
            build_indicator_note_info_box_html(
                label="Trigger exit",
                value=(
                    f"Prioritaskan exit di sekitar resistance kuat {format_price_value(float(resistance['price']))}"
                    if resistance is not None
                    else "Waspadai exit kalau support kuat breakdown"
                ),
                color=colors.get("resistance", "#22c55e"),
                detail_lines=[
                    "Area resistance kuat biasanya lebih layak jadi target ambil untung dibanding resistance minor.",
                    "Kalau support kuat jebol dengan volume besar, exit defensif makin relevan.",
                ],
            ),
        ],
    )


__all__ = [
    "build_consolidation_section",
    "build_trendline_section",
    "build_major_trendline_section",
    "build_nearest_support_resistance_section",
    "build_strong_support_resistance_section",
]
