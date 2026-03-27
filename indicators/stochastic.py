from __future__ import annotations

import pandas as pd

from indicators.rsi import calculate_chart_rsi
from indicators.source_frames import build_close_source, build_hlcv_source


def build_stochastic_dataframe(
    data: pd.DataFrame,
    k_length: int,
    k_smoothing: int,
    d_length: int,
) -> pd.DataFrame:
    """Prepare Stochastic %K and %D values."""
    indicator_frame = build_hlcv_source(data)
    highest_high = indicator_frame["high"].rolling(window=k_length, min_periods=1).max()
    lowest_low = indicator_frame["low"].rolling(window=k_length, min_periods=1).min()
    denominator = (highest_high - lowest_low).replace(0, pd.NA)
    raw_k = 100 * (indicator_frame["close"] - lowest_low).div(denominator)
    smooth_k = raw_k.rolling(window=k_smoothing, min_periods=1).mean()
    d_line = smooth_k.rolling(window=d_length, min_periods=1).mean()
    indicator_frame["%K"] = smooth_k
    indicator_frame["%D"] = d_line
    indicator_frame = indicator_frame.dropna(subset=["%K", "%D"])
    return indicator_frame[["time", "%K", "%D"]]


def build_stochastic_rsi_dataframe(
    data: pd.DataFrame,
    rsi_length: int,
    stoch_length: int,
    k_smoothing: int,
    d_length: int,
) -> pd.DataFrame:
    """Prepare Stochastic RSI values."""
    indicator_frame = build_close_source(data)
    rsi = calculate_chart_rsi(indicator_frame["close"], rsi_length)
    lowest_rsi = rsi.rolling(window=stoch_length, min_periods=1).min()
    highest_rsi = rsi.rolling(window=stoch_length, min_periods=1).max()
    denominator = (highest_rsi - lowest_rsi).replace(0, pd.NA)
    raw_stoch = 100 * (rsi - lowest_rsi).div(denominator)
    smooth_k = raw_stoch.rolling(window=k_smoothing, min_periods=1).mean()
    d_line = smooth_k.rolling(window=d_length, min_periods=1).mean()
    indicator_frame["%K"] = smooth_k
    indicator_frame["%D"] = d_line
    indicator_frame = indicator_frame.dropna(subset=["%K", "%D"])
    return indicator_frame[["time", "%K", "%D"]]
