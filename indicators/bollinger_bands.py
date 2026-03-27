from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_close_source


def build_bollinger_bands_dataframe(
    data: pd.DataFrame,
    length: int,
    deviation: int | float,
) -> pd.DataFrame:
    """Prepare Bollinger Bands values from close prices."""
    indicator_frame = build_close_source(data)
    close = indicator_frame["close"]
    basis_name = f"BB Basis {length}"
    upper_name = f"BB Upper {length}"
    lower_name = f"BB Lower {length}"

    basis = close.rolling(window=length, min_periods=1).mean()
    standard_deviation = close.rolling(window=length, min_periods=1).std(ddof=0)
    indicator_frame[basis_name] = basis
    indicator_frame[upper_name] = basis + (standard_deviation * deviation)
    indicator_frame[lower_name] = basis - (standard_deviation * deviation)
    return indicator_frame[["time", upper_name, basis_name, lower_name]]
