from __future__ import annotations

from typing import Any

INDICATOR_CATALOG = [
    {
        "key": "EMA",
        "modal_label": "EMA (Exponential Moving Average)",
        "description": "Satu garis EMA yang tampil di chart harga.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length",
                "label": "Panjang EMA",
                "default": 10,
                "min_value": 1,
            }
        ],
        "color_fields": [
            {"name": "line", "label": "EMA", "default": "#38bdf8"},
        ],
    },
    {
        "key": "EMA_CROSS",
        "modal_label": "EMA Cross",
        "description": "Dua garis EMA cepat dan lambat untuk melihat area cross.",
        "placement": "overlay",
        "fields": [
            {
                "name": "fast_length",
                "label": "Panjang EMA Cepat",
                "default": 9,
                "min_value": 1,
            },
            {
                "name": "slow_length",
                "label": "Panjang EMA Lambat",
                "default": 21,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "fast", "label": "EMA Cepat", "default": "#38bdf8"},
            {"name": "slow", "label": "EMA Lambat", "default": "#f59e0b"},
            {"name": "cross", "label": "Cross", "default": "#f8fafc"},
        ],
    },
    {
        "key": "DOUBLE_EMA",
        "modal_label": "Double EMA",
        "description": "Dua garis EMA dengan panjang yang bisa diatur terpisah.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length_one",
                "label": "Panjang EMA 1",
                "default": 20,
                "min_value": 1,
            },
            {
                "name": "length_two",
                "label": "Panjang EMA 2",
                "default": 50,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "line_one", "label": "EMA 1", "default": "#38bdf8"},
            {"name": "line_two", "label": "EMA 2", "default": "#f59e0b"},
        ],
    },
    {
        "key": "TRIPLE_EMA",
        "modal_label": "Triple EMA",
        "description": "Tiga garis EMA untuk setup trend bertingkat.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length_one",
                "label": "Panjang EMA 1",
                "default": 5,
                "min_value": 1,
            },
            {
                "name": "length_two",
                "label": "Panjang EMA 2",
                "default": 10,
                "min_value": 1,
            },
            {
                "name": "length_three",
                "label": "Panjang EMA 3",
                "default": 20,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "line_one", "label": "EMA 1", "default": "#38bdf8"},
            {"name": "line_two", "label": "EMA 2", "default": "#f59e0b"},
            {"name": "line_three", "label": "EMA 3", "default": "#22c55e"},
        ],
    },
    {
        "key": "MA",
        "modal_label": "MA (Moving Average)",
        "description": "Satu garis moving average biasa di chart harga.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length",
                "label": "Panjang MA",
                "default": 20,
                "min_value": 1,
            }
        ],
        "color_fields": [
            {"name": "line", "label": "MA", "default": "#fb923c"},
        ],
    },
    {
        "key": "MA_CROSS",
        "modal_label": "MA Cross",
        "description": "Dua garis MA cepat dan lambat untuk membaca cross.",
        "placement": "overlay",
        "fields": [
            {
                "name": "fast_length",
                "label": "Panjang MA Cepat",
                "default": 20,
                "min_value": 1,
            },
            {
                "name": "slow_length",
                "label": "Panjang MA Lambat",
                "default": 50,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "fast", "label": "MA Cepat", "default": "#fb923c"},
            {"name": "slow", "label": "MA Lambat", "default": "#a855f7"},
            {"name": "cross", "label": "Cross", "default": "#f8fafc"},
        ],
    },
    {
        "key": "DOUBLE_MA",
        "modal_label": "Double MA",
        "description": "Dua garis moving average biasa dengan panjang terpisah.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length_one",
                "label": "Panjang MA 1",
                "default": 20,
                "min_value": 1,
            },
            {
                "name": "length_two",
                "label": "Panjang MA 2",
                "default": 50,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "line_one", "label": "MA 1", "default": "#fb923c"},
            {"name": "line_two", "label": "MA 2", "default": "#a855f7"},
        ],
    },
    {
        "key": "TRIPLE_MA",
        "modal_label": "Triple MA",
        "description": "Tiga garis moving average biasa untuk trend bertingkat.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length_one",
                "label": "Panjang MA 1",
                "default": 10,
                "min_value": 1,
            },
            {
                "name": "length_two",
                "label": "Panjang MA 2",
                "default": 20,
                "min_value": 1,
            },
            {
                "name": "length_three",
                "label": "Panjang MA 3",
                "default": 50,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "line_one", "label": "MA 1", "default": "#fb923c"},
            {"name": "line_two", "label": "MA 2", "default": "#a855f7"},
            {"name": "line_three", "label": "MA 3", "default": "#14b8a6"},
        ],
    },
    {
        "key": "BOLLINGER_BANDS",
        "modal_label": "Bollinger Bands",
        "description": "Upper band, basis, dan lower band dari volatilitas harga.",
        "placement": "overlay",
        "fields": [
            {
                "name": "length",
                "label": "Panjang Bollinger",
                "default": 20,
                "min_value": 1,
            },
            {
                "name": "deviation",
                "label": "Deviasi",
                "default": 2,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "upper", "label": "Upper Band", "default": "#60a5fa"},
            {"name": "basis", "label": "Basis", "default": "#f8fafc"},
            {"name": "lower", "label": "Lower Band", "default": "#f472b6"},
        ],
    },
    {
        "key": "VWAP",
        "modal_label": "VWAP",
        "description": "Volume Weighted Average Price untuk membaca harga rata-rata berbobot volume.",
        "placement": "overlay",
        "fields": [],
        "color_fields": [
            {"name": "line", "label": "VWAP", "default": "#fbbf24"},
        ],
    },
    {
        "key": "PARABOLIC_SAR",
        "modal_label": "Parabolic SAR",
        "description": "Parabolic SAR standar untuk membaca arah trend dan titik pembalikan harga.",
        "placement": "overlay",
        "fields": [],
        "color_fields": [
            {"name": "line", "label": "Parabolic SAR", "default": "#38bdf8"},
        ],
    },
    {
        "key": "TRENDLINE",
        "modal_label": "Trendline Kecil (Minor Trend)",
        "description": (
            "Trendline minor untuk membaca pergerakan jangka pendek dari pivot terbaru "
            "di ujung chart, bisa naik atau turun."
        ),
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback",
                "default": 80,
                "min_value": 20,
            },
            {
                "name": "swing_window",
                "label": "Sensitivitas Pivot",
                "default": 3,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "up", "label": "Trendline Naik", "default": "#22c55e"},
            {"name": "down", "label": "Trendline Turun", "default": "#ef4444"},
        ],
    },
    {
        "key": "MAJOR_TRENDLINE",
        "modal_label": "Trendline Besar (Major Trend)",
        "description": (
            "Trendline besar dari chart weekly atau daily untuk membaca arah tren utama "
            "selama berbulan-bulan hingga bertahun-tahun. Lebih valid dan kuat."
        ),
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback Major",
                "default": 260,
                "min_value": 60,
            },
            {
                "name": "swing_window",
                "label": "Sensitivitas Pivot Major",
                "default": 4,
                "min_value": 2,
            },
        ],
        "color_fields": [
            {"name": "up", "label": "Major Trend Naik", "default": "#22c55e"},
            {"name": "down", "label": "Major Trend Turun", "default": "#ef4444"},
        ],
    },
    {
        "key": "NEAREST_SUPPORT_RESISTANCE",
        "modal_label": "Support & Resistance Terdekat",
        "description": (
            "Mencari area support dan resistance terdekat dari harga terbaru, "
            "lengkap dengan jumlah pantulan."
        ),
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback",
                "default": 120,
                "min_value": 20,
            },
            {
                "name": "swing_window",
                "label": "Sensitivitas Pivot",
                "default": 3,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "resistance", "label": "Resistance", "default": "#22c55e"},
            {"name": "support", "label": "Support", "default": "#ef4444"},
        ],
    },
    {
        "key": "STRONG_SUPPORT_RESISTANCE",
        "modal_label": "Support & Resistance Kuat",
        "description": (
            "Area support dan resistance kuat dari swing signifikan, "
            "minimal 2-3 pantulan, gagal breakout, dan didukung reversal volume besar."
        ),
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback HTF",
                "default": 160,
                "min_value": 40,
            },
            {
                "name": "swing_window",
                "label": "Sensitivitas Swing",
                "default": 3,
                "min_value": 1,
            },
            {
                "name": "min_bounces",
                "label": "Minimal Pantulan",
                "default": 3,
                "min_value": 2,
            },
        ],
        "color_fields": [
            {"name": "resistance", "label": "Resistance Kuat", "default": "#22c55e"},
            {"name": "support", "label": "Support Kuat", "default": "#ef4444"},
        ],
    },
    {
        "key": "RSI",
        "modal_label": "RSI",
        "description": "Relative Strength Index dengan level 30 dan 70.",
        "placement": "panel",
        "fields": [
            {
                "name": "length",
                "label": "Panjang RSI",
                "default": 14,
                "min_value": 1,
            }
        ],
        "color_fields": [
            {"name": "line", "label": "RSI", "default": "#a78bfa"},
        ],
    },
    {
        "key": "ATR",
        "modal_label": "ATR (Average True Range)",
        "description": "Average True Range untuk membaca besar kecilnya volatilitas harga.",
        "placement": "panel",
        "fields": [
            {
                "name": "length",
                "label": "Panjang ATR",
                "default": 14,
                "min_value": 1,
            }
        ],
        "color_fields": [
            {"name": "line", "label": "ATR", "default": "#f59e0b"},
        ],
    },
    {
        "key": "PRICE_OSCILLATOR",
        "modal_label": "Price Oscillator",
        "description": "Selisih EMA cepat dan EMA lambat untuk membaca momentum harga.",
        "placement": "panel",
        "fields": [
            {
                "name": "fast_length",
                "label": "Panjang Fast",
                "default": 12,
                "min_value": 1,
            },
            {
                "name": "slow_length",
                "label": "Panjang Slow",
                "default": 26,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "line", "label": "Price Oscillator", "default": "#38bdf8"},
        ],
    },
    {
        "key": "MACD",
        "modal_label": "MACD",
        "description": "MACD line, signal line, dan histogram momentum.",
        "placement": "panel",
        "fields": [
            {
                "name": "fast_length",
                "label": "Panjang Fast",
                "default": 12,
                "min_value": 1,
            },
            {
                "name": "slow_length",
                "label": "Panjang Slow",
                "default": 26,
                "min_value": 1,
            },
            {
                "name": "signal_length",
                "label": "Panjang Signal",
                "default": 9,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "macd", "label": "MACD", "default": "#38bdf8"},
            {"name": "signal", "label": "Signal", "default": "#f59e0b"},
            {"name": "cross", "label": "Cross", "default": "#f8fafc"},
            {"name": "histogram_up", "label": "Histogram Naik", "default": "#22c55e"},
            {"name": "histogram_down", "label": "Histogram Turun", "default": "#ef4444"},
        ],
    },
    {
        "key": "STOCHASTIC",
        "modal_label": "Stochastic",
        "description": "Oscillator %K dan %D untuk membaca momentum harga.",
        "placement": "panel",
        "fields": [
            {
                "name": "k_length",
                "label": "Panjang %K",
                "default": 14,
                "min_value": 1,
            },
            {
                "name": "k_smoothing",
                "label": "Smoothing %K",
                "default": 3,
                "min_value": 1,
            },
            {
                "name": "d_length",
                "label": "Panjang %D",
                "default": 3,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "k", "label": "%K", "default": "#38bdf8"},
            {"name": "d", "label": "%D", "default": "#f59e0b"},
        ],
    },
    {
        "key": "STOCHASTIC_RSI",
        "modal_label": "Stochastic RSI",
        "description": "Stochastic yang dihitung dari RSI untuk membaca momentum lebih sensitif.",
        "placement": "panel",
        "fields": [
            {
                "name": "rsi_length",
                "label": "Panjang RSI",
                "default": 14,
                "min_value": 1,
            },
            {
                "name": "stoch_length",
                "label": "Panjang Stochastic",
                "default": 14,
                "min_value": 1,
            },
            {
                "name": "k_smoothing",
                "label": "Smoothing %K",
                "default": 3,
                "min_value": 1,
            },
            {
                "name": "d_length",
                "label": "Panjang %D",
                "default": 3,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "k", "label": "%K", "default": "#38bdf8"},
            {"name": "d", "label": "%D", "default": "#f59e0b"},
        ],
    },
    {
        "key": "FIBONACCI",
        "modal_label": "Fibonacci",
        "description": "Level retracement Fibonacci dari range harga terbaru.",
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback",
                "default": 120,
                "min_value": 5,
            }
        ],
        "color_fields": [
            {"name": "line", "label": "Fibonacci", "default": "#60a5fa"},
        ],
    },
    {
        "key": "PIVOT_POINT_STANDARD",
        "modal_label": "Pivot Point Standard",
        "description": "Pivot point standard beserta support dan resistance utama.",
        "placement": "overlay",
        "fields": [],
        "color_fields": [
            {"name": "line", "label": "Pivot Point", "default": "#f8fafc"},
        ],
    },
]
INDICATOR_CATALOG_BY_KEY = {item["key"]: item for item in INDICATOR_CATALOG}
COLOR_PRESET_GRID = [
    ["#ffffff", "#e5e7eb", "#d1d5db", "#9ca3af", "#6b7280", "#374151", "#111827"],
    ["#fca5a5", "#fb7185", "#ef4444", "#dc2626", "#f59e0b", "#fbbf24", "#fde047"],
    ["#fef3c7", "#fde68a", "#fcd34d", "#86efac", "#4ade80", "#22c55e", "#15803d"],
    ["#d1fae5", "#99f6e4", "#5eead4", "#2dd4bf", "#67e8f9", "#22d3ee", "#06b6d4"],
    ["#bfdbfe", "#93c5fd", "#60a5fa", "#38bdf8", "#3b82f6", "#2563eb", "#1d4ed8"],
    ["#ddd6fe", "#c4b5fd", "#a78bfa", "#8b5cf6", "#7c3aed", "#a855f7", "#c026d3"],
    ["#f5d0fe", "#f0abfc", "#e879f9", "#d946ef", "#ec4899", "#db2777", "#be185d"],
]


