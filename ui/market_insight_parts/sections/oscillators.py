from __future__ import annotations

from typing import Any

from indicators.macd import build_macd_dataframe
from indicators.rsi import build_rsi_dataframe
from ui.market_insight_parts.note_builders import (
    build_indicator_note_info_box_html,
    build_indicator_note_section_html,
)


TONE_COLORS = {
    "positive": "#22c55e",
    "negative": "#ef4444",
    "neutral": "#38bdf8",
}


def _format_value(value: float) -> str:
    return f"{float(value):.2f}"


def _direction_label(current_value: float, previous_value: float | None) -> tuple[str, str]:
    if previous_value is None:
        return "belum terbaca", "neutral"
    if current_value > previous_value:
        return "naik", "positive"
    if current_value < previous_value:
        return "turun", "negative"
    return "datar", "neutral"


def _rsi_zone_label(rsi_value: float) -> tuple[str, str, str]:
    if rsi_value >= 70:
        return "Overbought", "negative", "RSI sudah masuk area jenuh beli di atas level 70."
    if rsi_value <= 30:
        return "Oversold", "positive", "RSI sudah masuk area jenuh jual di bawah level 30."
    return "Netral", "neutral", "RSI masih bergerak di area netral antara level 30 dan 70."


def _build_rsi_signal_text(current_value: float, previous_value: float | None) -> tuple[str, str, list[str]]:
    if previous_value is None:
        return (
            "Belum ada sinyal baru",
            "neutral",
            ["Minimal butuh dua titik RSI valid untuk membaca perubahan level."],
        )
    if previous_value < 30 <= current_value:
        return (
            "RSI keluar dari oversold",
            "positive",
            ["Momentum jual mulai mereda karena RSI naik lagi ke atas 30."],
        )
    if previous_value > 70 >= current_value:
        return (
            "RSI turun dari overbought",
            "negative",
            ["Momentum naik mulai mendingin karena RSI turun kembali ke bawah 70."],
        )
    if previous_value < 70 <= current_value:
        return (
            "RSI masuk overbought",
            "negative",
            ["Harga sedang sangat kuat, tapi area jenuh beli mulai terbentuk."],
        )
    if previous_value > 30 >= current_value:
        return (
            "RSI masuk oversold",
            "negative",
            ["Tekanan jual sedang dominan karena RSI turun ke bawah 30."],
        )
    return (
        "Belum ada cross level baru",
        "neutral",
        ["Belum ada perpindahan RSI yang menembus level 30 atau 70 pada candle terakhir."],
    )


def _build_rsi_exit_text(current_value: float, previous_value: float | None) -> tuple[str, str, list[str]]:
    if previous_value is None:
        return (
            "Trigger exit RSI belum terbaca",
            "neutral",
            ["Minimal butuh dua titik RSI valid untuk membaca momentum exit."],
        )
    if previous_value > 70 >= current_value:
        return (
            "Exit RSI terpicu dari overbought",
            "negative",
            ["RSI baru turun kembali ke bawah 70, momentum naik mulai melemah."],
        )
    if current_value >= 70:
        return (
            "Waspadai exit, RSI terlalu tinggi",
            "negative",
            ["RSI sudah masuk area overbought. Exit makin valid kalau berikutnya turun lagi ke bawah 70."],
        )
    return (
        "Belum ada trigger exit RSI",
        "positive",
        ["Exit RSI biasanya dikonfirmasi saat indikator gagal bertahan di area kuat lalu melemah dari overbought."],
    )


