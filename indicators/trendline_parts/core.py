from __future__ import annotations

from typing import Any

import pandas as pd

from common.time_utils import format_short_date_label

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


def _trendline_tolerance(frame: pd.DataFrame) -> float:
    """Return a small tolerance so minor wick noise does not invalidate a trendline."""
    high_series = pd.to_numeric(frame["high"], errors="coerce")
    low_series = pd.to_numeric(frame["low"], errors="coerce")
    close_series = pd.to_numeric(frame["close"], errors="coerce")
    price_range = float(high_series.max() - low_series.min())
    latest_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0
    if price_range > 0:
        return price_range * 0.015
    return max(abs(latest_close) * 0.002, 0.01)


def _true_cluster_event_dates(mask: pd.Series, time_series: pd.Series) -> list[str]:
    """Return one date label for each contiguous True cluster."""
    normalized_mask = mask.fillna(False).astype(bool)
    if normalized_mask.empty:
        return []

    transition_mask = normalized_mask & ~normalized_mask.shift(1, fill_value=False)
    raw_event_times = time_series.loc[transition_mask]
    event_dates: list[str] = []
    seen_dates: set[str] = set()

    for raw_time in raw_event_times:
        parsed_time = pd.to_datetime(raw_time, errors="coerce")
        if pd.isna(parsed_time):
            date_label = format_short_date_label(raw_time)
        else:
            date_label = format_short_date_label(parsed_time)

        if date_label and date_label not in seen_dates:
            seen_dates.add(date_label)
            event_dates.append(date_label)

    return event_dates


def _count_true_clusters(mask: pd.Series) -> int:
    """Return the number of contiguous True segments inside one boolean mask."""
    normalized_mask = mask.fillna(False).astype(bool)
    if normalized_mask.empty:
        return 0
    transition_mask = normalized_mask & ~normalized_mask.shift(1, fill_value=False)
    return int(transition_mask.sum())


def _score_trendline_candidate(
    frame: pd.DataFrame,
    start_pivot: dict[str, Any],
    end_pivot: dict[str, Any],
    direction: str,
) -> dict[str, Any] | None:
    """Score one trendline candidate so the most recent clean line can be selected."""
    start_index = int(start_pivot["index"])
    end_index = int(end_pivot["index"])
    if end_index <= start_index:
        return None

    span = end_index - start_index
    slope = (float(end_pivot["price"]) - float(start_pivot["price"])) / span
    if direction == "up" and slope <= 0:
        return None
    if direction == "down" and slope >= 0:
        return None

    last_index = len(frame) - 1
    projected_end_price = float(end_pivot["price"]) + (slope * (last_index - end_index))
    if pd.isna(projected_end_price) or projected_end_price <= 0:
        return None

    comparison_frame = frame.iloc[start_index : last_index + 1]
    line_values = pd.Series(
        [
            float(start_pivot["price"]) + (slope * (index - start_index))
            for index in range(start_index, last_index + 1)
        ],
        index=comparison_frame.index,
        dtype="float64",
    )
    tolerance = _trendline_tolerance(frame)

    if direction == "up":
        reference_series = pd.to_numeric(comparison_frame["low"], errors="coerce")
        violations = int(reference_series.lt(line_values - tolerance).sum())
    else:
        reference_series = pd.to_numeric(comparison_frame["high"], errors="coerce")
        violations = int(reference_series.gt(line_values + tolerance).sum())

    close_series = pd.to_numeric(comparison_frame["close"], errors="coerce")
    latest_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    latest_line_value = float(line_values.iloc[-1])
    breakout_dates = _true_cluster_event_dates(
        close_series.gt(line_values + tolerance),
        comparison_frame["time"],
    )
    breakdown_dates = _true_cluster_event_dates(
        close_series.lt(line_values - tolerance),
        comparison_frame["time"],
    )
    breakout_count = len(breakout_dates)
    breakdown_count = len(breakdown_dates)

    previous_close = float(close_series.iloc[-2]) if len(close_series) >= 2 else latest_close
    previous_line_value = float(line_values.iloc[-2]) if len(line_values) >= 2 else latest_line_value
    previous_above = previous_close > previous_line_value + tolerance
    previous_below = previous_close < previous_line_value - tolerance
    latest_above = latest_close > latest_line_value + tolerance
    latest_below = latest_close < latest_line_value - tolerance

    if direction == "up":
        if latest_below and not previous_below:
            latest_signal = "fresh_breakdown"
        elif latest_below:
            latest_signal = "breakdown"
        elif breakdown_count > 0:
            latest_signal = "reclaimed"
        elif abs(latest_close - latest_line_value) <= tolerance:
            latest_signal = "retest"
        else:
            latest_signal = "holding"
    else:
        if latest_above and not previous_above:
            latest_signal = "fresh_breakout"
        elif latest_above:
            latest_signal = "breakout"
        elif breakout_count > 0:
            latest_signal = "rejected"
        elif abs(latest_close - latest_line_value) <= tolerance:
            latest_signal = "retest"
        else:
            latest_signal = "holding"

    return {
        "direction": direction,
        "start_index": start_index,
        "end_index": end_index,
        "start_time": start_pivot["time"],
        "start_value": float(start_pivot["price"]),
        "end_pivot_time": end_pivot["time"],
        "end_pivot_value": float(end_pivot["price"]),
        "end_time": frame["time"].iloc[-1],
        "end_value": projected_end_price,
        "slope": slope,
        "tolerance": tolerance,
        "line_value": latest_line_value,
        "violations": violations,
        "breakout_count": breakout_count,
        "breakdown_count": breakdown_count,
        "breakout_dates": breakout_dates,
        "breakdown_dates": breakdown_dates,
        "latest_signal": latest_signal,
        "last_pivot_gap": last_index - end_index,
        "distance": abs(latest_close - projected_end_price),
        "span": span,
    }


