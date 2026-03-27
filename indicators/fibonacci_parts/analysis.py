from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.fibonacci_parts.core import (
    _build_high_low_close_volume_source,
    build_fibonacci_level_configs,
    count_fibonacci_level_bounces,
    resolve_fibonacci_swing,
)
from indicators.fibonacci_parts.meta import (
    FIBONACCI_LEVEL_NOTES,
    FIBONACCI_MONOCHROME_DEFAULT,
    normalize_fibonacci_swing_direction,
    normalize_fibonacci_swing_mode,
)

def build_fibonacci_analysis(
    data: pd.DataFrame,
    params: dict[str, Any] | None = None,
    colors: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build one complete Fibonacci analysis payload for notes and chart rendering."""
    params = params or {}
    colors = colors or {}
    lookback = int(params.get("lookback", 120))
    swing_direction = normalize_fibonacci_swing_direction(params.get("swing_direction", "low_to_high"))
    swing_mode = normalize_fibonacci_swing_mode(params.get("swing_mode", "balanced"))
    indicator_frame = _build_high_low_close_volume_source(data).tail(lookback).reset_index(drop=True)
    if indicator_frame.empty or len(indicator_frame) < 2:
        return None

    swing = resolve_fibonacci_swing(indicator_frame, swing_direction, swing_mode)
    if swing is None:
        return None

    swing_high = float(swing["swing_high"])
    swing_low = float(swing["swing_low"])
    price_range = float(swing["price_range"])
    if price_range <= 0:
        return None

    line_override = str(colors.get("line", "")).strip().lower()
    use_monochrome = bool(line_override and line_override != FIBONACCI_MONOCHROME_DEFAULT.lower())
    level_configs = build_fibonacci_level_configs(
        swing_high=swing_high,
        swing_low=swing_low,
        price_range=price_range,
        swing_direction=swing_direction,
        line_override=line_override,
        use_monochrome=use_monochrome,
    )
    if not level_configs:
        return None

    current_price_series = pd.to_numeric(indicator_frame["close"], errors="coerce")
    if current_price_series.empty or pd.isna(current_price_series.iloc[-1]):
        return None
    current_price = float(current_price_series.iloc[-1])
    analysis_start_index = min(int(swing["start_index"]), len(indicator_frame) - 1)
    analysis_frame = indicator_frame.iloc[analysis_start_index:].reset_index(drop=True)
    tolerance = max(price_range * 0.02, abs(current_price) * 0.003, 0.01)

    level_cards: list[dict[str, Any]] = []
    for level in level_configs:
        rounded_ratio = round(float(level["ratio"]), 3)
        level_note = FIBONACCI_LEVEL_NOTES.get(rounded_ratio)
        if level_note is None:
            continue
        title, description = level_note
        touch_count, bounce_count = count_fibonacci_level_bounces(
            analysis_frame,
            float(level["price"]),
            tolerance,
            swing_direction,
        )
        level_cards.append(
            {
                "ratio": float(level["ratio"]),
                "price": float(level["price"]),
                "color": str(level["color"]),
                "label": str(level["label"]),
                "title": title,
                "description": description,
                "touch_count": touch_count,
                "bounce_count": bounce_count,
            }
        )

    ordered_levels = sorted(level_configs, key=lambda item: float(item["price"]), reverse=True)
    current_zone_label = ""
    if current_price > float(ordered_levels[0]["price"]):
        current_zone_label = f"di atas level {ordered_levels[0]['label']}"
    elif current_price < float(ordered_levels[-1]["price"]):
        current_zone_label = f"di bawah level {ordered_levels[-1]['label']}"
    else:
        for upper_level, lower_level in zip(ordered_levels, ordered_levels[1:]):
            upper_price = float(upper_level["price"])
            lower_price = float(lower_level["price"])
            if upper_price >= current_price >= lower_price:
                current_zone_label = f"di area {upper_level['label']} - {lower_level['label']}"
                break

    nearest_level = min(level_configs, key=lambda item: abs(float(item["price"]) - current_price))
    level_lookup = {round(float(level["ratio"]), 3): float(level["price"]) for level in level_configs}
    shallow_level = level_lookup.get(0.382, swing_high)
    medium_level = level_lookup.get(0.618, (swing_high + swing_low) / 2)
    if swing_direction == "low_to_high":
        if current_price >= shallow_level:
            bias_text = "Retracement masih relatif dangkal dan tren utama belum banyak terkoreksi."
        elif current_price >= medium_level:
            bias_text = "Harga masuk area retracement menengah yang sering dipakai untuk uji support."
        else:
            bias_text = "Harga sudah masuk retracement dalam, jadi area support akhir makin penting."
    else:
        if current_price <= shallow_level:
            bias_text = "Pullback balik masih dangkal sehingga resistance atas belum terlalu tertekan."
        elif current_price <= medium_level:
            bias_text = "Harga masuk area pullback menengah dan resistance Fibonacci mulai penting diperhatikan."
        else:
            bias_text = "Pullback balik sudah dalam, jadi area resistance atas makin krusial."

    return {
        "lookback": lookback,
        "swing_direction": swing_direction,
        "swing_mode": swing_mode,
        "current_price": current_price,
        "current_zone_label": current_zone_label,
        "nearest_level_label": str(nearest_level["label"]),
        "nearest_level_price": float(nearest_level["price"]),
        "bias_text": bias_text.strip(),
        "swing_start_time": swing["start_time"],
        "swing_end_time": swing["end_time"],
        "swing_start_price": float(swing["start_price"]),
        "swing_end_price": float(swing["end_price"]),
        "swing_high": swing_high,
        "swing_low": swing_low,
        "line_override": line_override,
        "use_monochrome": use_monochrome,
        "render_start_time": swing["start_time"],
        "render_end_time": indicator_frame["time"].iloc[-1],
        "level_configs": level_configs,
        "levels": level_cards,
    }


