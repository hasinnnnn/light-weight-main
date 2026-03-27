from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_hlcv_source


def build_vwap_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare VWAP values from price and volume data."""
    indicator_frame = build_hlcv_source(data)
    if indicator_frame.empty:
        return indicator_frame

    timestamps = pd.to_datetime(indicator_frame["time"], errors="coerce")
    typical_price = (
        indicator_frame["high"] + indicator_frame["low"] + indicator_frame["close"]
    ) / 3
    weighted_price = typical_price * indicator_frame["volume"].fillna(0)
    is_intraday = (
        timestamps.dt.hour.ne(0)
        | timestamps.dt.minute.ne(0)
        | timestamps.dt.second.ne(0)
    ).any()

    if is_intraday:
        groups = timestamps.dt.date.astype(str)
    else:
        groups = pd.Series(["all"] * len(indicator_frame), index=indicator_frame.index)

    cumulative_weighted_price = weighted_price.groupby(groups).cumsum()
    cumulative_volume = indicator_frame["volume"].fillna(0).groupby(groups).cumsum()
    indicator_frame["VWAP"] = cumulative_weighted_price.div(cumulative_volume.replace(0, pd.NA))
    indicator_frame["VWAP"] = indicator_frame["VWAP"].fillna(indicator_frame["close"])
    return indicator_frame[["time", "VWAP"]]
