from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_core import (
    STRONG_SUPPORT_RESISTANCE_VOLUME_THRESHOLD,
    _build_datetime_ohlcv_source,
    _build_high_low_close_volume_source,
    _indicator_params,
    _select_strong_sr_analysis_frame,
)
from indicators.support_resistance_parts.nearest import _nearest_support_resistance_zone_half_height
from indicators.trendlines import _collect_pivot_points

def _build_strong_sr_pivot_points(
    frame: pd.DataFrame,
    column: str,
    window: int,
) -> list[dict[str, Any]]:
    """Collect significant pivots together with reversal-volume context."""
    pivot_points = _collect_pivot_points(frame, column, window)
    if not pivot_points:
        return []

    volume_series = pd.to_numeric(frame["volume"], errors="coerce").fillna(0.0)
    volume_average = volume_series.rolling(window=20, min_periods=3).mean()
    volume_ratio = volume_series.div(volume_average.replace(0, pd.NA)).fillna(1.0)

    enriched_pivots: list[dict[str, Any]] = []
    for pivot_point in pivot_points:
        pivot_index = int(pivot_point["index"])
        enriched_pivots.append(
            {
                **pivot_point,
                "volume_ratio": float(volume_ratio.iloc[pivot_index]),
            }
        )
    return enriched_pivots


def _strong_support_resistance_zone_half_height(frame: pd.DataFrame) -> float:
    """Return a slightly wider zone for strong support/resistance areas."""
    return _nearest_support_resistance_zone_half_height(frame) * 1.15


def _build_strong_level_candidate(
    frame: pd.DataFrame,
    pivot_points: list[dict[str, Any]],
    direction: str,
    zone_half_height: float,
    min_bounces: int,
) -> dict[str, Any] | None:
    """Build one strong support or resistance candidate from repeated higher-timeframe pivots."""
    if frame.empty or not pivot_points:
        return None

    current_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    side_tolerance = zone_half_height * 0.45
    candidates: list[dict[str, Any]] = []
    seen_signatures: set[tuple[int, ...]] = set()
    close_series = pd.to_numeric(frame["close"], errors="coerce")

    for seed_point in pivot_points:
        cluster_points = [
            point
            for point in pivot_points
            if abs(float(point["price"]) - float(seed_point["price"])) <= zone_half_height
        ]
        cluster_signature = tuple(sorted(int(point["index"]) for point in cluster_points))
        if (
            len(cluster_points) < min_bounces
            or not cluster_signature
            or cluster_signature in seen_signatures
        ):
            continue
        seen_signatures.add(cluster_signature)

        cluster_price = float(
            sum(float(point["price"]) for point in cluster_points) / len(cluster_points)
        )
        if direction == "support" and cluster_price > current_close + side_tolerance:
            continue
        if direction == "resistance" and cluster_price < current_close - side_tolerance:
            continue

        first_touch_index = min(int(point["index"]) for point in cluster_points)
        last_touch_index = max(int(point["index"]) for point in cluster_points)
        zone_bottom = cluster_price - zone_half_height
        zone_top = cluster_price + zone_half_height
        post_touch_close = close_series.iloc[first_touch_index:]
        if direction == "support":
            breakout_count = int(post_touch_close.lt(zone_bottom).sum())
        else:
            breakout_count = int(post_touch_close.gt(zone_top).sum())

        high_volume_reversals = sum(
            1
            for point in cluster_points
            if float(point.get("volume_ratio", 1.0)) >= STRONG_SUPPORT_RESISTANCE_VOLUME_THRESHOLD
        )
        average_volume_ratio = (
            sum(float(point.get("volume_ratio", 1.0)) for point in cluster_points) / len(cluster_points)
        )
        candidates.append(
            {
                "direction": direction,
                "price": cluster_price,
                "zone_bottom": zone_bottom,
                "zone_top": zone_top,
                "bounces": len(cluster_points),
                "breakout_count": breakout_count,
                "high_volume_reversals": high_volume_reversals,
                "average_volume_ratio": average_volume_ratio,
                "distance": abs(current_close - cluster_price),
                "last_touch_gap": (len(frame) - 1) - last_touch_index,
                "span": last_touch_index - first_touch_index,
            }
        )

    if not candidates:
        return None

    clean_candidates = [candidate for candidate in candidates if candidate["breakout_count"] == 0]
    if clean_candidates:
        candidates = clean_candidates
    else:
        candidates = sorted(candidates, key=lambda item: item["breakout_count"])[:3]

    return min(
        candidates,
        key=lambda item: (
            item["breakout_count"],
            -item["bounces"],
            -item["high_volume_reversals"],
            -item["average_volume_ratio"],
            item["distance"],
            item["last_touch_gap"],
            -item["span"],
        ),
    )


def _build_strong_support_resistance_summary(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Build strong support/resistance levels from repeated higher-timeframe tests."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 160), 40)
    swing_window = max(params.get("swing_window", 3), 1)
    min_bounces = max(params.get("min_bounces", 3), 2)
    source_frame = _build_datetime_ohlcv_source(data)
    if source_frame.empty:
        return None

    analysis_frame, analysis_timeframe = _select_strong_sr_analysis_frame(source_frame, interval_label)
    analysis_frame = analysis_frame.tail(lookback).reset_index(drop=True)
    if len(analysis_frame) < max((swing_window * 2) + 3, min_bounces + 2):
        return None

    zone_half_height = _strong_support_resistance_zone_half_height(analysis_frame)
    support = _build_strong_level_candidate(
        frame=analysis_frame,
        pivot_points=_build_strong_sr_pivot_points(analysis_frame, "low", swing_window),
        direction="support",
        zone_half_height=zone_half_height,
        min_bounces=min_bounces,
    )
    resistance = _build_strong_level_candidate(
        frame=analysis_frame,
        pivot_points=_build_strong_sr_pivot_points(analysis_frame, "high", swing_window),
        direction="resistance",
        zone_half_height=zone_half_height,
        min_bounces=min_bounces,
    )

    chart_frame = _build_high_low_close_volume_source(data).reset_index(drop=True)
    chart_times = pd.to_datetime(chart_frame["time"], errors="coerce")
    analysis_start_time = analysis_frame["time"].iloc[0]
    visible_chart_frame = chart_frame.loc[chart_times >= analysis_start_time]
    if visible_chart_frame.empty:
        visible_chart_frame = chart_frame

    return {
        "start_time": visible_chart_frame["time"].iloc[0],
        "end_time": chart_frame["time"].iloc[-1],
        "current_price": float(pd.to_numeric(chart_frame["close"], errors="coerce").iloc[-1]),
        "analysis_timeframe": analysis_timeframe,
        "minimum_bounces": min_bounces,
        "support": support,
        "resistance": resistance,
    }


def describe_strong_support_resistance(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Return the strong support/resistance summary for UI display."""
    return _build_strong_support_resistance_summary(data, indicator, interval_label)

