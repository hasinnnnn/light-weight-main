from __future__ import annotations

def build_moving_average_overlay_series_specs(
    indicator_key: str,
    params: dict[str, int],
    colors: dict[str, str],
    ema_colors: list[str],
    ma_colors: list[str],
) -> list[dict[str, object]]:
    """Build overlay line specs for EMA and MA families."""
    normalized_key = str(indicator_key or "").upper()

    if normalized_key == "EMA":
        return [
            {
                "method": "ema",
                "length": params.get("length", 10),
                "name": f"EMA {params.get('length', 10)}",
                "color": colors.get("line", ema_colors[0]),
            }
        ]
    if normalized_key == "EMA_CROSS":
        return [
            {
                "method": "ema",
                "length": params.get("fast_length", 9),
                "name": f"EMA {params.get('fast_length', 9)}",
                "color": colors.get("fast", ema_colors[0]),
            },
            {
                "method": "ema",
                "length": params.get("slow_length", 21),
                "name": f"EMA {params.get('slow_length', 21)}",
                "color": colors.get("slow", ema_colors[1]),
            },
        ]
    if normalized_key == "DOUBLE_EMA":
        return [
            {
                "method": "ema",
                "length": params.get("length_one", 20),
                "name": f"EMA {params.get('length_one', 20)}",
                "color": colors.get("line_one", ema_colors[0]),
            },
            {
                "method": "ema",
                "length": params.get("length_two", 50),
                "name": f"EMA {params.get('length_two', 50)}",
                "color": colors.get("line_two", ema_colors[1]),
            },
        ]
    if normalized_key == "TRIPLE_EMA":
        return [
            {
                "method": "ema",
                "length": params.get("length_one", 5),
                "name": f"EMA {params.get('length_one', 5)}",
                "color": colors.get("line_one", ema_colors[0]),
            },
            {
                "method": "ema",
                "length": params.get("length_two", 10),
                "name": f"EMA {params.get('length_two', 10)}",
                "color": colors.get("line_two", ema_colors[1]),
            },
            {
                "method": "ema",
                "length": params.get("length_three", 20),
                "name": f"EMA {params.get('length_three', 20)}",
                "color": colors.get("line_three", ema_colors[2]),
            },
        ]
    if normalized_key == "MA":
        return [
            {
                "method": "ma",
                "length": params.get("length", 20),
                "name": f"MA {params.get('length', 20)}",
                "color": colors.get("line", ma_colors[0]),
            }
        ]
    if normalized_key == "MA_CROSS":
        return [
            {
                "method": "ma",
                "length": params.get("fast_length", 20),
                "name": f"MA {params.get('fast_length', 20)}",
                "color": colors.get("fast", ma_colors[0]),
            },
            {
                "method": "ma",
                "length": params.get("slow_length", 50),
                "name": f"MA {params.get('slow_length', 50)}",
                "color": colors.get("slow", ma_colors[1]),
            },
        ]
    if normalized_key == "DOUBLE_MA":
        return [
            {
                "method": "ma",
                "length": params.get("length_one", 20),
                "name": f"MA {params.get('length_one', 20)}",
                "color": colors.get("line_one", ma_colors[0]),
            },
            {
                "method": "ma",
                "length": params.get("length_two", 50),
                "name": f"MA {params.get('length_two', 50)}",
                "color": colors.get("line_two", ma_colors[1]),
            },
        ]
    if normalized_key == "TRIPLE_MA":
        return [
            {
                "method": "ma",
                "length": params.get("length_one", 10),
                "name": f"MA {params.get('length_one', 10)}",
                "color": colors.get("line_one", ma_colors[0]),
            },
            {
                "method": "ma",
                "length": params.get("length_two", 20),
                "name": f"MA {params.get('length_two', 20)}",
                "color": colors.get("line_two", ma_colors[1]),
            },
            {
                "method": "ma",
                "length": params.get("length_three", 50),
                "name": f"MA {params.get('length_three', 50)}",
                "color": colors.get("line_three", ma_colors[2]),
            },
        ]
    return []