def _build_fallback_trendline_candidate(
    frame: pd.DataFrame,
    direction: str,
) -> dict[str, Any] | None:
    """Fallback to broad recent extremes if pivot detection finds no clean pair."""
    if len(frame) < 6:
        return None

    split_index = max(len(frame) // 2, 2)
    first_half = frame.iloc[:split_index]
    second_half = frame.iloc[split_index:-1]
    if first_half.empty or second_half.empty:
        return None

    pivot_column = "low" if direction == "up" else "high"
    first_series = pd.to_numeric(first_half[pivot_column], errors="coerce")
    second_series = pd.to_numeric(second_half[pivot_column], errors="coerce")
    if first_series.empty or second_series.empty:
        return None

    first_index = int(first_series.idxmin() if direction == "up" else first_series.idxmax())
    second_index = int(second_series.idxmin() if direction == "up" else second_series.idxmax())
    if second_index <= first_index:
        return None

    start_pivot = {
        "index": first_index,
        "time": frame["time"].iloc[first_index],
        "price": float(pd.to_numeric(frame[pivot_column], errors="coerce").iloc[first_index]),
    }
    end_pivot = {
        "index": second_index,
        "time": frame["time"].iloc[second_index],
        "price": float(pd.to_numeric(frame[pivot_column], errors="coerce").iloc[second_index]),
    }
    return _score_trendline_candidate(frame, start_pivot, end_pivot, direction)


def _build_trendline_candidates(
    frame: pd.DataFrame,
    direction: str,
    pivot_window: int,
) -> list[dict[str, Any]]:
    """Build ranked recent trendline candidates for one direction."""
    pivot_column = "low" if direction == "up" else "high"
    pivot_points = _collect_pivot_points(frame, pivot_column, pivot_window)
    if len(pivot_points) < 2:
        fallback = _build_fallback_trendline_candidate(frame, direction)
        return [fallback] if fallback is not None else []

    recent_gap_limit = max(pivot_window * 4, len(frame) // 4, 6)
    recent_start_floor = max(pivot_window, len(frame) // 3)
    ranked_candidates: list[dict[str, Any]] = []

    for require_recent in (True, False):
        candidates: list[dict[str, Any]] = []
        pivot_start_index = max(0, len(pivot_points) - 6)
        for first_index in range(pivot_start_index, len(pivot_points) - 1):
            for second_index in range(first_index + 1, len(pivot_points)):
                start_pivot = pivot_points[first_index]
                end_pivot = pivot_points[second_index]
                if require_recent:
                    if int(start_pivot["index"]) < recent_start_floor:
                        continue
                    if (len(frame) - 1) - int(end_pivot["index"]) > recent_gap_limit:
                        continue

                candidate = _score_trendline_candidate(
                    frame=frame,
                    start_pivot=start_pivot,
                    end_pivot=end_pivot,
                    direction=direction,
                )
                if candidate is not None:
                    candidates.append(candidate)

        if candidates:
            ranked_candidates.extend(
                sorted(
                    candidates,
                    key=lambda candidate: (
                        int(candidate["violations"]),
                        int(candidate["last_pivot_gap"]),
                        float(candidate["distance"]),
                        -int(candidate["span"]),
                    ),
                )
            )
            if require_recent:
                break

    if not ranked_candidates:
        fallback = _build_fallback_trendline_candidate(frame, direction)
        return [fallback] if fallback is not None else []

    unique_candidates: list[dict[str, Any]] = []
    seen_anchor_pairs: set[tuple[int, int]] = set()
    for candidate in ranked_candidates:
        anchor_pair = (int(candidate["start_index"]), int(candidate["end_index"]))
        if anchor_pair in seen_anchor_pairs:
            continue
        seen_anchor_pairs.add(anchor_pair)
        unique_candidates.append(candidate)

    return unique_candidates



def _select_auto_trendline_candidates(
    frame: pd.DataFrame,
    pivot_window: int,
    max_candidates: int,
) -> list[dict[str, Any]]:
    """Choose the most relevant recent trendlines, up or down, for the chart tail."""
    if frame.empty or len(frame) < max((pivot_window * 2) + 3, 8):
        return []

    up_candidates = _build_trendline_candidates(frame, "up", pivot_window)
    down_candidates = _build_trendline_candidates(frame, "down", pivot_window)
    candidates = [candidate for candidate in [*up_candidates, *down_candidates] if candidate is not None]
    if not candidates:
        return []

    recent_span = min(max(pivot_window * 4, 6), len(frame) - 1)
    baseline_index = max(len(frame) - recent_span - 1, 0)
    close_series = pd.to_numeric(frame["close"], errors="coerce")
    preferred_direction = (
        "up"
        if float(close_series.iloc[-1] - close_series.iloc[baseline_index]) >= 0
        else "down"
    )
    ranked_candidates = sorted(
        candidates,
        key=lambda item: (
            item["violations"],
            0 if item["direction"] == preferred_direction else 1,
            item["last_pivot_gap"],
            item["distance"],
            -item["span"],
        ),
    )

    selected_candidates: list[dict[str, Any]] = []
    start_anchor_gap = max(pivot_window * 2, 2)
    end_anchor_gap = max(pivot_window, 1)

    for candidate in ranked_candidates:
        is_too_similar = any(
            str(existing["direction"]) == str(candidate["direction"])
            and abs(int(existing["end_index"]) - int(candidate["end_index"])) <= end_anchor_gap
            and abs(int(existing["start_index"]) - int(candidate["start_index"])) <= start_anchor_gap
            for existing in selected_candidates
        )
        if is_too_similar:
            continue

        shares_anchor = any(
            str(existing["direction"]) == str(candidate["direction"])
            and (
                abs(int(existing["start_index"]) - int(candidate["start_index"])) <= start_anchor_gap
                or abs(int(existing["end_index"]) - int(candidate["end_index"])) <= end_anchor_gap
            )
            for existing in selected_candidates
        )
        if shares_anchor:
            continue

        selected_candidates.append(candidate)
        if len(selected_candidates) >= max(max_candidates, 1):
            break

    return selected_candidates

