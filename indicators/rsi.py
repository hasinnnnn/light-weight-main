from __future__ import annotations

import pandas as pd

from indicators.source_frames import build_close_source


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


def calculate_chart_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate chart-display RSI while preserving the existing UI behavior."""
    close_series = pd.to_numeric(close, errors="coerce")
    delta = close_series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    average_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    relative_strength = average_gain.div(average_loss.replace(0.0, pd.NA))
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.where(average_loss.ne(0), 100.0)
    rsi = rsi.where(~((average_gain == 0) & (average_loss == 0)), 50.0)
    return rsi


def build_rsi_dataframe(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Prepare RSI values from close prices for chart rendering."""
    indicator_frame = build_close_source(data)
    line_name = f"RSI {window}"
    indicator_frame[line_name] = calculate_chart_rsi(indicator_frame["close"], window)
    indicator_frame = indicator_frame.dropna(subset=[line_name])
    return indicator_frame[["time", line_name]]
