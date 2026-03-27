from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_core import _build_high_low_close_volume_source, _indicator_params
from indicators.trendlines import _collect_pivot_points

def _nearest_support_resistance_zone_half_height(frame: pd.DataFrame) -> float:
    """Estimate one reasonable half-zone size from recent volatility."""
    high_series = pd.to_numeric(frame["high"], errors="coerce")
    low_series = pd.to_numeric(frame["low"], errors="coerce")
    close_series = pd.to_numeric(frame["close"], errors="coerce")
    candle_ranges = (high_series - low_series).dropna()
    median_range = float(candle_ranges.median()) if not candle_ranges.empty else 0.0
    full_range = float(high_series.max() - low_series.min()) if not frame.empty else 0.0
    latest_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0

    zone_half_height = max(
        median_range * 0.6,
        full_range * 0.008,
        abs(latest_close) * 0.0025,
        0.01,
    )
    zone_half_height_cap = max(
        median_range * 1.8,
        full_range * 0.05,
        abs(latest_close) * 0.02,
        0.05,
    )
    return min(zone_half_height, zone_half_height_cap)


def _fallback_nearest_level(
    frame: pd.DataFrame,
    direction: str,
    zone_half_height: float,
) -> dict[str, Any] | None:
    """Fallback to the nearest raw candle extreme when pivot clustering is sparse."""
    current_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    source_column = "low" if direction == "support" else "high"
    source_series = pd.to_numeric(frame[source_column], errors="coerce")

    if direction == "support":
        candidate_series = source_series[source_series <= current_close]
        if candidate_series.empty:
            candidate_series = source_series
        level_index = int(candidate_series.idxmax())
    else:
        candidate_series = source_series[source_series >= current_close]
        if candidate_series.empty:
            candidate_series = source_series
        level_index = int(candidate_series.idxmin())

    level_price = float(source_series.iloc[level_index])
    return {
        "direction": direction,
        "price": level_price,
        "zone_bottom": level_price - zone_half_height,
        "zone_top": level_price + zone_half_height,
        "bounces": 1,
        "distance": abs(current_close - level_price),
        "last_touch_gap": (len(frame) - 1) - level_index,
    }


def _build_nearest_level_candidate(
    frame: pd.DataFrame,
    pivot_points: list[dict[str, Any]],
    direction: str,
    zone_half_height: float,
) -> dict[str, Any] | None:
    """Build the nearest support or resistance level from clustered pivots."""
    if frame.empty:
        return None

    current_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    if not pivot_points:
        return _fallback_nearest_level(frame, direction, zone_half_height)

    candidates: list[dict[str, Any]] = []
    seen_signatures: set[tuple[int, ...]] = set()
    side_tolerance = zone_half_height * 0.4

    for seed_point in pivot_points:
        cluster_points = [
            point
            for point in pivot_points
            if abs(float(point["price"]) - float(seed_point["price"])) <= zone_half_height
        ]
        cluster_signature = tuple(sorted(int(point["index"]) for point in cluster_points))
        if not cluster_signature or cluster_signature in seen_signatures:
            continue
        seen_signatures.add(cluster_signature)

        cluster_price = float(
            sum(float(point["price"]) for point in cluster_points) / len(cluster_points)
        )
        if direction == "support" and cluster_price > current_close + side_tolerance:
            continue
        if direction == "resistance" and cluster_price < current_close - side_tolerance:
            continue

        last_touch_index = max(int(point["index"]) for point in cluster_points)
        candidates.append(
            {
                "direction": direction,
                "price": cluster_price,
                "zone_bottom": cluster_price - zone_half_height,
                "zone_top": cluster_price + zone_half_height,
                "bounces": len(cluster_points),
                "distance": abs(current_close - cluster_price),
                "last_touch_gap": (len(frame) - 1) - last_touch_index,
            }
        )

    if not candidates:
        return _fallback_nearest_level(frame, direction, zone_half_height)

    return min(
        candidates,
        key=lambda item: (
            item["distance"],
            -item["bounces"],
            item["last_touch_gap"],
        ),
    )


def _build_nearest_support_resistance_summary(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Build one support/resistance summary for both chart rendering and UI details."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 120), 20)
    swing_window = max(params.get("swing_window", 3), 1)
    frame = _build_high_low_close_volume_source(data).tail(lookback).reset_index(drop=True)
    if frame.empty or len(frame) < max((swing_window * 2) + 3, 8):
        return None

    zone_half_height = _nearest_support_resistance_zone_half_height(frame)
    support = _build_nearest_level_candidate(
        frame=frame,
        pivot_points=_collect_pivot_points(frame, "low", swing_window),
        direction="support",
        zone_half_height=zone_half_height,
    )
    resistance = _build_nearest_level_candidate(
        frame=frame,
        pivot_points=_collect_pivot_points(frame, "high", swing_window),
        direction="resistance",
        zone_half_height=zone_half_height,
    )

    return {
        "start_time": frame["time"].iloc[0],
        "end_time": frame["time"].iloc[-1],
        "current_price": float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1]),
        "zone_half_height": zone_half_height,
        "support": support,
        "resistance": resistance,
    }


def describe_nearest_support_resistance(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the nearest support/resistance summary for UI display."""
    return _build_nearest_support_resistance_summary(data, indicator)

