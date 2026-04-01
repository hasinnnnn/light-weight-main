from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.ema import calculate_ema
from indicators.sma import calculate_sma
from ui.market_insight_parts.formatters import format_price_value
from ui.market_insight_parts.note_builders import (
    build_indicator_note_info_box_html,
    build_indicator_note_section_html,
    format_price_distance_percentage,
)


TONE_COLORS = {
    "positive": "#22c55e",
    "negative": "#ef4444",
    "neutral": "#38bdf8",
}


def _moving_average_context_line(label: str, length: int) -> str:
    return (
        f"Aturan entry: Buy saat harga pullback ke {label} {length}, low menyentuh {label} {length} "
        f"dan close tetap di atas {label} {length}."
    )


def _moving_average_exit_context_line(label: str, length: int) -> str:
    return (
        f"Trigger exit: waspadai keluar saat harga breakdown di bawah {label} {length}, "
        f"terutama kalau candle close sudah tidak mampu bertahan di atas garis."
    )


def _slope_label(current_value: float, previous_value: float | None) -> tuple[str, str]:
    if previous_value is None:
        return "belum terbaca", "neutral"
    if current_value > previous_value:
        return "naik", "positive"
    if current_value < previous_value:
        return "turun", "negative"
    return "datar", "neutral"


def _build_single_moving_average_section_payload(
    result: Any,
    params: dict[str, Any],
    colors: dict[str, str],
    *,
    line_label: str,
    indicator_title: str,
    default_length: int,
    use_ema: bool,
) -> dict[str, Any] | None:
    frame = getattr(result, "data", None)
    if frame is None or getattr(frame, "empty", True):
        return None

    required_columns = {"open", "high", "low", "close"}
    if not required_columns.issubset(set(frame.columns)):
        return None

    length = max(int(params.get("length", default_length)), 1)
    close_values = pd.to_numeric(frame["close"], errors="coerce")
    source = pd.DataFrame(
        {
            "open": pd.to_numeric(frame["open"], errors="coerce"),
            "high": pd.to_numeric(frame["high"], errors="coerce"),
            "low": pd.to_numeric(frame["low"], errors="coerce"),
            "close": close_values,
        }
    )
    source["line"] = calculate_ema(close_values, length) if use_ema else calculate_sma(close_values, length)
    source = source.dropna(subset=["high", "low", "close", "line"])

    line_name = f"{line_label} {length}"
    accent_color = colors.get("line", "#38bdf8" if use_ema else "#f59e0b")
    if source.empty:
        return {
            "title": indicator_title,
            "summary_text": f"Data chart belum cukup untuk membaca posisi harga terhadap {line_name}.",
            "context_text": _moving_average_context_line(line_label, length),
            "entry_context_text": _moving_average_context_line(line_label, length),
            "exit_context_text": _moving_average_exit_context_line(line_label, length),
            "boxes": [
                {
                    "label": line_name,
                    "value": None,
                    "color": accent_color,
                    "detail_lines": [],
                    "empty_message": f"{line_name} belum siap di range chart aktif.",
                }
            ],
        }

    latest = source.iloc[-1]
    previous_line = float(source.iloc[-2]["line"]) if len(source) > 1 else None
    close_price = float(latest["close"])
    low_price = float(latest["low"])
    high_price = float(latest["high"])
    line_value = float(latest["line"])
    close_above = close_price >= line_value
    low_touches_line = low_price <= line_value <= high_price
    valid_pullback_entry = low_touches_line and close_above
    slope_text, _ = _slope_label(line_value, previous_line)
    price_position_text = f"di atas {line_name}" if close_above else f"di bawah {line_name}"
    distance_text = format_price_distance_percentage(close_price, line_value)
    bearish_breakdown = close_price < line_value

    if valid_pullback_entry:
        entry_value = f"Cocok untuk entry pullback {line_name}"
        entry_tone = "positive"
        entry_details = [
            f"Low {format_price_value(low_price)} sudah menyentuh {line_name} {format_price_value(line_value)}",
            f"Close {format_price_value(close_price)} tetap bertahan di atas {line_name}",
        ]
        trigger_value = "Bisa entry sekarang"
        trigger_tone = "positive"
        trigger_details = [
            f"Semua syarat pullback {line_name} terpenuhi di candle terakhir",
            f"Low sentuh area {line_name} dan close tetap kuat di atas garis",
        ]
    else:
        entry_value = "Belum pas buat entry"
        entry_tone = "negative"
        entry_details = []
        if not low_touches_line:
            entry_details.append(
                f"Low {format_price_value(low_price)} belum menyentuh area {line_name} {format_price_value(line_value)}"
            )
        if not close_above:
            entry_details.append(
                f"Close {format_price_value(close_price)} masih di bawah {line_name}"
            )
        if not entry_details:
            entry_details.append(f"Setup pullback {line_name} belum lengkap.")
        trigger_value = "Belum ada trigger entry"
        trigger_tone = "negative"
        trigger_details = [
            "Entry baru valid kalau low menyentuh garis dan close tetap di atasnya",
            *entry_details,
        ]

    if bearish_breakdown:
        exit_value = f"Exit sudah terpicu di bawah {line_name}"
        exit_tone = "negative"
        exit_details = [
            f"Close {format_price_value(close_price)} sudah di bawah {line_name} {format_price_value(line_value)}",
            "Pullback dianggap gagal kalau harga tidak mampu bertahan di atas garis acuan.",
        ]
    else:
        exit_value = f"Belum ada trigger exit {line_name}"
        exit_tone = "positive"
        exit_details = [
            f"Close {format_price_value(close_price)} masih bertahan di atas {line_name}",
            f"Waspadai exit kalau nanti ada candle breakdown dan close menutup di bawah {line_name}.",
        ]

    entry_context_text = _moving_average_context_line(line_label, length)
    exit_context_text = _moving_average_exit_context_line(line_label, length)
    return {
        "title": indicator_title,
        "summary_text": (
            f"Harga sekarang berada {price_position_text}. Close terakhir {format_price_value(close_price)} "
            f"sedangkan {line_name} ada di {format_price_value(line_value)}."
        ),
        "context_text": (
            f"{entry_context_text} "
            f"{exit_context_text} "
            f"Kemiringan garis sedang {slope_text} dan jarak harga ke {line_name} sekitar {distance_text}."
        ),
        "entry_context_text": entry_context_text,
        "exit_context_text": exit_context_text,
        "boxes": [
            {
                "label": "Posisi harga",
                "value": f"Harga {price_position_text}",
                "color": TONE_COLORS["positive" if close_above else "negative"],
                "detail_lines": [
                    f"Close {format_price_value(close_price)} | {line_name} {format_price_value(line_value)}",
                    f"Jarak harga {distance_text}",
                ],
            },
            {
                "label": "Status pullback",
                "value": f"Low menyentuh {line_name}" if low_touches_line else f"Low belum menyentuh {line_name}",
                "color": TONE_COLORS["positive" if low_touches_line else "negative"],
                "detail_lines": [
                    f"Low {format_price_value(low_price)} | High {format_price_value(high_price)}",
                    f"Kemiringan {line_name} {slope_text}",
                ],
            },
            {
                "label": "Kelayakan entry",
                "value": entry_value,
                "color": TONE_COLORS[entry_tone],
                "detail_lines": entry_details,
            },
            {
                "label": "Trigger entry",
                "value": trigger_value,
                "color": TONE_COLORS[trigger_tone],
                "detail_lines": trigger_details,
            },
            {
                "label": "Trigger exit",
                "value": exit_value,
                "color": TONE_COLORS[exit_tone],
                "detail_lines": exit_details,
            },
        ],
    }