def _coerce_positive_integer(value: Any, fallback: int) -> int:
    """Convert a raw field value into a positive integer."""
    try:
        normalized_value = int(value)
    except (TypeError, ValueError):
        normalized_value = int(fallback)
    return max(normalized_value, 1)


def _normalize_hex_color(value: Any, fallback: str) -> str:
    """Convert a raw color value into a valid hex color."""
    if isinstance(value, str):
        normalized_value = value.strip()
        if (
            len(normalized_value) == 7
            and normalized_value.startswith("#")
            and all(character in "0123456789abcdefABCDEF" for character in normalized_value[1:])
        ):
            return normalized_value.lower()
    return fallback.lower()


def _normalize_ordered_values(values: list[int]) -> list[int]:
    """Sort period values and keep them strictly increasing."""
    normalized_values = sorted(max(int(value), 1) for value in values)
    result: list[int] = []
    for value in normalized_values:
        if result and value <= result[-1]:
            value = result[-1] + 1
        result.append(value)
    return result


def default_indicator_params(indicator_key: str) -> dict[str, int]:
    """Return a clean default parameter dictionary for one indicator type."""
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    return {field["name"]: int(field["default"]) for field in indicator["fields"]}


def default_indicator_colors(indicator_key: str) -> dict[str, str]:
    """Return a clean default color dictionary for one indicator type."""
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    return {
        field["name"]: str(field["default"]).lower()
        for field in indicator.get("color_fields", [])
    }


