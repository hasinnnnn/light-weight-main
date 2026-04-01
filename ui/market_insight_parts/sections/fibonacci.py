from __future__ import annotations

from typing import Any

from charts.chart_service import describe_fibonacci_levels

from ui.market_insight_parts.formatters import format_price_value
from ui.market_insight_parts.note_builders import (
    build_indicator_note_info_box_html,
    build_indicator_note_section_html,
    format_date_label,
)


def build_fibonacci_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    summary = describe_fibonacci_levels(
        result.data,
        {
            "key": "FIBONACCI",
            "params": params,
            "colors": colors,
            "visible": True,
        },
    )
    fib_color = colors.get("line", "#60a5fa")
    if summary is None:
        return build_indicator_note_section_html(
            title="Fibonacci",
            summary_text="Data chart belum cukup untuk membaca swing Fibonacci yang valid.",
            context_text="Coba perpanjang lookback atau ganti mode swing.",
            boxes_html=[
                build_indicator_note_info_box_html(
                    label="Fibonacci",
                    value=None,
                    color=fib_color,
                    empty_message="Belum ada swing Fibonacci yang valid di range ini.",
                ),
            ],
        )

    swing_direction_label = (
        "Swing Low -> Swing High"
        if summary["swing_direction"] == "low_to_high"
        else "Swing High -> Swing Low"
    )
    swing_mode_label = {
        "aggressive": "Agresif",
        "balanced": "Seimbang",
        "major": "Mayor",
    }.get(str(summary["swing_mode"]), "Seimbang")
    current_zone_text = str(summary["current_zone_label"] or "masih dekat area swing")
    fibonacci_boxes = [
        build_indicator_note_info_box_html(
            label=str(level["title"]),
            value=format_price_value(float(level["price"])),
            color=str(level["color"]),
            detail_lines=[
                f"{(float(level['ratio']) * 100):.1f}% ({float(level['ratio']):.3f})".replace(".", ",", 1),
                f"Disentuh {int(level['touch_count'])} kali | Mantul {int(level['bounce_count'])} kali",
                str(level["description"]),
            ],
        )
        for level in summary["levels"]
    ]
    fibonacci_boxes.append(
        build_indicator_note_info_box_html(
            label="Trigger exit",
            value=(
                f"Waspadai exit dekat {summary['nearest_level_label']}"
                if summary["nearest_level_label"]
                else "Waspadai exit di resistance terdekat"
            ),
            color="#ef4444",
            detail_lines=[
                "Exit bertahap masuk akal saat harga mendekati level resistance Fibonacci berikutnya.",
                "Kalau harga gagal bertahan di atas level retracement penting, setup biasanya mulai melemah.",
            ],
        )
    )
    return build_indicator_note_section_html(
        title="Fibonacci",
        summary_text=(
            f"Fibonacci aktif memakai {swing_direction_label} dari {format_date_label(summary['swing_start_time'])} "
            f"ke {format_date_label(summary['swing_end_time'])}. Harga sekarang {current_zone_text} "
            f"dan level terdekat ada di {summary['nearest_level_label']} ({format_price_value(float(summary['nearest_level_price']))})."
        ),
        context_text=(
            f"Lookback {int(summary['lookback'])} candle, mode swing {swing_mode_label}. "
            f"Anchor swing {format_price_value(float(summary['swing_start_price']))} -> "
            f"{format_price_value(float(summary['swing_end_price']))}. {summary['bias_text']} "
            "Jumlah sentuhan dan mantulan dihitung sejak anchor swing mulai terbentuk."
        ),
        boxes_html=fibonacci_boxes,
    )


__all__ = ["build_fibonacci_section"]