def build_rsi_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    frame = getattr(result, "data", None)
    if frame is None or getattr(frame, "empty", True):
        return None

    length = max(int(params.get("length", 14)), 1)
    line_name = f"RSI {length}"
    accent_color = colors.get("line", "#a78bfa")
    rsi_frame = build_rsi_dataframe(frame, length)
    if rsi_frame.empty:
        return build_indicator_note_section_html(
            title="RSI",
            summary_text="Data chart belum cukup untuk membaca RSI di range aktif.",
            context_text=f"RSI memakai panjang {length} dengan level acuan 30 dan 70.",
            boxes_html=[
                build_indicator_note_info_box_html(
                    label="RSI Saat Ini",
                    value=None,
                    color=accent_color,
                    empty_message=f"RSI {length} belum siap karena data masih terlalu sedikit.",
                )
            ],
        )

    latest_rsi = float(rsi_frame.iloc[-1][line_name])
    previous_rsi = float(rsi_frame.iloc[-2][line_name]) if len(rsi_frame) > 1 else None
    zone_label, zone_tone, zone_detail = _rsi_zone_label(latest_rsi)
    direction_text, direction_tone = _direction_label(latest_rsi, previous_rsi)
    signal_text, signal_tone, signal_details = _build_rsi_signal_text(latest_rsi, previous_rsi)
    exit_text, exit_tone, exit_details = _build_rsi_exit_text(latest_rsi, previous_rsi)
    distance_to_upper = max(70.0 - latest_rsi, 0.0)
    distance_to_lower = max(latest_rsi - 30.0, 0.0)

    summary_text = (
        f"RSI saat ini berada di {_format_value(latest_rsi)} dengan status {zone_label.lower()}. "
        f"Arah RSI pada candle terakhir sedang {direction_text}."
    )
    context_text = (
        f"RSI {length} dipakai untuk membaca momentum dengan batas umum oversold 30 dan "
        f"overbought 70."
    )

    boxes_html = [
        build_indicator_note_info_box_html(
            label="RSI Saat Ini",
            value=_format_value(latest_rsi),
            color=accent_color,
            detail_lines=[
                f"Status {zone_label}",
                f"Arah RSI {direction_text}",
            ],
        ),
        build_indicator_note_info_box_html(
            label="Zona Momentum",
            value=zone_label,
            color=TONE_COLORS[zone_tone],
            detail_lines=[
                zone_detail,
                f"Jarak ke 70: {_format_value(distance_to_upper)} | Jarak ke 30: {_format_value(distance_to_lower)}",
            ],
        ),
        build_indicator_note_info_box_html(
            label="Arah RSI",
            value=f"RSI sedang {direction_text}",
            color=TONE_COLORS[direction_tone],
            detail_lines=(
                [f"RSI sebelumnya {_format_value(previous_rsi)}"] if previous_rsi is not None else None
            ),
        ),
        build_indicator_note_info_box_html(
            label="Sinyal Terbaru",
            value=signal_text,
            color=TONE_COLORS[signal_tone],
            detail_lines=signal_details,
        ),
        build_indicator_note_info_box_html(
            label="Trigger exit",
            value=exit_text,
            color=TONE_COLORS[exit_tone],
            detail_lines=exit_details,
        ),
    ]
    return build_indicator_note_section_html(
        title="RSI",
        summary_text=summary_text,
        context_text=context_text,
        boxes_html=boxes_html,
    )


def _build_macd_cross_text(
    current_macd: float,
    current_signal: float,
    previous_macd: float | None,
    previous_signal: float | None,
) -> tuple[str, str, list[str]]:
    if previous_macd is not None and previous_signal is not None:
        if previous_macd <= previous_signal and current_macd > current_signal:
            return (
                "Bullish cross",
                "positive",
                ["MACD baru memotong naik signal line pada candle terakhir."],
            )
        if previous_macd >= previous_signal and current_macd < current_signal:
            return (
                "Bearish cross",
                "negative",
                ["MACD baru memotong turun signal line pada candle terakhir."],
            )
    if current_macd > current_signal:
        return (
            "MACD di atas signal",
            "positive",
            ["Momentum naik masih lebih dominan daripada signal line."],
        )
    if current_macd < current_signal:
        return (
            "MACD di bawah signal",
            "negative",
            ["Momentum masih tertahan karena MACD belum kembali di atas signal."],
        )
    return (
        "MACD menempel signal",
        "neutral",
        ["MACD dan signal line sedang sangat berdekatan."],
    )


def _build_histogram_text(current_histogram: float, previous_histogram: float | None) -> tuple[str, str, list[str]]:
    histogram_side = "positif" if current_histogram >= 0 else "negatif"
    if previous_histogram is None:
        return (
            f"Histogram {histogram_side}",
            "neutral",
            [f"Nilai histogram sekarang {_format_value(current_histogram)}."],
        )
    if current_histogram > previous_histogram:
        return (
            f"Histogram {histogram_side} menguat",
            "positive" if current_histogram >= 0 else "neutral",
            [
                f"Histogram naik dari {_format_value(previous_histogram)} ke {_format_value(current_histogram)}.",
            ],
        )
    if current_histogram < previous_histogram:
        return (
            f"Histogram {histogram_side} melemah",
            "negative" if current_histogram < 0 else "neutral",
            [
                f"Histogram turun dari {_format_value(previous_histogram)} ke {_format_value(current_histogram)}.",
            ],
        )
    return (
        f"Histogram {histogram_side} datar",
        "neutral",
        [f"Histogram bertahan di {_format_value(current_histogram)}."],
    )


def _build_macd_exit_text(
    current_macd: float,
    current_signal: float,
    previous_macd: float | None,
    previous_signal: float | None,
) -> tuple[str, str, list[str]]:
    if previous_macd is not None and previous_signal is not None:
        if previous_macd >= previous_signal and current_macd < current_signal:
            return (
                "Exit MACD terpicu bearish cross",
                "negative",
                ["MACD baru memotong turun signal line. Ini tanda exit yang paling umum dipakai di strategi MACD."],
            )
    if current_macd < 0:
        return (
            "Waspadai exit, MACD di bawah nol",
            "negative",
            ["Momentum menengah sudah bergeser ke area negatif walau cross baru belum selalu muncul."],
        )
    return (
        "Belum ada trigger exit MACD",
        "positive",
        ["Selama MACD masih di atas signal line dan belum jatuh di bawah nol, momentum naik masih relatif aman."],
    )