def normalize_indicator_params(
    indicator_key: str,
    raw_params: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Normalize indicator params so the chart always receives valid numbers."""
    raw_params = raw_params or {}
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    normalized_params = {}
    for field in indicator["fields"]:
        normalized_params[field["name"]] = _coerce_positive_integer(
            raw_params.get(field["name"]),
            int(field["default"]),
        )

    if indicator_key in {"EMA_CROSS", "MA_CROSS"}:
        fast_length, slow_length = _normalize_ordered_values(
            [normalized_params["fast_length"], normalized_params["slow_length"]]
        )
        normalized_params["fast_length"] = fast_length
        normalized_params["slow_length"] = slow_length
    elif indicator_key in {"DOUBLE_EMA", "DOUBLE_MA"}:
        length_one, length_two = _normalize_ordered_values(
            [normalized_params["length_one"], normalized_params["length_two"]]
        )
        normalized_params["length_one"] = length_one
        normalized_params["length_two"] = length_two
    elif indicator_key in {"TRIPLE_EMA", "TRIPLE_MA"}:
        length_one, length_two, length_three = _normalize_ordered_values(
            [
                normalized_params["length_one"],
                normalized_params["length_two"],
                normalized_params["length_three"],
            ]
        )
        normalized_params["length_one"] = length_one
        normalized_params["length_two"] = length_two
        normalized_params["length_three"] = length_three
    elif indicator_key in {"MACD", "PRICE_OSCILLATOR"}:
        fast_length, slow_length = _normalize_ordered_values(
            [normalized_params["fast_length"], normalized_params["slow_length"]]
        )
        normalized_params["fast_length"] = fast_length
        normalized_params["slow_length"] = slow_length
        if indicator_key == "MACD":
            normalized_params["signal_length"] = _coerce_positive_integer(
                normalized_params["signal_length"],
                default_indicator_params("MACD")["signal_length"],
            )
    elif indicator_key in {"TRENDLINE", "NEAREST_SUPPORT_RESISTANCE"}:
        normalized_params["lookback"] = max(normalized_params["lookback"], 20)
        normalized_params["swing_window"] = min(
            max(normalized_params["swing_window"], 1),
            max(normalized_params["lookback"] // 4, 1),
        )
    elif indicator_key == "MAJOR_TRENDLINE":
        normalized_params["lookback"] = max(normalized_params["lookback"], 60)
        normalized_params["swing_window"] = min(
            max(normalized_params["swing_window"], 2),
            max(normalized_params["lookback"] // 6, 2),
        )
    elif indicator_key == "STRONG_SUPPORT_RESISTANCE":
        normalized_params["lookback"] = max(normalized_params["lookback"], 40)
        normalized_params["swing_window"] = min(
            max(normalized_params["swing_window"], 1),
            max(normalized_params["lookback"] // 4, 1),
        )
        normalized_params["min_bounces"] = min(
            max(normalized_params["min_bounces"], 2),
            6,
        )

    return normalized_params


def normalize_indicator_colors(
    indicator_key: str,
    raw_colors: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Normalize indicator colors so the chart always receives valid hex values."""
    raw_colors = raw_colors or {}
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    normalized_colors = {}
    for field in indicator.get("color_fields", []):
        normalized_colors[field["name"]] = _normalize_hex_color(
            raw_colors.get(field["name"]),
            str(field["default"]),
        )
    return normalized_colors

def indicator_supports_edit(indicator_key: str) -> bool:
    """Return whether an indicator has editable parameters."""
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    return bool(indicator["fields"] or indicator.get("color_fields"))


def indicator_param_widget_key(indicator_id: str, field_name: str) -> str:
    """Build the widget key for one indicator parameter input."""
    return f"indicator_edit_{indicator_id}_{field_name}"


def indicator_color_widget_key(indicator_id: str, field_name: str) -> str:
    """Build the widget key for one indicator color input."""
    return f"indicator_color_{indicator_id}_{field_name}"


def clear_indicator_editor_draft(indicator_id: str) -> None:
    """Clear draft widgets for one indicator editor."""
    indicator = find_indicator(indicator_id)
    if indicator is None:
        return

    indicator_definition = INDICATOR_CATALOG_BY_KEY[indicator["key"]]
    for field in indicator_definition["fields"]:
        st.session_state.pop(indicator_param_widget_key(indicator_id, field["name"]), None)
    for color_field in indicator_definition.get("color_fields", []):
        st.session_state.pop(indicator_color_widget_key(indicator_id, color_field["name"]), None)


def select_indicator_color(widget_key: str, color_value: str) -> None:
    """Store a preset color selection for the current indicator editor."""
    st.session_state[widget_key] = color_value.lower()


def format_indicator_instance_label(indicator: dict[str, Any]) -> str:
    """Build the compact indicator name shown in the active-indicator controls."""
    indicator_key = indicator["key"]
    params = normalize_indicator_params(indicator_key, indicator.get("params"))

    if indicator_key == "EMA":
        return f"EMA {params['length']}"
    if indicator_key == "EMA_CROSS":
        return f"EMA Cross {params['fast_length']} / {params['slow_length']}"
    if indicator_key == "DOUBLE_EMA":
        return f"Double EMA {params['length_one']} / {params['length_two']}"
    if indicator_key == "TRIPLE_EMA":
        return (
            f"Triple EMA {params['length_one']} / "
            f"{params['length_two']} / {params['length_three']}"
        )
    if indicator_key == "MA":
        return f"MA {params['length']}"
    if indicator_key == "MA_CROSS":
        return f"MA Cross {params['fast_length']} / {params['slow_length']}"
    if indicator_key == "DOUBLE_MA":
        return f"Double MA {params['length_one']} / {params['length_two']}"
    if indicator_key == "TRIPLE_MA":
        return (
            f"Triple MA {params['length_one']} / "
            f"{params['length_two']} / {params['length_three']}"
        )
    if indicator_key == "BOLLINGER_BANDS":
        return f"Bollinger Bands {params['length']} / {params['deviation']}"
    if indicator_key == "VWAP":
        return "VWAP"
    if indicator_key == "PARABOLIC_SAR":
        return "Parabolic SAR"
    if indicator_key == "TRENDLINE":
        return f"Minor Trend {params['lookback']} / {params['swing_window']}"
    if indicator_key == "MAJOR_TRENDLINE":
        return f"Major Trend {params['lookback']} / {params['swing_window']}"
    if indicator_key == "NEAREST_SUPPORT_RESISTANCE":
        return f"S/R {params['lookback']} / {params['swing_window']}"
    if indicator_key == "STRONG_SUPPORT_RESISTANCE":
        return (
            f"Strong S/R {params['lookback']} / "
            f"{params['swing_window']} / {params['min_bounces']}"
        )
    if indicator_key == "ATR":
        return f"ATR {params['length']}"
    if indicator_key == "PRICE_OSCILLATOR":
        return f"Price Oscillator {params['fast_length']} / {params['slow_length']}"
    if indicator_key == "RSI":
        return f"RSI {params['length']}"
    if indicator_key == "MACD":
        return (
            f"MACD {params['fast_length']} / "
            f"{params['slow_length']} / {params['signal_length']}"
        )
    if indicator_key == "STOCHASTIC":
        return (
            f"Stochastic {params['k_length']} / "
            f"{params['k_smoothing']} / {params['d_length']}"
        )
    if indicator_key == "STOCHASTIC_RSI":
        return (
            f"Stochastic RSI {params['rsi_length']} / {params['stoch_length']} / "
            f"{params['k_smoothing']} / {params['d_length']}"
        )
    if indicator_key == "FIBONACCI":
        return f"Fibonacci {params['lookback']}"
    if indicator_key == "PIVOT_POINT_STANDARD":
        return "Pivot Point Standard"
    return indicator_key


