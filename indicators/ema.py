from __future__ import annotations

import pandas as pd


def calculate_ema(close_series: pd.Series, period: int = 10) -> pd.Series:
    """Calculate one EMA series with a warmup that respects the requested period."""
    normalized_period = max(int(period), 1)
    close_values = pd.to_numeric(close_series, errors="coerce")
    return close_values.ewm(
        span=normalized_period,
        adjust=False,
        min_periods=normalized_period,
    ).mean()
