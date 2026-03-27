from __future__ import annotations

import pandas as pd


def build_close_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare a numeric close-price source dataframe."""
    indicator_frame = data[["time", "close"]].copy()
    indicator_frame["close"] = pd.to_numeric(indicator_frame["close"], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["close"])
    return indicator_frame


def build_hlcv_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare a numeric OHLCV dataframe for indicators and strategy helpers."""
    indicator_frame = data[["time", "open", "high", "low", "close", "volume"]].copy()
    for column in ["open", "high", "low", "close", "volume"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["open", "high", "low", "close"])
    return indicator_frame
