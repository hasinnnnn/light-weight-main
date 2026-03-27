from __future__ import annotations

from typing import Any

import pandas as pd

from indicators.fibonacci_parts.meta import (
    FIBONACCI_LEVELS,
    normalize_fibonacci_swing_direction,
    normalize_fibonacci_swing_mode,
)

def _build_high_low_close_volume_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare a numeric dataframe for Fibonacci analysis."""
    indicator_frame = data[["time", "high", "low", "close", "volume"]].copy()
    for column in ["high", "low", "close", "volume"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["high", "low", "close"])
    return indicator_frame


def _collect_pivot_points(
    frame: pd.DataFrame,
    column: str,
    window: int,
) -> list[dict[str, Any]]:
    """Collect local swing highs or lows from a recent price frame."""
    if frame.empty or len(frame) < (window * 2) + 1:
        return []

    price_series = pd.to_numeric(frame[column], errors="coerce").reset_index(drop=True)
    time_series = frame["time"].reset_index(drop=True)
    pivot_points: list[dict[str, Any]] = []

    for index in range(window, len(price_series) - window):
        current_price = price_series.iloc[index]
        if pd.isna(current_price):
            continue

        local_slice = price_series.iloc[index - window : index + window + 1]
        local_extreme = local_slice.min() if column == "low" else local_slice.max()
        if current_price != local_extreme:
            continue

        if index > 0 and price_series.iloc[index - 1] == current_price:
            continue

        pivot_points.append(
            {
                "index": index,
                "time": time_series.iloc[index],
                "price": float(current_price),
            }
        )

    return pivot_points


def _count_true_clusters(mask: pd.Series) -> int:
    """Return the number of contiguous True segments inside one boolean mask."""
    normalized_mask = mask.fillna(False).astype(bool)
    if normalized_mask.empty:
        return 0
    transition_mask = normalized_mask & ~normalized_mask.shift(1, fill_value=False)
    return int(transition_mask.sum())


def resolve_fibonacci_swing(
    frame: pd.DataFrame,
    swing_direction: str,
    swing_mode: str = "balanced",
) -> dict[str, Any] | None:
    """Resolve one Fibonacci swing pair using the selected swing mode."""
    if frame.empty or len(frame) < 2:
        return None

    normalized_direction = normalize_fibonacci_swing_direction(swing_direction)
    normalized_mode = normalize_fibonacci_swing_mode(swing_mode)
    pivot_window = min(max(len(frame) // 30, 2), 5)
    minimum_span = max(pivot_window * 2, 3)
    low_pivots = _collect_pivot_points(frame, "low", pivot_window)
    high_pivots = _collect_pivot_points(frame, "high", pivot_window)
    high_series = pd.to_numeric(frame["high"], errors="coerce")
    low_series = pd.to_numeric(frame["low"], errors="coerce")
    full_range = float(high_series.max() - low_series.min())
    if full_range <= 0:
        return None

    candidates: list[dict[str, Any]] = []
    if normalized_direction == "high_to_low":
        for high_pivot in high_pivots:
            following_lows = [pivot for pivot in low_pivots if int(pivot["index"]) > int(high_pivot["index"])]
            if not following_lows:
                continue
            for low_pivot in following_lows:
                span = int(low_pivot["index"]) - int(high_pivot["index"])
                if span < minimum_span:
                    continue
                swing_high = float(high_pivot["price"])
                swing_low = float(low_pivot["price"])
                price_range = swing_high - swing_low
                if price_range <= 0:
                    continue
                candidates.append(
                    {
                        "start_index": int(high_pivot["index"]),
                        "end_index": int(low_pivot["index"]),
                        "start_price": swing_high,
                        "end_price": swing_low,
                        "swing_high": swing_high,
                        "swing_low": swing_low,
                        "price_range": price_range,
                        "range_ratio": price_range / full_range,
                        "start_time": high_pivot["time"],
                        "end_time": low_pivot["time"],
                        "span": span,
                    }
                )
    else:
        for low_pivot in low_pivots:
            following_highs = [pivot for pivot in high_pivots if int(pivot["index"]) > int(low_pivot["index"])]
            if not following_highs:
                continue
            for high_pivot in following_highs:
                span = int(high_pivot["index"]) - int(low_pivot["index"])
                if span < minimum_span:
                    continue
                swing_low = float(low_pivot["price"])
                swing_high = float(high_pivot["price"])
                price_range = swing_high - swing_low
                if price_range <= 0:
                    continue
                candidates.append(
                    {
                        "start_index": int(low_pivot["index"]),
                        "end_index": int(high_pivot["index"]),
                        "start_price": swing_low,
                        "end_price": swing_high,
                        "swing_high": swing_high,
                        "swing_low": swing_low,
                        "price_range": price_range,
                        "range_ratio": price_range / full_range,
                        "start_time": low_pivot["time"],
                        "end_time": high_pivot["time"],
                        "span": span,
                    }
                )

    if candidates:
        latest_end_index = max(int(candidate["end_index"]) for candidate in candidates)
        frame_span = max(len(frame) - 1, 1)
        target_span = max(minimum_span, frame_span // 3)

        if normalized_mode == "aggressive":
            recent_window = max(pivot_window * 3, frame_span // 8, 4)
            selected_pool = [
                candidate
                for candidate in candidates
                if (latest_end_index - int(candidate["end_index"])) <= recent_window
            ] or candidates
            selected_pool = [
                candidate
                for candidate in selected_pool
                if float(candidate["range_ratio"]) >= 0.08
            ] or selected_pool
            return max(
                selected_pool,
                key=lambda candidate: (
                    int(candidate["end_index"]),
                    -int(candidate["span"]),
                    float(candidate["range_ratio"]),
                ),
            )

        if normalized_mode == "major":
            selected_pool = [
                candidate
                for candidate in candidates
                if float(candidate["range_ratio"]) >= 0.28
            ] or candidates
            return max(
                selected_pool,
                key=lambda candidate: (
                    float(candidate["range_ratio"]),
                    int(candidate["span"]),
                    -abs(int(candidate["end_index"]) - latest_end_index),
                ),
            )

        selected_pool = [
            candidate
            for candidate in candidates
            if float(candidate["range_ratio"]) >= 0.16
        ] or candidates
        return max(
            selected_pool,
            key=lambda candidate: (
                round(
                    (float(candidate["range_ratio"]) * 0.6)
                    + ((int(candidate["end_index"]) / frame_span) * 0.3)
                    - ((abs(int(candidate["span"]) - target_span) / frame_span) * 0.1),
                    6,
                ),
                float(candidate["range_ratio"]),
                int(candidate["end_index"]),
            ),
        )

    if normalized_direction == "high_to_low":
        high_index = int(high_series.idxmax())
        if high_index < len(frame) - 1:
            low_index = int(low_series.iloc[high_index + 1 :].idxmin())
            swing_high = float(high_series.iloc[high_index])
            swing_low = float(low_series.iloc[low_index])
            if swing_high > swing_low:
                return {
                    "start_index": high_index,
                    "end_index": low_index,
                    "start_price": swing_high,
                    "end_price": swing_low,
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "price_range": swing_high - swing_low,
                    "range_ratio": (swing_high - swing_low) / full_range,
                    "start_time": frame["time"].iloc[high_index],
                    "end_time": frame["time"].iloc[low_index],
                    "span": low_index - high_index,
                }
    else:
        low_index = int(low_series.idxmin())
        if low_index < len(frame) - 1:
            high_index = int(high_series.iloc[low_index + 1 :].idxmax())
            swing_low = float(low_series.iloc[low_index])
            swing_high = float(high_series.iloc[high_index])
            if swing_high > swing_low:
                return {
                    "start_index": low_index,
                    "end_index": high_index,
                    "start_price": swing_low,
                    "end_price": swing_high,
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "price_range": swing_high - swing_low,
                    "range_ratio": (swing_high - swing_low) / full_range,
                    "start_time": frame["time"].iloc[low_index],
                    "end_time": frame["time"].iloc[high_index],
                    "span": high_index - low_index,
                }
    return None


def build_fibonacci_level_configs(
    swing_high: float,
    swing_low: float,
    price_range: float,
    swing_direction: str,
    line_override: str = "",
    use_monochrome: bool = False,
) -> list[dict[str, Any]]:
    """Build Fibonacci levels with orientation that matches the selected swing direction."""
    normalized_direction = normalize_fibonacci_swing_direction(swing_direction)
    level_configs: list[dict[str, Any]] = []
    for ratio, default_color in FIBONACCI_LEVELS:
        level_color = line_override if use_monochrome else default_color
        if normalized_direction == "high_to_low":
            level_price = swing_low + (price_range * ratio)
            boundary_label = "Low" if ratio == 0.0 else "High" if ratio == 1.0 else ""
        else:
            level_price = swing_high - (price_range * ratio)
            boundary_label = "High" if ratio == 0.0 else "Low" if ratio == 1.0 else ""
        label = f"{ratio * 100:.2f}%"
        if boundary_label:
            label = f"{label} {boundary_label}"
        level_configs.append(
            {
                "ratio": ratio,
                "price": level_price,
                "color": level_color,
                "label": label,
            }
        )
    return level_configs


def count_fibonacci_level_bounces(
    frame: pd.DataFrame,
    level_price: float,
    tolerance: float,
    swing_direction: str,
) -> tuple[int, int]:
    """Count how often one Fibonacci level is touched and followed by a bounce."""
    if frame.empty:
        return 0, 0

    high_series = pd.to_numeric(frame["high"], errors="coerce").reset_index(drop=True)
    low_series = pd.to_numeric(frame["low"], errors="coerce").reset_index(drop=True)
    touch_mask = high_series.ge(level_price - tolerance) & low_series.le(level_price + tolerance)
    normalized_touch = touch_mask.fillna(False).astype(bool).reset_index(drop=True)
    touch_count = _count_true_clusters(normalized_touch)
    if touch_count == 0:
        return 0, 0

    bounce_count = 0
    index = 0
    normalized_direction = normalize_fibonacci_swing_direction(swing_direction)
    while index < len(normalized_touch):
        if not bool(normalized_touch.iloc[index]):
            index += 1
            continue

        cluster_end = index
        while cluster_end + 1 < len(normalized_touch) and bool(normalized_touch.iloc[cluster_end + 1]):
            cluster_end += 1

        future_frame = frame.iloc[cluster_end + 1 : cluster_end + 4]
        if not future_frame.empty:
            future_high = pd.to_numeric(future_frame["high"], errors="coerce")
            future_low = pd.to_numeric(future_frame["low"], errors="coerce")
            future_close = pd.to_numeric(future_frame["close"], errors="coerce")
            if normalized_direction == "low_to_high":
                upside_move = max(
                    float(future_high.max()) if future_high.notna().any() else level_price,
                    float(future_close.max()) if future_close.notna().any() else level_price,
                )
                if upside_move >= level_price + (tolerance * 1.2):
                    bounce_count += 1
            else:
                downside_move = min(
                    float(future_low.min()) if future_low.notna().any() else level_price,
                    float(future_close.min()) if future_close.notna().any() else level_price,
                )
                if downside_move <= level_price - (tolerance * 1.2):
                    bounce_count += 1

        index = cluster_end + 1

    return touch_count, bounce_count


