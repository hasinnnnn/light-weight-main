from __future__ import annotations

from typing import Any

import pandas as pd

from common.time_utils import format_short_date_label
from indicators.chart_patterns_parts.runtime import detect_chart_patterns

def summarize_chart_patterns(
    data: pd.DataFrame,
    raw_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return grouped chart-pattern summary data for UI explanations."""
    patterns = detect_chart_patterns(data, raw_params)
    latest_by_direction: dict[str, dict[str, Any]] = {}
    for direction in ["bullish", "bearish", "neutral"]:
        direction_patterns = [pattern for pattern in patterns if pattern["direction"] == direction]
        if not direction_patterns:
            continue
        latest = direction_patterns[-1]
        latest_by_direction[direction] = {
            "label": latest["label"],
            "short_label": latest["short_label"],
            "description": latest["description"],
            "time": latest["start_time"],
            "start_time": latest["start_time"],
            "end_time": latest["end_time"],
            "date_label": format_short_date_label(latest["start_time"]),
            "detail_lines": latest.get("detail_lines") or [],
        }

    summary_rows = [
        {
            "label": pattern["label"],
            "short_label": pattern["short_label"],
            "description": pattern["description"],
            "direction": pattern["direction"],
            "time": pattern["start_time"],
            "start_time": pattern["start_time"],
            "end_time": pattern["end_time"],
            "date_label": format_short_date_label(pattern["start_time"]),
            "detail_lines": pattern.get("detail_lines") or [],
        }
        for pattern in patterns
    ]
    return {
        "patterns": summary_rows,
        "latest_by_direction": latest_by_direction,
        "total_patterns": int(len(patterns)),
    }