def _build_single_moving_average_section(
    result: Any,
    params: dict[str, Any],
    colors: dict[str, str],
    *,
    line_label: str,
    indicator_title: str,
    default_length: int,
    use_ema: bool,
) -> str | None:
    payload = _build_single_moving_average_section_payload(
        result,
        params,
        colors,
        line_label=line_label,
        indicator_title=indicator_title,
        default_length=default_length,
        use_ema=use_ema,
    )
    if payload is None:
        return None

    boxes_html = [
        build_indicator_note_info_box_html(
            label=str(box["label"]),
            value=box.get("value"),
            color=str(box["color"]),
            detail_lines=list(box.get("detail_lines", [])),
            empty_message=str(box.get("empty_message", "")),
        )
        for box in payload["boxes"]
    ]
    return build_indicator_note_section_html(
        title=str(payload["title"]),
        summary_text=str(payload["summary_text"]),
        context_text=str(payload.get("context_text", "")),
        boxes_html=boxes_html,
    )


def build_ema_note_payload(result: Any, params: dict[str, Any], colors: dict[str, str]) -> dict[str, Any] | None:
    return _build_single_moving_average_section_payload(
        result,
        params,
        colors,
        line_label="EMA",
        indicator_title="EMA",
        default_length=10,
        use_ema=True,
    )


def build_sma_note_payload(result: Any, params: dict[str, Any], colors: dict[str, str]) -> dict[str, Any] | None:
    return _build_single_moving_average_section_payload(
        result,
        params,
        colors,
        line_label="SMA",
        indicator_title="SMA",
        default_length=20,
        use_ema=False,
    )


def build_ema_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    return _build_single_moving_average_section(
        result,
        params,
        colors,
        line_label="EMA",
        indicator_title="EMA",
        default_length=10,
        use_ema=True,
    )


def build_sma_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    return _build_single_moving_average_section(
        result,
        params,
        colors,
        line_label="SMA",
        indicator_title="SMA",
        default_length=20,
        use_ema=False,
    )


__all__ = ["build_ema_note_payload", "build_ema_section", "build_sma_note_payload", "build_sma_section"]
