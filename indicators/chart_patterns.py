from __future__ import annotations

from typing import Any

import pandas as pd

from common.time_utils import format_short_date_label

CHART_PATTERN_DEFINITIONS: dict[str, dict[str, str]] = {
    "double_top": {
        "label": "Double Top",
        "short_label": "DTOP",
        "description": "Dua puncak di area yang mirip, sering dibaca sebagai pola distribusi dan potensi reversal turun.",
        "direction": "bearish",
    },
    "double_bottom": {
        "label": "Double Bottom",
        "short_label": "DBOT",
        "description": "Dua lembah di area yang mirip, sering dibaca sebagai pola akumulasi dan potensi reversal naik.",
        "direction": "bullish",
    },
    "head_shoulders": {
        "label": "Head and Shoulders",
        "short_label": "H&S",
        "description": "Pola tiga puncak dengan kepala lebih tinggi dari kedua bahu, biasanya memberi bias bearish.",
        "direction": "bearish",
    },
    "inverse_head_shoulders": {
        "label": "Inverse Head and Shoulders",
        "short_label": "IHS",
        "description": "Pola tiga lembah dengan kepala lebih rendah dari kedua bahu, biasanya memberi bias bullish.",
        "direction": "bullish",
    },
    "ascending_triangle": {
        "label": "Ascending Triangle",
        "short_label": "AT",
        "description": "Resistance cenderung datar dengan support naik, biasanya mendukung skenario breakout bullish.",
        "direction": "bullish",
    },
    "descending_triangle": {
        "label": "Descending Triangle",
        "short_label": "DTG",
        "description": "Support cenderung datar dengan resistance turun, biasanya mendukung skenario breakdown bearish.",
        "direction": "bearish",
    },
    "symmetrical_triangle": {
        "label": "Symmetrical Triangle",
        "short_label": "ST",
        "description": "Range makin menyempit dengan lower high dan higher low, biasanya menunggu arah breakout berikutnya.",
        "direction": "neutral",
    },
    "rising_wedge": {
        "label": "Rising Wedge",
        "short_label": "RW",
        "description": "Harga naik dalam dua garis konvergen, sering dianggap sinyal melemahnya tren naik dan rawan koreksi.",
        "direction": "bearish",
    },
    "falling_wedge": {
        "label": "Falling Wedge",
        "short_label": "FW",
        "description": "Harga turun dalam dua garis konvergen, sering dianggap sinyal pelemahan tekanan jual dan potensi reversal naik.",
        "direction": "bullish",
    },
    "cup_handle": {
        "label": "Cup and Handle",
        "short_label": "C&H",
        "description": "Pola rounded base diikuti handle dangkal, sering dibaca sebagai kelanjutan bullish saat breakout rim.",
        "direction": "bullish",
    },
}

ALL_CHART_PATTERN_KEYS = list(CHART_PATTERN_DEFINITIONS.keys())


def get_default_chart_pattern_params() -> dict[str, Any]:
    """Return the default Chart Pattern indicator settings."""
    defaults: dict[str, Any] = {
        "lookback": 220,
        "pivot_window": 3,
        "tolerance_pct": 3,
    }
    for pattern_key in ALL_CHART_PATTERN_KEYS:
        defaults[f"show_{pattern_key}"] = True
    return defaults


