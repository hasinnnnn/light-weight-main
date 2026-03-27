from __future__ import annotations

import pandas as pd

from config.chart_options import JAKARTA_TIMEZONE
from data.models import DataServiceError

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


def _normalize_datetime_index(index: pd.Index) -> pd.DatetimeIndex:
    """Convert the source index to a timezone-safe, naive UTC DatetimeIndex."""
    timestamps = pd.to_datetime(index, errors="coerce", utc=True)
    if not isinstance(timestamps, pd.DatetimeIndex):
        timestamps = pd.DatetimeIndex(timestamps)
    return timestamps.tz_convert("UTC").tz_localize(None)



def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance columns and normalize them to lowercase names."""
    normalized = frame.copy()
    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [str(column[0]).strip().lower() for column in normalized.columns]
    else:
        normalized.columns = [str(column).strip().lower() for column in normalized.columns]

    if "close" not in normalized.columns and "adj close" in normalized.columns:
        normalized["close"] = normalized["adj close"]

    missing = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing:
        raise DataServiceError(
            "The downloaded data is missing required columns: " + ", ".join(missing)
        )

    return normalized[REQUIRED_COLUMNS].copy()



def normalize_history_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw yfinance output into a clean OHLCV dataframe."""
    if frame is None or frame.empty:
        raise DataServiceError(
            "No market data was returned. Please verify the ticker and try a different period."
        )

    normalized = _normalize_columns(frame)
    normalized.index = _normalize_datetime_index(frame.index)
    normalized = normalized.loc[~normalized.index.isna()].copy()
    normalized = normalized.loc[~normalized.index.duplicated(keep="last")]
    normalized = normalized.sort_index()

    for column in REQUIRED_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized = normalized.dropna(how="all", subset=REQUIRED_COLUMNS)
    normalized = normalized.dropna(subset=["open", "high", "low", "close"])
    normalized["volume"] = normalized["volume"].fillna(0)

    if normalized.empty:
        raise DataServiceError(
            "The response was received, but it did not contain valid OHLCV rows."
        )

    return normalized



def resample_to_4h(frame: pd.DataFrame) -> pd.DataFrame:
    """Build 4-hour candles from 1-hour source data."""
    if frame.empty:
        raise DataServiceError("Cannot resample empty data into 4-hour candles.")

    try:
        resampled = frame.resample("4h").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": lambda values: values.sum(min_count=1),
            }
        )
    except Exception as exc:
        raise DataServiceError("Failed to resample 1-hour data into 4-hour candles.") from exc

    resampled = resampled.dropna(subset=["open", "high", "low", "close"])
    if resampled.empty:
        raise DataServiceError(
            "Unable to construct 4-hour candles from the available 1-hour history."
        )

    return resampled



def finalize_chart_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure the final dataframe matches lightweight-charts OHLCV expectations."""
    prepared = frame.copy()
    prepared.index.name = "time"
    prepared = prepared.reset_index()
    prepared = prepared[["time", *REQUIRED_COLUMNS]].copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    prepared = prepared.dropna(subset=["time"])
    prepared = prepared.sort_values("time")
    prepared = prepared.drop_duplicates(subset=["time"], keep="last")
    prepared = prepared.dropna(how="all", subset=REQUIRED_COLUMNS)

    if prepared.empty:
        raise DataServiceError("No chartable rows remained after dataframe normalization.")

    is_date_only = (
        prepared["time"].dt.hour.eq(0).all()
        and prepared["time"].dt.minute.eq(0).all()
        and prepared["time"].dt.second.eq(0).all()
    )
    if is_date_only:
        prepared["time"] = prepared["time"].dt.strftime("%Y-%m-%d")
    else:
        prepared["time"] = (
            prepared["time"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(JAKARTA_TIMEZONE)
            .dt.tz_localize(None)
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )

    return prepared



def extract_price_snapshot(frame: pd.DataFrame) -> tuple[float, float | None]:
    """Return the latest close and the previous close for change calculations."""
    close = pd.to_numeric(frame["close"], errors="coerce").dropna()
    if close.empty:
        raise DataServiceError("No valid close prices were available for the selected symbol.")

    current_price = float(close.iloc[-1])
    previous_close = float(close.iloc[-2]) if len(close) >= 2 else None

    if isinstance(close.index, pd.DatetimeIndex) and len(close) >= 2:
        current_day = close.index[-1].date()
        earlier_sessions = close.loc[close.index.date < current_day]
        if not earlier_sessions.empty:
            previous_close = float(earlier_sessions.iloc[-1])

    return current_price, previous_close



def daily_ohlcv_from_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Build one clean daily OHLCV dataframe from a normalized history frame."""
    if frame.empty:
        return frame

    if not isinstance(frame.index, pd.DatetimeIndex):
        daily_frame = frame.copy()
        return daily_frame.dropna(subset=["open", "high", "low", "close"])

    has_intraday_timestamps = (
        frame.index.hour.any()
        or frame.index.minute.any()
        or frame.index.second.any()
    )
    if not has_intraday_timestamps:
        return frame.dropna(subset=["open", "high", "low", "close"]).copy()

    daily_frame = frame.resample("1D").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": lambda values: values.sum(min_count=1),
        }
    )
    daily_frame = daily_frame.dropna(subset=["open", "high", "low", "close"])
    daily_frame["volume"] = daily_frame["volume"].fillna(0.0)
    return daily_frame


__all__ = [
    "REQUIRED_COLUMNS",
    "daily_ohlcv_from_history",
    "extract_price_snapshot",
    "finalize_chart_dataframe",
    "normalize_history_dataframe",
    "resample_to_4h",
]
