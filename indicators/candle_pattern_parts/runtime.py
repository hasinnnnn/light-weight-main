from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.candle_pattern_parts.meta import CANDLE_PATTERN_DEFINITIONS, normalize_candle_pattern_params

def _prepare_source_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Build one numeric OHLC source frame for candle-pattern detection."""
    if data is None or data.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close"])

    prepared = data[["time", "open", "high", "low", "close"]].copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    for column in ["open", "high", "low", "close"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared = prepared.dropna(subset=["time", "open", "high", "low", "close"])
    prepared = prepared.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    return prepared.reset_index(drop=True)


def _trend_up(close_series: pd.Series, index: int, bars: int = 3) -> bool:
    """Check whether the recent closes were trending up."""
    start_index = max(index - bars, 0)
    return bool(close_series.iloc[index] > close_series.iloc[start_index])


def _trend_down(close_series: pd.Series, index: int, bars: int = 3) -> bool:
    """Check whether the recent closes were trending down."""
    start_index = max(index - bars, 0)
    return bool(close_series.iloc[index] < close_series.iloc[start_index])


def detect_candle_patterns(
    data: pd.DataFrame,
    raw_params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Detect common candle patterns and return UI-ready event rows."""
    params = normalize_candle_pattern_params(raw_params)
    frame = _prepare_source_frame(data)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "time",
                "pattern_key",
                "label",
                "short_label",
                "description",
                "direction",
                "position",
                "price",
            ]
        )

    if params["lookback"] > 0:
        frame = frame.tail(int(params["lookback"])).reset_index(drop=True)
    if len(frame) < 2:
        return pd.DataFrame(columns=["time", "pattern_key", "label", "short_label", "description", "direction", "position", "price"])

    open_price = frame["open"]
    high_price = frame["high"]
    low_price = frame["low"]
    close_price = frame["close"]
    candle_range = (high_price - low_price).replace(0, pd.NA)
    body = (close_price - open_price).abs()
    body_direction = close_price - open_price
    upper_shadow = high_price - pd.concat([open_price, close_price], axis=1).max(axis=1)
    lower_shadow = pd.concat([open_price, close_price], axis=1).min(axis=1) - low_price

    prev_open = open_price.shift(1)
    prev_close = close_price.shift(1)
    prev_body = body.shift(1)
    prev_direction = body_direction.shift(1)

    events: list[dict[str, Any]] = []

    def _append_event(index: int, pattern_key: str) -> None:
        meta = CANDLE_PATTERN_DEFINITIONS[pattern_key]
        direction = meta["direction"]
        if direction == "bullish":
            position = "below"
            marker_price = float(low_price.iloc[index])
        elif direction == "bearish":
            position = "above"
            marker_price = float(high_price.iloc[index])
        else:
            position = "above"
            marker_price = float(high_price.iloc[index])
        events.append(
            {
                "time": frame["time"].iloc[index],
                "pattern_key": pattern_key,
                "label": meta["label"],
                "short_label": meta["short_label"],
                "description": meta["description"],
                "direction": direction,
                "position": position,
                "price": marker_price,
            }
        )

    for index in range(2, len(frame)):
        prev_index = index - 1
        if params["show_bullish_engulfing"]:
            if (
                prev_direction.iloc[prev_index] < 0
                and body_direction.iloc[index] > 0
                and open_price.iloc[index] <= prev_close.iloc[prev_index]
                and close_price.iloc[index] >= prev_open.iloc[prev_index]
                and body.iloc[index] >= (prev_body.iloc[prev_index] * 0.9)
            ):
                _append_event(index, "bullish_engulfing")

        if params["show_bearish_engulfing"]:
            if (
                prev_direction.iloc[prev_index] > 0
                and body_direction.iloc[index] < 0
                and open_price.iloc[index] >= prev_close.iloc[prev_index]
                and close_price.iloc[index] <= prev_open.iloc[prev_index]
                and body.iloc[index] >= (prev_body.iloc[prev_index] * 0.9)
            ):
                _append_event(index, "bearish_engulfing")

        if params["show_doji"] and pd.notna(candle_range.iloc[index]):
            if body.iloc[index] <= (candle_range.iloc[index] * 0.1):
                _append_event(index, "doji")

        if params["show_hammer"] and pd.notna(candle_range.iloc[index]):
            if (
                lower_shadow.iloc[index] >= body.iloc[index] * 2.2
                and upper_shadow.iloc[index] <= max(body.iloc[index], candle_range.iloc[index] * 0.18)
                and _trend_down(close_price, prev_index)
            ):
                _append_event(index, "hammer")

        if params["show_hanging_man"] and pd.notna(candle_range.iloc[index]):
            if (
                lower_shadow.iloc[index] >= body.iloc[index] * 2.2
                and upper_shadow.iloc[index] <= max(body.iloc[index], candle_range.iloc[index] * 0.18)
                and _trend_up(close_price, prev_index)
            ):
                _append_event(index, "hanging_man")

        if params["show_shooting_star"] and pd.notna(candle_range.iloc[index]):
            if (
                upper_shadow.iloc[index] >= body.iloc[index] * 2.2
                and lower_shadow.iloc[index] <= max(body.iloc[index], candle_range.iloc[index] * 0.18)
                and _trend_up(close_price, prev_index)
            ):
                _append_event(index, "shooting_star")

        if params["show_inverted_hammer"] and pd.notna(candle_range.iloc[index]):
            if (
                upper_shadow.iloc[index] >= body.iloc[index] * 2.2
                and lower_shadow.iloc[index] <= max(body.iloc[index], candle_range.iloc[index] * 0.18)
                and _trend_down(close_price, prev_index)
            ):
                _append_event(index, "inverted_hammer")

        if params["show_bullish_harami"]:
            if (
                prev_direction.iloc[prev_index] < 0
                and body_direction.iloc[index] > 0
                and open_price.iloc[index] >= min(prev_open.iloc[prev_index], prev_close.iloc[prev_index])
                and close_price.iloc[index] <= max(prev_open.iloc[prev_index], prev_close.iloc[prev_index])
                and body.iloc[index] <= prev_body.iloc[prev_index]
            ):
                _append_event(index, "bullish_harami")

        if params["show_bearish_harami"]:
            if (
                prev_direction.iloc[prev_index] > 0
                and body_direction.iloc[index] < 0
                and open_price.iloc[index] <= max(prev_open.iloc[prev_index], prev_close.iloc[prev_index])
                and close_price.iloc[index] >= min(prev_open.iloc[prev_index], prev_close.iloc[prev_index])
                and body.iloc[index] <= prev_body.iloc[prev_index]
            ):
                _append_event(index, "bearish_harami")

        if params["show_piercing_line"]:
            midpoint = (prev_open.iloc[prev_index] + prev_close.iloc[prev_index]) / 2.0
            if (
                prev_direction.iloc[prev_index] < 0
                and body_direction.iloc[index] > 0
                and open_price.iloc[index] < prev_close.iloc[prev_index]
                and close_price.iloc[index] > midpoint
                and close_price.iloc[index] < prev_open.iloc[prev_index]
            ):
                _append_event(index, "piercing_line")

        if params["show_dark_cloud_cover"]:
            midpoint = (prev_open.iloc[prev_index] + prev_close.iloc[prev_index]) / 2.0
            if (
                prev_direction.iloc[prev_index] > 0
                and body_direction.iloc[index] < 0
                and open_price.iloc[index] > prev_close.iloc[prev_index]
                and close_price.iloc[index] < midpoint
                and close_price.iloc[index] > prev_open.iloc[prev_index]
            ):
                _append_event(index, "dark_cloud_cover")

        if params["show_morning_star"] and index >= 2:
            first_index = index - 2
            second_index = index - 1
            if (
                body_direction.iloc[first_index] < 0
                and body.iloc[second_index] <= prev_body.iloc[second_index] * 0.6
                and body_direction.iloc[index] > 0
                and close_price.iloc[index] > ((open_price.iloc[first_index] + close_price.iloc[first_index]) / 2.0)
                and _trend_down(close_price, second_index)
            ):
                _append_event(index, "morning_star")

        if params["show_evening_star"] and index >= 2:
            first_index = index - 2
            second_index = index - 1
            if (
                body_direction.iloc[first_index] > 0
                and body.iloc[second_index] <= prev_body.iloc[second_index] * 0.6
                and body_direction.iloc[index] < 0
                and close_price.iloc[index] < ((open_price.iloc[first_index] + close_price.iloc[first_index]) / 2.0)
                and _trend_up(close_price, second_index)
            ):
                _append_event(index, "evening_star")

        if params["show_bullish_marubozu"] and pd.notna(candle_range.iloc[index]):
            if body_direction.iloc[index] > 0 and body.iloc[index] >= (candle_range.iloc[index] * 0.82):
                _append_event(index, "bullish_marubozu")

        if params["show_bearish_marubozu"] and pd.notna(candle_range.iloc[index]):
            if body_direction.iloc[index] < 0 and body.iloc[index] >= (candle_range.iloc[index] * 0.82):
                _append_event(index, "bearish_marubozu")

    if not events:
        return pd.DataFrame(columns=["time", "pattern_key", "label", "short_label", "description", "direction", "position", "price"])

    return pd.DataFrame(events).sort_values("time").reset_index(drop=True)

