from __future__ import annotations

from typing import Any

import pandas as pd

from charts.chart_core import (
    _build_datetime_ohlcv_source,
    _build_high_low_close_volume_source,
    _indicator_params,
    _select_major_trend_analysis_frame,
)
from indicators.trendline_parts.core import _collect_pivot_points, _select_auto_trendline_candidates

def _trendline_break_display_label(direction: str, latest_signal: str, has_any_break: bool) -> str:
    """Return one compact break label that respects support vs resistance roles."""
    if direction == "up":
        if latest_signal in {"fresh_breakdown", "breakdown"}:
            return "Breakdown Valid"
        if latest_signal == "reclaimed":
            return "False Breakdown"
        if latest_signal == "retest":
            return "Baru Disentuh"
        return "Pernah Breakdown" if has_any_break else "Belum Ada Breakdown"

    if latest_signal in {"fresh_breakout", "breakout"}:
        return "Breakout Valid"
    if latest_signal == "rejected":
        return "False Breakout"
    if latest_signal == "retest":
        return "Baru Disentuh"
    return "Pernah Breakout" if has_any_break else "Belum Ada Breakout"



def _trendline_status_label(direction: str, latest_signal: str) -> str:
    """Return one human-friendly trendline status label."""
    if direction == "up":
        labels = {
            "fresh_breakdown": "Breakdown valid: candle close baru menutup di bawah trendline support.",
            "breakdown": "Breakdown valid: candle close masih berada di bawah trendline support.",
            "reclaimed": "False breakdown: sempat close di bawah support, tetapi sekarang sudah kembali di atas trendline.",
            "retest": "Harga baru menyentuh trendline support. Ini belum breakdown karena candle close belum ditutup jelas di bawah garis.",
            "holding": "Harga masih bertahan di atas trendline support. Belum ada breakdown valid.",
        }
    else:
        labels = {
            "fresh_breakout": "Breakout valid: candle close baru menutup di atas trendline resistance.",
            "breakout": "Breakout valid: candle close masih berada di atas trendline resistance.",
            "rejected": "False breakout: sempat close di atas resistance, tetapi sekarang sudah kembali di bawah trendline.",
            "retest": "Harga baru menyentuh trendline resistance. Ini belum breakout karena candle close belum ditutup jelas di atas garis.",
            "holding": "Harga masih tertahan di bawah trendline resistance. Belum ada breakout valid.",
        }
    return labels.get(latest_signal, "Status trendline belum terbaca dengan jelas.")



def _build_trendline_summary_item(
    frame: pd.DataFrame,
    trendline_candidate: dict[str, Any],
    lookback: int,
    pivot_window: int,
    current_price_frame: pd.DataFrame | None = None,
    start_time_override: Any | None = None,
    end_time_override: Any | None = None,
    analysis_timeframe: str | None = None,
) -> dict[str, Any] | None:
    """Convert one raw trendline candidate into a full UI/chart summary item."""
    direction = str(trendline_candidate["direction"])
    start_index = int(trendline_candidate["start_index"])
    end_index = int(trendline_candidate["end_index"])
    last_index = len(frame) - 1
    if start_index < 0 or last_index < start_index:
        return None

    comparison_frame = frame.iloc[start_index : last_index + 1]
    line_values = pd.Series(
        [
            float(trendline_candidate["start_value"])
            + (float(trendline_candidate["slope"]) * (index - start_index))
            for index in range(start_index, last_index + 1)
        ],
        index=comparison_frame.index,
        dtype="float64",
    )
    tolerance = float(trendline_candidate["tolerance"])
    active_price_frame = current_price_frame if current_price_frame is not None else frame
    current_price = float(pd.to_numeric(active_price_frame["close"], errors="coerce").iloc[-1])
    current_line_value = float(line_values.iloc[-1])
    pivot_column = "low" if direction == "up" else "high"
    pivot_points = _collect_pivot_points(frame, pivot_column, pivot_window)

    touch_indices = {start_index, end_index}
    for pivot_point in pivot_points:
        pivot_index = int(pivot_point["index"])
        if pivot_index < start_index or pivot_index > last_index:
            continue
        line_value_at_pivot = float(trendline_candidate["start_value"]) + (
            float(trendline_candidate["slope"]) * (pivot_index - start_index)
        )
        if abs(float(pivot_point["price"]) - line_value_at_pivot) <= tolerance:
            touch_indices.add(pivot_index)

    last_touch_index = max(touch_indices) if touch_indices else end_index
    latest_signal = str(trendline_candidate.get("latest_signal") or "")
    relevant_break_dates = list(
        trendline_candidate.get("breakdown_dates", [])
        if direction == "up"
        else trendline_candidate.get("breakout_dates", [])
    )
    latest_break_date = relevant_break_dates[-1] if relevant_break_dates else None
    has_any_relevant_break = bool(relevant_break_dates)
    break_display_label = _trendline_break_display_label(direction, latest_signal, has_any_relevant_break)
    is_breakout_active = latest_signal in {"fresh_breakout", "breakout"}
    is_breakdown_active = latest_signal in {"fresh_breakdown", "breakdown"}

    summary = {
        **trendline_candidate,
        "start_time": start_time_override if start_time_override is not None else frame["time"].iloc[start_index],
        "end_time": end_time_override if end_time_override is not None else frame["time"].iloc[-1],
        "lookback": lookback,
        "pivot_window": pivot_window,
        "role": "support" if direction == "up" else "resistance",
        "touch_count": len(touch_indices),
        "last_touch_gap": last_index - last_touch_index,
        "current_price": current_price,
        "line_value": current_line_value,
        "distance_to_line": abs(current_price - current_line_value),
        "status_label": _trendline_status_label(direction, latest_signal),
        "break_display_label": break_display_label,
        "latest_break_date": latest_break_date,
        "has_any_relevant_break": has_any_relevant_break,
        "relevant_break_dates": relevant_break_dates,
        "is_breakout_active": is_breakout_active,
        "is_breakdown_active": is_breakdown_active,
    }
    if analysis_timeframe is not None:
        summary["analysis_timeframe"] = analysis_timeframe
    return summary



