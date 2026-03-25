from __future__ import annotations

import pandas as pd


def calculate_sma(values: pd.Series, period: int) -> pd.Series:
    """Calculate a simple moving average series."""
    return pd.to_numeric(values, errors="coerce").rolling(window=period, min_periods=period).mean()