def build_macd_section(result: Any, params: dict[str, Any], colors: dict[str, str]) -> str | None:
    frame = getattr(result, "data", None)
    if frame is None or getattr(frame, "empty", True):
        return None

    fast_length = max(int(params.get("fast_length", 12)), 1)
    slow_length = max(int(params.get("slow_length", 26)), fast_length + 1)
    signal_length = max(int(params.get("signal_length", 9)), 1)
    macd_frame = build_macd_dataframe(frame, fast_length, slow_length, signal_length)
    if macd_frame.empty:
        return build_indicator_note_section_html(
            title="MACD",
            summary_text="Data chart belum cukup untuk membaca MACD di range aktif.",
            context_text=(
                f"MACD memakai kombinasi fast {fast_length}, slow {slow_length}, "
                f"dan signal {signal_length}."
            ),
            boxes_html=[
                build_indicator_note_info_box_html(
                    label="MACD Saat Ini",
                    value=None,
                    color=colors.get("macd", "#38bdf8"),
                    empty_message="MACD belum siap karena data masih terlalu sedikit.",
                )
            ],
        )

    latest = macd_frame.iloc[-1]
    previous = macd_frame.iloc[-2] if len(macd_frame) > 1 else None
    latest_macd = float(latest["MACD"])
    latest_signal = float(latest["Signal"])
    latest_histogram = float(latest["Histogram"])
    previous_macd = float(previous["MACD"]) if previous is not None else None
    previous_signal = float(previous["Signal"]) if previous is not None else None
    previous_histogram = float(previous["Histogram"]) if previous is not None else None
    cross_text, cross_tone, cross_details = _build_macd_cross_text(
        latest_macd,
        latest_signal,
        previous_macd,
        previous_signal,
    )
    histogram_text, histogram_tone, histogram_details = _build_histogram_text(
        latest_histogram,
        previous_histogram,
    )
    exit_text, exit_tone, exit_details = _build_macd_exit_text(
        latest_macd,
        latest_signal,
        previous_macd,
        previous_signal,
    )
    zero_line_text = "MACD di atas nol" if latest_macd >= 0 else "MACD di bawah nol"
    zero_line_tone = "positive" if latest_macd >= 0 else "negative"
    signal_gap = latest_macd - latest_signal

    summary_text = (
        f"MACD saat ini {_format_value(latest_macd)} dan signal {_format_value(latest_signal)}. "
        f"Status terbaru: {cross_text.lower()} dengan histogram {_format_value(latest_histogram)}."
    )
    context_text = (
        f"MACD memakai kombinasi fast {fast_length}, slow {slow_length}, dan signal {signal_length} "
        f"untuk membaca perubahan momentum."
    )

    boxes_html = [
        build_indicator_note_info_box_html(
            label="MACD vs Signal",
            value=cross_text,
            color=TONE_COLORS[cross_tone],
            detail_lines=[
                f"MACD {_format_value(latest_macd)} | Signal {_format_value(latest_signal)}",
                f"Selisih MACD ke signal {_format_value(signal_gap)}",
                *cross_details,
            ],
        ),
        build_indicator_note_info_box_html(
            label="Garis Nol",
            value=zero_line_text,
            color=TONE_COLORS[zero_line_tone],
            detail_lines=[
                "MACD di atas nol biasanya menandakan momentum menengah masih bullish."
                if latest_macd >= 0
                else "MACD di bawah nol biasanya menandakan momentum menengah masih bearish."
            ],
        ),
        build_indicator_note_info_box_html(
            label="Histogram",
            value=histogram_text,
            color=(
                colors.get("histogram_up", "#22c55e")
                if latest_histogram >= 0
                else colors.get("histogram_down", "#ef4444")
            ),
            detail_lines=histogram_details,
        ),
        build_indicator_note_info_box_html(
            label="Arah Momentum",
            value=(
                "Momentum naik dominan"
                if latest_macd >= latest_signal and latest_histogram >= 0
                else "Momentum turun dominan"
                if latest_macd < latest_signal and latest_histogram < 0
                else "Momentum campuran"
            ),
            color=(
                TONE_COLORS["positive"]
                if latest_macd >= latest_signal and latest_histogram >= 0
                else TONE_COLORS["negative"]
                if latest_macd < latest_signal and latest_histogram < 0
                else TONE_COLORS["neutral"]
            ),
            detail_lines=[
                "Pembacaan ini menggabungkan posisi MACD terhadap signal line dan histogram saat ini."
            ],
        ),
        build_indicator_note_info_box_html(
            label="Trigger exit",
            value=exit_text,
            color=TONE_COLORS[exit_tone],
            detail_lines=exit_details,
        ),
    ]
    return build_indicator_note_section_html(
        title="MACD",
        summary_text=summary_text,
        context_text=context_text,
        boxes_html=boxes_html,
    )


__all__ = ["build_macd_section", "build_rsi_section"]
