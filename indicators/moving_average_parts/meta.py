from __future__ import annotations

import pandas as pd

EMA_FAMILY_KEYS = {"EMA", "EMA_CROSS", "DOUBLE_EMA", "TRIPLE_EMA"}
MA_FAMILY_KEYS = {"MA", "MA_CROSS", "DOUBLE_MA", "TRIPLE_MA"}


def _calculate_chart_ema(close_series: pd.Series, period: int) -> pd.Series:
    """Calculate an EMA series for chart display without warmup gaps."""
    normalized_period = max(int(period), 1)
    close_values = pd.to_numeric(close_series, errors="coerce")
    return close_values.ewm(
        span=normalized_period,
        adjust=False,
        min_periods=1,
    ).mean()



def _calculate_chart_sma(close_series: pd.Series, period: int) -> pd.Series:
    """Calculate an SMA series for chart display without warmup gaps."""
    normalized_period = max(int(period), 1)
    close_values = pd.to_numeric(close_series, errors="coerce")
    return close_values.rolling(window=normalized_period, min_periods=1).mean()