def _build_auto_trendline_summaries(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Build multiple auto-trendline summaries for chart rendering and UI details."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 80), 20)
    pivot_window = max(params.get("swing_window", 3), 1)
    max_trendlines = max(params.get("max_trendlines", 3), 1)
    frame = _build_high_low_close_volume_source(data).tail(lookback).reset_index(drop=True)
    trendline_candidates = _select_auto_trendline_candidates(frame, pivot_window, max_trendlines)
    if not trendline_candidates:
        return None

    trendlines: list[dict[str, Any]] = []
    for candidate in trendline_candidates:
        summary = _build_trendline_summary_item(
            frame=frame,
            trendline_candidate=candidate,
            lookback=lookback,
            pivot_window=pivot_window,
        )
        if summary is not None:
            trendlines.append(summary)

    if not trendlines:
        return None

    return {
        "primary": trendlines[0],
        "trendlines": trendlines,
        "lookback": lookback,
        "pivot_window": pivot_window,
        "max_trendlines": max_trendlines,
    }



def describe_auto_trendline(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the primary auto-trendline summary for UI display."""
    summary_bundle = _build_auto_trendline_summaries(data, indicator)
    if summary_bundle is None:
        return None
    return summary_bundle["primary"]



def describe_auto_trendlines(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Return all visible auto-trendline summaries for UI display."""
    return _build_auto_trendline_summaries(data, indicator)



def _build_major_trendline_summaries(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Build multiple higher-timeframe major trendline summaries for chart rendering and UI details."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 260), 60)
    pivot_window = max(params.get("swing_window", 4), 2)
    max_trendlines = max(params.get("max_trendlines", 3), 1)
    source_frame = _build_datetime_ohlcv_source(data)
    if source_frame.empty:
        return None

    analysis_frame, analysis_timeframe = _select_major_trend_analysis_frame(source_frame, interval_label)
    analysis_frame = analysis_frame.tail(lookback).reset_index(drop=True)
    if len(analysis_frame) < max((pivot_window * 2) + 3, 12):
        return None

    chart_frame = _build_high_low_close_volume_source(data).reset_index(drop=True)
    if chart_frame.empty:
        return None

    chart_times = pd.to_datetime(chart_frame["time"], errors="coerce")
    trendline_candidates = _select_auto_trendline_candidates(analysis_frame, pivot_window, max_trendlines)
    if not trendline_candidates:
        return None

    trendlines: list[dict[str, Any]] = []
    for candidate in trendline_candidates:
        start_index = int(candidate["start_index"])
        analysis_start_time = pd.to_datetime(analysis_frame["time"].iloc[start_index], errors="coerce")
        aligned_start_mask = chart_times.ge(analysis_start_time)
        if aligned_start_mask.any():
            aligned_start_index = int(aligned_start_mask.idxmax())
        else:
            aligned_start_index = 0

        summary = _build_trendline_summary_item(
            frame=analysis_frame,
            trendline_candidate=candidate,
            lookback=lookback,
            pivot_window=pivot_window,
            current_price_frame=chart_frame,
            start_time_override=chart_frame["time"].iloc[aligned_start_index],
            end_time_override=chart_frame["time"].iloc[-1],
            analysis_timeframe=analysis_timeframe,
        )
        if summary is not None:
            trendlines.append(summary)

    if not trendlines:
        return None

    return {
        "primary": trendlines[0],
        "trendlines": trendlines,
        "lookback": lookback,
        "pivot_window": pivot_window,
        "max_trendlines": max_trendlines,
        "analysis_timeframe": analysis_timeframe,
    }



def describe_major_trendline(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Return the primary major trendline summary for UI display."""
    summary_bundle = _build_major_trendline_summaries(data, indicator, interval_label)
    if summary_bundle is None:
        return None
    return summary_bundle["primary"]



def describe_major_trendlines(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Return all visible major trendline summaries for UI display."""
    return _build_major_trendline_summaries(data, indicator, interval_label)

