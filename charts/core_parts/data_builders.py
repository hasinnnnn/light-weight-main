from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.parabolic_sar import calculate_parabolic_sar
from charts.core_parts.constants import VOLUME_MA_WINDOW

def _build_price_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare the main candle dataframe, including volume for the built-in volume pane."""
    price_frame = data[["time", "open", "high", "low", "close", "volume"]].copy()
    for column in ["open", "high", "low", "close", "volume"]:
        if column in price_frame:
            price_frame[column] = pd.to_numeric(price_frame[column], errors="coerce")
    price_frame = price_frame.dropna(subset=["open", "high", "low", "close"])
    price_frame["volume"] = price_frame["volume"].fillna(0.0)
    return price_frame


def _build_high_low_close_volume_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare a numeric dataframe for indicators that need HLCV data."""
    indicator_frame = data[["time", "high", "low", "close", "volume"]].copy()
    for column in ["high", "low", "close", "volume"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["high", "low", "close"])
    return indicator_frame


def _build_datetime_ohlcv_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare one datetime-aware OHLCV dataframe for higher-timeframe analysis."""
    indicator_frame = data[["time", "open", "high", "low", "close", "volume"]].copy()
    indicator_frame["time"] = pd.to_datetime(indicator_frame["time"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame["volume"] = indicator_frame["volume"].fillna(0.0)
    indicator_frame = indicator_frame.dropna(subset=["time", "open", "high", "low", "close"])
    indicator_frame = indicator_frame.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    return indicator_frame.reset_index(drop=True)


def _is_date_only_chart_data(data: pd.DataFrame) -> bool:
    """Return whether the chart uses date-only timestamps."""
    if data.empty:
        return False
    first_time_value = str(data["time"].iloc[0])
    return " " not in first_time_value


def _resample_datetime_ohlcv_frame(
    frame: pd.DataFrame,
    rule: str,
) -> pd.DataFrame:
    """Resample one datetime OHLCV frame into a higher timeframe."""
    if frame.empty:
        return frame

    resampled = (
        frame.set_index("time")
        .resample(rule)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": lambda values: values.sum(min_count=1),
            }
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return resampled


def _select_strong_sr_analysis_frame(
    frame: pd.DataFrame,
    interval_label: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """Choose the higher-timeframe source used for strong support/resistance analysis."""
    normalized_interval = str(interval_label or "").strip().casefold()

    if normalized_interval in {"5 menit", "15 menit", "1 jam"}:
        resampled_frame = _resample_datetime_ohlcv_frame(frame, "4h")
        if not resampled_frame.empty:
            return resampled_frame, "4H"
    elif normalized_interval == "4 jam":
        resampled_frame = _resample_datetime_ohlcv_frame(frame, "1D")
        if not resampled_frame.empty:
            return resampled_frame, "Daily"
    elif normalized_interval == "1 hari":
        return frame, "Daily"
    elif normalized_interval == "1 minggu":
        return frame, "Weekly"

    if frame.empty:
        return frame, "Current"

    has_intraday_timestamps = (
        frame["time"].dt.hour.ne(0)
        | frame["time"].dt.minute.ne(0)
        | frame["time"].dt.second.ne(0)
    ).any()
    if has_intraday_timestamps:
        resampled_frame = _resample_datetime_ohlcv_frame(frame, "4h")
        if not resampled_frame.empty:
            return resampled_frame, "4H"
        return frame, "Intraday"
    return frame, "Daily"


def _select_major_trend_analysis_frame(
    frame: pd.DataFrame,
    interval_label: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """Choose the higher-timeframe source used for major trendline analysis."""
    normalized_interval = str(interval_label or "").strip().casefold()

    if normalized_interval in {"5 menit", "15 menit", "1 jam", "4 jam"}:
        daily_frame = _resample_datetime_ohlcv_frame(frame, "1D")
        weekly_frame = _resample_datetime_ohlcv_frame(daily_frame, "W-FRI")
        if len(weekly_frame) >= 12:
            return weekly_frame, "Weekly"
        if not daily_frame.empty:
            return daily_frame, "Daily"
    elif normalized_interval == "1 hari":
        weekly_frame = _resample_datetime_ohlcv_frame(frame, "W-FRI")
        if len(weekly_frame) >= 12:
            return weekly_frame, "Weekly"
        return frame, "Daily"
    elif normalized_interval == "1 minggu":
        return frame, "Weekly"

    if frame.empty:
        return frame, "Current"

    has_intraday_timestamps = (
        frame["time"].dt.hour.ne(0)
        | frame["time"].dt.minute.ne(0)
        | frame["time"].dt.second.ne(0)
    ).any()
    if has_intraday_timestamps:
        daily_frame = _resample_datetime_ohlcv_frame(frame, "1D")
        weekly_frame = _resample_datetime_ohlcv_frame(daily_frame, "W-FRI")
        if len(weekly_frame) >= 12:
            return weekly_frame, "Weekly"
        if not daily_frame.empty:
            return daily_frame, "Daily"
        return frame, "Intraday"

    weekly_frame = _resample_datetime_ohlcv_frame(frame, "W-FRI")
    if len(weekly_frame) >= 12:
        return weekly_frame, "Weekly"
    return frame, "Daily"


def _build_volume_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare custom volume bars and a volume moving average line."""
    volume_frame = data[["time", "open", "close", "volume"]].copy()
    for column in ["open", "close", "volume"]:
        volume_frame[column] = pd.to_numeric(volume_frame[column], errors="coerce")
    volume_frame = volume_frame.dropna(subset=["volume"])
    volume_frame["color"] = "rgba(239, 68, 68, 0.45)"
    volume_frame.loc[
        volume_frame["close"] >= volume_frame["open"], "color"
    ] = "rgba(34, 197, 94, 0.45)"
    line_name = f"Volume MA {VOLUME_MA_WINDOW}"
    volume_frame[line_name] = volume_frame["volume"].rolling(
        window=VOLUME_MA_WINDOW,
        min_periods=1,
    ).mean()
    return volume_frame[["time", "volume", "color", line_name]]


