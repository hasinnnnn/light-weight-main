from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_hlcv_source


def build_standard_pivot_levels(data: pd.DataFrame) -> dict[str, float] | None:
    """Build standard pivot point levels from the previous completed candle."""
    indicator_frame = build_hlcv_source(data)
    if len(indicator_frame) < 2:
        return None

    previous_bar = indicator_frame.iloc[-2]
    high = float(previous_bar["high"])
    low = float(previous_bar["low"])
    close = float(previous_bar["close"])
    pivot_point = (high + low + close) / 3
    price_range = high - low

    return {
        "PP": pivot_point,
        "R1": (2 * pivot_point) - low,
        "R2": pivot_point + price_range,
        "R3": high + (2 * (pivot_point - low)),
        "S1": (2 * pivot_point) - high,
        "S2": pivot_point - price_range,
        "S3": low - (2 * (high - pivot_point)),
    }
