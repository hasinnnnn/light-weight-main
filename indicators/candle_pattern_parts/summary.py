from __future__ import annotations

from typing import Any

import pandas as pd

from common.time_utils import format_short_date_label
from indicators.candle_pattern_parts.meta import normalize_candle_pattern_params
from indicators.candle_pattern_parts.runtime import detect_candle_patterns

def summarize_candle_patterns(
    data: pd.DataFrame,
    raw_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return grouped candle-pattern summary data for UI explanations."""
    params = normalize_candle_pattern_params(raw_params)
    events = detect_candle_patterns(data, params)
    if events.empty:
        return {
            "events": [],
            "latest_by_direction": {},
            "total_events": 0,
        }

    formatted_events = events.copy()
    formatted_events["date_label"] = formatted_events["time"].map(format_short_date_label)
    event_rows = [
        {
            "time": row.time,
            "date_label": row.date_label,
            "pattern_key": row.pattern_key,
            "label": row.label,
            "short_label": row.short_label,
            "description": row.description,
            "direction": row.direction,
        }
        for row in formatted_events.itertuples(index=False)
    ]

    latest_by_direction: dict[str, dict[str, Any]] = {}
    for direction in ["bullish", "bearish", "neutral"]:
        direction_events = formatted_events.loc[formatted_events["direction"] == direction]
        if direction_events.empty:
            continue
        latest = direction_events.iloc[-1]
        latest_by_direction[direction] = {
            "label": str(latest["label"]),
            "short_label": str(latest["short_label"]),
            "description": str(latest["description"]),
            "date_label": format_short_date_label(latest["time"]),
        }

    return {
        "events": event_rows,
        "latest_by_direction": latest_by_direction,
        "total_events": int(len(events)),
    }