def _build_parabolic_sar_dataframe(
    data: pd.DataFrame,
    acceleration: float = 0.02,
    max_acceleration: float = 0.2,
) -> pd.DataFrame:
    """Prepare Parabolic SAR values from high/low price action."""
    indicator_frame = calculate_parabolic_sar(
        _build_high_low_close_volume_source(data)[["time", "high", "low", "close"]].copy(),
        acceleration=acceleration,
        max_acceleration=max_acceleration,
    )
    if indicator_frame.empty:
        return indicator_frame.iloc[0:0]

    candle_range = (indicator_frame["high"] - indicator_frame["low"]).abs()
    median_candle_range = float(candle_range.dropna().median()) if not candle_range.dropna().empty else 0.0
    latest_close = float(pd.to_numeric(indicator_frame["close"], errors="coerce").iloc[-1])
    display_offset = max(median_candle_range * 0.22, abs(latest_close) * 0.0012, 0.01)

    psar_series = pd.to_numeric(indicator_frame["psar"], errors="coerce")
    position_series = indicator_frame["position"].astype("object")
    psar_series.loc[position_series.eq("above")] = (
        psar_series.loc[position_series.eq("above")] + display_offset
    )
    psar_series.loc[position_series.eq("below")] = (
        psar_series.loc[position_series.eq("below")] - display_offset
    )

    indicator_frame["Parabolic SAR"] = psar_series
    indicator_frame = indicator_frame.dropna(subset=["Parabolic SAR"])
    return indicator_frame[["time", "Parabolic SAR", "position"]]


def _split_parabolic_sar_segments(psar_frame: pd.DataFrame) -> list[pd.DataFrame]:
    """Split PSAR runs whenever the side flips so dots do not connect across reversals."""
    if psar_frame.empty:
        return []

    segmented_frame = psar_frame.copy().reset_index(drop=True)
    segmented_frame["segment"] = segmented_frame["position"].ne(
        segmented_frame["position"].shift(1)
    ).cumsum()

    segments: list[pd.DataFrame] = []
    for _, segment_frame in segmented_frame.groupby("segment", sort=True):
        if segment_frame.empty:
            continue
        segments.append(segment_frame[["time", "Parabolic SAR"]].copy())
    return segments
