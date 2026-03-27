from __future__ import annotations

from typing import Any

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
    "triple_top": {
        "label": "Triple Top",
        "short_label": "TTOP",
        "description": "Tiga puncak di area resistance yang mirip, sering dibaca sebagai distribusi berkepanjangan dan risiko reversal turun.",
        "direction": "bearish",
    },
    "triple_bottom": {
        "label": "Triple Bottom",
        "short_label": "TBOT",
        "description": "Tiga lembah di area support yang mirip, sering dibaca sebagai akumulasi yang lebih kuat dan potensi reversal naik.",
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

