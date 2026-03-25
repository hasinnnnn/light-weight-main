from __future__ import annotations

import pandas as pd


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate a Wilder-style RSI series from close prices."""
    close_series = pd.to_numeric(close, errors="coerce")
    delta = close_series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    average_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    relative_strength = average_gain.div(average_loss.replace(0.0, pd.NA))
    return 100 - (100 / (1 + relative_strength))