def normalize_chart_pattern_params(raw_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize Chart Pattern settings into safe runtime values."""
    defaults = get_default_chart_pattern_params()
    raw_params = raw_params or {}

    def _coerce_int(name: str, minimum: int) -> int:
        try:
            value = int(raw_params.get(name, defaults[name]))
        except (TypeError, ValueError):
            value = int(defaults[name])
        return max(value, minimum)

    normalized: dict[str, Any] = {
        "lookback": _coerce_int("lookback", 80),
        "pivot_window": min(_coerce_int("pivot_window", 2), 12),
        "tolerance_pct": min(_coerce_int("tolerance_pct", 1), 20),
    }
    for pattern_key in ALL_CHART_PATTERN_KEYS:
        param_key = f"show_{pattern_key}"
        normalized[param_key] = bool(raw_params.get(param_key, defaults[param_key]))
    return normalized


def _prepare_source_frame(data: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Prepare a numeric OHLCV frame for chart-pattern analysis."""
    if data is None or data.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    prepared = data[["time", "open", "high", "low", "close", "volume"]].copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared["volume"] = prepared["volume"].fillna(0.0)
    prepared = prepared.dropna(subset=["time", "open", "high", "low", "close"])
    prepared = prepared.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    return prepared.tail(lookback).reset_index(drop=True)


def _price_similarity(first: float, second: float) -> float:
    """Return percentage distance between two price points."""
    denominator = max(abs(first), abs(second), 1e-9)
    return abs(first - second) / denominator * 100.0


def _build_pivots(frame: pd.DataFrame, window: int) -> list[dict[str, Any]]:
    """Return local pivot highs and lows used by the chart-pattern heuristics."""
    pivots: list[dict[str, Any]] = []
    if len(frame) < (window * 2) + 1:
        return pivots

    for index in range(window, len(frame) - window):
        high_value = float(frame["high"].iloc[index])
        low_value = float(frame["low"].iloc[index])
        high_slice = frame["high"].iloc[index - window : index + window + 1]
        low_slice = frame["low"].iloc[index - window : index + window + 1]
        if high_value >= float(high_slice.max()):
            pivots.append(
                {
                    "type": "high",
                    "index": index,
                    "time": frame["time"].iloc[index],
                    "price": high_value,
                }
            )
        if low_value <= float(low_slice.min()):
            pivots.append(
                {
                    "type": "low",
                    "index": index,
                    "time": frame["time"].iloc[index],
                    "price": low_value,
                }
            )

    pivots.sort(key=lambda pivot: (int(pivot["index"]), 0 if pivot["type"] == "high" else 1))
    deduped: list[dict[str, Any]] = []
    for pivot in pivots:
        if deduped and deduped[-1]["index"] == pivot["index"] and deduped[-1]["type"] == pivot["type"]:
            if pivot["type"] == "high" and pivot["price"] > deduped[-1]["price"]:
                deduped[-1] = pivot
            elif pivot["type"] == "low" and pivot["price"] < deduped[-1]["price"]:
                deduped[-1] = pivot
            continue
        deduped.append(pivot)
    return deduped


def _candidate(
    pattern_key: str,
    label_time: pd.Timestamp,
    label_price: float,
    points: list[dict[str, Any]],
    lines: list[dict[str, Any]] | None = None,
    extra_lines: list[str] | None = None,
) -> dict[str, Any]:
    """Build one chart-pattern candidate object."""
    meta = CHART_PATTERN_DEFINITIONS[pattern_key]
    start_time = points[0]["time"]
    end_time = points[-1]["time"]
    return {
        "pattern_key": pattern_key,
        "label": meta["label"],
        "short_label": meta["short_label"],
        "description": meta["description"],
        "direction": meta["direction"],
        "label_time": label_time,
        "label_price": label_price,
        "start_time": start_time,
        "end_time": end_time,
        "points": points,
        "lines": lines or [],
        "detail_lines": extra_lines or [],
    }


def _detect_double_top(pivots: list[dict[str, Any]], tolerance_pct: float) -> dict[str, Any] | None:
    for index in range(len(pivots) - 3, -1, -1):
        window = pivots[index : index + 3]
        if len(window) < 3 or [pivot["type"] for pivot in window] != ["high", "low", "high"]:
            continue
        left_high, neckline, right_high = window
        if _price_similarity(float(left_high["price"]), float(right_high["price"])) > tolerance_pct:
            continue
        if float(neckline["price"]) >= min(float(left_high["price"]), float(right_high["price"])) * 0.97:
            continue
        return _candidate(
            "double_top",
            label_time=right_high["time"],
            label_price=float(right_high["price"]),
            points=window,
            lines=[
                {
                    "start_time": left_high["time"],
                    "start_value": neckline["price"],
                    "end_time": right_high["time"],
                    "end_value": neckline["price"],
                }
            ],
            extra_lines=[
                f"Puncak 1 {float(left_high['price']):.2f}",
                f"Puncak 2 {float(right_high['price']):.2f}",
                f"Neckline {float(neckline['price']):.2f}",
            ],
        )
    return None


def _detect_double_bottom(pivots: list[dict[str, Any]], tolerance_pct: float) -> dict[str, Any] | None:
    for index in range(len(pivots) - 3, -1, -1):
        window = pivots[index : index + 3]
        if len(window) < 3 or [pivot["type"] for pivot in window] != ["low", "high", "low"]:
            continue
        left_low, neckline, right_low = window
        if _price_similarity(float(left_low["price"]), float(right_low["price"])) > tolerance_pct:
            continue
        if float(neckline["price"]) <= max(float(left_low["price"]), float(right_low["price"])) * 1.03:
            continue
        return _candidate(
            "double_bottom",
            label_time=right_low["time"],
            label_price=float(right_low["price"]),
            points=window,
            lines=[
                {
                    "start_time": left_low["time"],
                    "start_value": neckline["price"],
                    "end_time": right_low["time"],
                    "end_value": neckline["price"],
                }
            ],
            extra_lines=[
                f"Bottom 1 {float(left_low['price']):.2f}",
                f"Bottom 2 {float(right_low['price']):.2f}",
                f"Neckline {float(neckline['price']):.2f}",
            ],
        )
    return None


def _detect_head_shoulders(pivots: list[dict[str, Any]], tolerance_pct: float) -> dict[str, Any] | None:
    for index in range(len(pivots) - 5, -1, -1):
        window = pivots[index : index + 5]
        if len(window) < 5 or [pivot["type"] for pivot in window] != ["high", "low", "high", "low", "high"]:
            continue
        left_shoulder, left_neck, head, right_neck, right_shoulder = window
        if float(head["price"]) <= max(float(left_shoulder["price"]), float(right_shoulder["price"])) * 1.02:
            continue
        if _price_similarity(float(left_shoulder["price"]), float(right_shoulder["price"])) > tolerance_pct * 1.4:
            continue
        return _candidate(
            "head_shoulders",
            label_time=right_shoulder["time"],
            label_price=float(right_shoulder["price"]),
            points=window,
            lines=[
                {
                    "start_time": left_neck["time"],
                    "start_value": left_neck["price"],
                    "end_time": right_neck["time"],
                    "end_value": right_neck["price"],
                }
            ],
            extra_lines=[
                f"Shoulder kiri {float(left_shoulder['price']):.2f}",
                f"Head {float(head['price']):.2f}",
                f"Shoulder kanan {float(right_shoulder['price']):.2f}",
            ],
        )
    return None


def _detect_inverse_head_shoulders(pivots: list[dict[str, Any]], tolerance_pct: float) -> dict[str, Any] | None:
    for index in range(len(pivots) - 5, -1, -1):
        window = pivots[index : index + 5]
        if len(window) < 5 or [pivot["type"] for pivot in window] != ["low", "high", "low", "high", "low"]:
            continue
        left_shoulder, left_neck, head, right_neck, right_shoulder = window
        if float(head["price"]) >= min(float(left_shoulder["price"]), float(right_shoulder["price"])) * 0.98:
            continue
        if _price_similarity(float(left_shoulder["price"]), float(right_shoulder["price"])) > tolerance_pct * 1.4:
            continue
        return _candidate(
            "inverse_head_shoulders",
            label_time=right_shoulder["time"],
            label_price=float(right_shoulder["price"]),
            points=window,
            lines=[
                {
                    "start_time": left_neck["time"],
                    "start_value": left_neck["price"],
                    "end_time": right_neck["time"],
                    "end_value": right_neck["price"],
                }
            ],
            extra_lines=[
                f"Shoulder kiri {float(left_shoulder['price']):.2f}",
                f"Head {float(head['price']):.2f}",
                f"Shoulder kanan {float(right_shoulder['price']):.2f}",
            ],
        )
    return None


def _detect_triangle_family(pivots: list[dict[str, Any]], tolerance_pct: float) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    high_pivots = [pivot for pivot in pivots if pivot["type"] == "high"][-3:]
    low_pivots = [pivot for pivot in pivots if pivot["type"] == "low"][-3:]
    if len(high_pivots) < 2 or len(low_pivots) < 2:
        return candidates

    first_high, last_high = high_pivots[0], high_pivots[-1]
    first_low, last_low = low_pivots[0], low_pivots[-1]
    resistance_flat = _price_similarity(float(first_high["price"]), float(last_high["price"])) <= tolerance_pct
    support_flat = _price_similarity(float(first_low["price"]), float(last_low["price"])) <= tolerance_pct
    higher_lows = float(last_low["price"]) > float(first_low["price"]) * 1.01
    lower_highs = float(last_high["price"]) < float(first_high["price"]) * 0.99

    common_points = [first_high, last_high, first_low, last_low]
    if resistance_flat and higher_lows:
        candidates.append(
            _candidate(
                "ascending_triangle",
                label_time=max(last_high["time"], last_low["time"]),
                label_price=float(last_high["price"]),
                points=common_points,
                lines=[
                    {
                        "start_time": first_high["time"],
                        "start_value": first_high["price"],
                        "end_time": last_high["time"],
                        "end_value": last_high["price"],
                    },
                    {
                        "start_time": first_low["time"],
                        "start_value": first_low["price"],
                        "end_time": last_low["time"],
                        "end_value": last_low["price"],
                    },
                ],
                extra_lines=["Resistance datar", "Support naik"],
            )
        )
    if support_flat and lower_highs:
        candidates.append(
            _candidate(
                "descending_triangle",
                label_time=max(last_high["time"], last_low["time"]),
                label_price=float(last_high["price"]),
                points=common_points,
                lines=[
                    {
                        "start_time": first_low["time"],
                        "start_value": first_low["price"],
                        "end_time": last_low["time"],
                        "end_value": last_low["price"],
                    },
                    {
                        "start_time": first_high["time"],
                        "start_value": first_high["price"],
                        "end_time": last_high["time"],
                        "end_value": last_high["price"],
                    },
                ],
                extra_lines=["Support datar", "Resistance turun"],
            )
        )
    if higher_lows and lower_highs:
        candidates.append(
            _candidate(
                "symmetrical_triangle",
                label_time=max(last_high["time"], last_low["time"]),
                label_price=max(float(last_high["price"]), float(last_low["price"])),
                points=common_points,
                lines=[
                    {
                        "start_time": first_high["time"],
                        "start_value": first_high["price"],
                        "end_time": last_high["time"],
                        "end_value": last_high["price"],
                    },
                    {
                        "start_time": first_low["time"],
                        "start_value": first_low["price"],
                        "end_time": last_low["time"],
                        "end_value": last_low["price"],
                    },
                ],
                extra_lines=["Lower high", "Higher low"],
            )
        )
    return candidates


def _detect_wedges(pivots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    high_pivots = [pivot for pivot in pivots if pivot["type"] == "high"][-3:]
    low_pivots = [pivot for pivot in pivots if pivot["type"] == "low"][-3:]
    if len(high_pivots) < 2 or len(low_pivots) < 2:
        return candidates

    first_high, last_high = high_pivots[0], high_pivots[-1]
    first_low, last_low = low_pivots[0], low_pivots[-1]
    high_slope = float(last_high["price"] - first_high["price"])
    low_slope = float(last_low["price"] - first_low["price"])
    converging = abs(high_slope) < abs(low_slope) if low_slope != 0 else False
    divergence = abs(high_slope) > abs(low_slope) if high_slope != 0 else False
    common_points = [first_high, last_high, first_low, last_low]

    if high_slope > 0 and low_slope > 0 and converging:
        candidates.append(
            _candidate(
                "rising_wedge",
                label_time=max(last_high["time"], last_low["time"]),
                label_price=float(last_high["price"]),
                points=common_points,
                lines=[
                    {
                        "start_time": first_high["time"],
                        "start_value": first_high["price"],
                        "end_time": last_high["time"],
                        "end_value": last_high["price"],
                    },
                    {
                        "start_time": first_low["time"],
                        "start_value": first_low["price"],
                        "end_time": last_low["time"],
                        "end_value": last_low["price"],
                    },
                ],
                extra_lines=["Kedua garis naik", "Makin menyempit"],
            )
        )
    if high_slope < 0 and low_slope < 0 and divergence:
        candidates.append(
            _candidate(
                "falling_wedge",
                label_time=max(last_high["time"], last_low["time"]),
                label_price=float(last_high["price"]),
                points=common_points,
                lines=[
                    {
                        "start_time": first_high["time"],
                        "start_value": first_high["price"],
                        "end_time": last_high["time"],
                        "end_value": last_high["price"],
                    },
                    {
                        "start_time": first_low["time"],
                        "start_value": first_low["price"],
                        "end_time": last_low["time"],
                        "end_value": last_low["price"],
                    },
                ],
                extra_lines=["Kedua garis turun", "Tekanan jual melemah"],
            )
        )
    return candidates


def _detect_cup_handle(frame: pd.DataFrame, tolerance_pct: float) -> dict[str, Any] | None:
    if len(frame) < 40:
        return None

    first_segment = frame.iloc[: max(len(frame) // 3, 10)]
    middle_segment = frame.iloc[len(frame) // 4 : (len(frame) * 3) // 4]
    last_segment = frame.iloc[(len(frame) * 2) // 3 :]
    if first_segment.empty or middle_segment.empty or last_segment.empty:
        return None

    left_rim_index = int(first_segment["high"].idxmax())
    cup_low_index = int(middle_segment["low"].idxmin())
    right_rim_index = int(last_segment["high"].idxmax())
    if not (left_rim_index < cup_low_index < right_rim_index):
        return None

    left_rim = float(frame.loc[left_rim_index, "high"])
    cup_low = float(frame.loc[cup_low_index, "low"])
    right_rim = float(frame.loc[right_rim_index, "high"])
    if _price_similarity(left_rim, right_rim) > tolerance_pct * 1.4:
        return None
    if cup_low >= min(left_rim, right_rim) * 0.94:
        return None

    handle_frame = frame.iloc[right_rim_index:]
    if len(handle_frame) < 4:
        return None
    handle_low = float(handle_frame["low"].min())
    cup_depth = min(left_rim, right_rim) - cup_low
    handle_pullback = min(left_rim, right_rim) - handle_low
    if handle_pullback <= 0 or handle_pullback >= cup_depth * 0.55:
        return None

    left_point = {
        "type": "high",
        "index": left_rim_index,
        "time": frame.loc[left_rim_index, "time"],
        "price": left_rim,
    }
    low_point = {
        "type": "low",
        "index": cup_low_index,
        "time": frame.loc[cup_low_index, "time"],
        "price": cup_low,
    }
    right_point = {
        "type": "high",
        "index": right_rim_index,
        "time": frame.loc[right_rim_index, "time"],
        "price": right_rim,
    }
    handle_point = {
        "type": "low",
        "index": int(handle_frame["low"].idxmin()),
        "time": frame.loc[int(handle_frame["low"].idxmin()), "time"],
        "price": handle_low,
    }

    return _candidate(
        "cup_handle",
        label_time=handle_point["time"],
        label_price=right_rim,
        points=[left_point, low_point, right_point, handle_point],
        lines=[
            {
                "start_time": left_point["time"],
                "start_value": left_rim,
                "end_time": right_point["time"],
                "end_value": right_rim,
            }
        ],
        extra_lines=[
            f"Rim {left_rim:.2f} / {right_rim:.2f}",
            f"Cup low {cup_low:.2f}",
            f"Handle low {handle_low:.2f}",
        ],
    )


def detect_chart_patterns(
    data: pd.DataFrame,
    raw_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Detect major chart patterns from the active OHLCV range."""
    params = normalize_chart_pattern_params(raw_params)
    frame = _prepare_source_frame(data, int(params["lookback"]))
    if frame.empty:
        return []

    tolerance_pct = float(params["tolerance_pct"])
    pivots = _build_pivots(frame, int(params["pivot_window"]))
    candidates: list[dict[str, Any]] = []

    if params["show_double_top"]:
        candidate = _detect_double_top(pivots, tolerance_pct)
        if candidate is not None:
            candidates.append(candidate)
    if params["show_double_bottom"]:
        candidate = _detect_double_bottom(pivots, tolerance_pct)
        if candidate is not None:
            candidates.append(candidate)
    if params["show_head_shoulders"]:
        candidate = _detect_head_shoulders(pivots, tolerance_pct)
        if candidate is not None:
            candidates.append(candidate)
    if params["show_inverse_head_shoulders"]:
        candidate = _detect_inverse_head_shoulders(pivots, tolerance_pct)
        if candidate is not None:
            candidates.append(candidate)
    triangle_candidates = _detect_triangle_family(pivots, tolerance_pct)
    for candidate in triangle_candidates:
        if params.get(f"show_{candidate['pattern_key']}", True):
            candidates.append(candidate)
    wedge_candidates = _detect_wedges(pivots)
    for candidate in wedge_candidates:
        if params.get(f"show_{candidate['pattern_key']}", True):
            candidates.append(candidate)
    if params["show_cup_handle"]:
        candidate = _detect_cup_handle(frame, tolerance_pct)
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(key=lambda item: item["end_time"])
    return candidates


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
            "date_label": format_short_date_label(latest["end_time"]),
            "detail_lines": latest.get("detail_lines") or [],
        }

    summary_rows = [
        {
            "label": pattern["label"],
            "short_label": pattern["short_label"],
            "description": pattern["description"],
            "direction": pattern["direction"],
            "date_label": format_short_date_label(pattern["end_time"]),
            "detail_lines": pattern.get("detail_lines") or [],
        }
        for pattern in patterns
    ]
    return {
        "patterns": summary_rows,
        "latest_by_direction": latest_by_direction,
        "total_patterns": int(len(patterns)),
    }


