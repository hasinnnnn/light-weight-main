from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_close_source


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


def build_macd_dataframe(
    data: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    signal_window: int,
) -> pd.DataFrame:
    """Prepare MACD, signal, and histogram values for chart rendering."""
    indicator_frame = build_close_source(data)
    close = indicator_frame["close"]
    fast_ema = close.ewm(span=fast_window, adjust=False, min_periods=1).mean()
    slow_ema = close.ewm(span=slow_window, adjust=False, min_periods=1).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(
        span=signal_window,
        adjust=False,
        min_periods=1,
    ).mean()
    histogram = macd_line - signal_line

    indicator_frame["MACD"] = macd_line
    indicator_frame["Signal"] = signal_line
    indicator_frame["Histogram"] = histogram
    indicator_frame["color"] = "rgba(239, 68, 68, 0.50)"
    indicator_frame.loc[
        indicator_frame["Histogram"] >= 0, "color"
    ] = "rgba(34, 197, 94, 0.50)"
    indicator_frame = indicator_frame.dropna(subset=["MACD", "Signal", "Histogram"])
    return indicator_frame[["time", "MACD", "Signal", "Histogram", "color"]]
