from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_hlcv_source


def build_atr_dataframe(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Prepare ATR values from high, low, and close prices."""
    indicator_frame = build_hlcv_source(data)[["time", "high", "low", "close"]].copy()
    if indicator_frame.empty:
        return indicator_frame

    previous_close = indicator_frame["close"].shift(1)
    true_range = pd.concat(
        [
            indicator_frame["high"] - indicator_frame["low"],
            (indicator_frame["high"] - previous_close).abs(),
            (indicator_frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    line_name = f"ATR {window}"
    indicator_frame[line_name] = true_range.ewm(
        alpha=1 / window,
        adjust=False,
        min_periods=window,
    ).mean()
    indicator_frame = indicator_frame.dropna(subset=[line_name])
    return indicator_frame[["time", line_name]]
