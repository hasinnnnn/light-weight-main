from __future__ import annotations

import pandas as pd


def calculate_macd(
    close: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """Calculate MACD, signal, and histogram columns."""
    close_series = pd.to_numeric(close, errors="coerce")
    fast_ema = close_series.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
    slow_ema = close_series.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(
        span=signal_period,
        adjust=False,
        min_periods=signal_period,
    ).mean()
    return pd.DataFrame(
        {
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": macd_line - signal_line,
        }
    )
