from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_close_source


def build_price_oscillator_dataframe(
    data: pd.DataFrame,
    fast_window: int,
    slow_window: int,
) -> pd.DataFrame:
    """Prepare Price Oscillator values from two EMA lengths."""
    indicator_frame = build_close_source(data)
    close = indicator_frame["close"]
    fast_ema = close.ewm(span=fast_window, adjust=False, min_periods=1).mean()
    slow_ema = close.ewm(span=slow_window, adjust=False, min_periods=1).mean()
    indicator_frame["Price Oscillator"] = fast_ema - slow_ema
    indicator_frame = indicator_frame.dropna(subset=["Price Oscillator"])
    return indicator_frame[["time", "Price Oscillator"]]
