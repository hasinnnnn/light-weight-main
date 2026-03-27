from __future__ import annotations

from typing import Any

from indicators.candle_patterns import (
    get_default_candle_pattern_params,
    normalize_candle_pattern_params,
)
from indicators.chart_patterns import (
    get_default_chart_pattern_params,
    normalize_chart_pattern_params,
)
from indicators.consolidation_areas import (
    get_default_consolidation_area_params,
    normalize_consolidation_area_params,
)
from indicators.fibonacci import FIBONACCI_SWING_MODE_SHORT_LABELS
from indicators.specs.color_presets import COLOR_PRESET_GRID
from indicators.specs.fibonacci_spec import FIBONACCI_INDICATOR_SPEC
from indicators.specs.overlay_specs import OVERLAY_INDICATOR_SPECS
from indicators.specs.panel_specs import PANEL_AND_MISC_INDICATOR_SPECS
from indicators.specs.pattern_specs import PATTERN_AND_STRUCTURE_INDICATOR_SPECS

INDICATOR_CATALOG = [
    *OVERLAY_INDICATOR_SPECS,
    FIBONACCI_INDICATOR_SPEC,
    *PATTERN_AND_STRUCTURE_INDICATOR_SPECS,
    *PANEL_AND_MISC_INDICATOR_SPECS,
]
INDICATOR_CATALOG_BY_KEY = {item["key"]: item for item in INDICATOR_CATALOG}
def _coerce_positive_integer(value: Any, fallback: int) -> int:
    """Convert a raw field value into a positive integer."""
    try:
        normalized_value = int(value)
    except (TypeError, ValueError):
        normalized_value = int(fallback)
    return max(normalized_value, 1)



def _coerce_positive_float(value: Any, fallback: float, minimum: float = 0.0) -> float:
    """Convert a raw field value into a positive float."""
    try:
        normalized_value = float(value)
    except (TypeError, ValueError):
        normalized_value = float(fallback)
    return max(normalized_value, float(minimum))

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


def default_indicator_params(indicator_key: str) -> dict[str, Any]:
    """Return a clean default parameter dictionary for one indicator type."""
    if indicator_key == "CANDLE_PATTERN":
        return get_default_candle_pattern_params()
    if indicator_key == "CHART_PATTERN":
        return get_default_chart_pattern_params()
    if indicator_key == "CONSOLIDATION_AREA":
        return get_default_consolidation_area_params()
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    default_params: dict[str, Any] = {}
    for field in indicator["fields"]:
        if field.get("input_type") == "select" or field.get("options"):
            default_params[field["name"]] = str(field["default"])
        elif str(field.get("value_type", "")).strip().lower() == "float" or isinstance(field.get("default"), float):
            default_params[field["name"]] = float(field["default"] )
        else:
            default_params[field["name"]] = int(field["default"])
    return default_params


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
) -> dict[str, Any]:
    """Normalize indicator params so the chart always receives valid values."""
    if indicator_key == "CANDLE_PATTERN":
        return normalize_candle_pattern_params(raw_params)
    if indicator_key == "CHART_PATTERN":
        return normalize_chart_pattern_params(raw_params)
    if indicator_key == "CONSOLIDATION_AREA":
        return normalize_consolidation_area_params(raw_params)

    raw_params = raw_params or {}
    indicator = INDICATOR_CATALOG_BY_KEY[indicator_key]
    normalized_params = {}
    for field in indicator["fields"]:
        field_name = field["name"]
        if field.get("input_type") == "select" or field.get("options"):
            allowed_values = [
                str(option.get("value") if isinstance(option, dict) else option)
                for option in field.get("options", [])
            ]
            default_value = str(field["default"])
            raw_value = str(raw_params.get(field_name, default_value))
            normalized_params[field_name] = raw_value if raw_value in allowed_values else default_value
        elif str(field.get("value_type", "")).strip().lower() == "float" or isinstance(field.get("default"), float):
            normalized_params[field_name] = _coerce_positive_float(
                raw_params.get(field_name),
                float(field["default"]),
                float(field.get("min_value", 0.0)),
            )
        else:
            normalized_params[field_name] = max(
                _coerce_positive_integer(raw_params.get(field_name), int(field["default"])),
                int(field.get("min_value", 1)),
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
        if indicator_key == "TRENDLINE":
            normalized_params["max_trendlines"] = min(
                max(normalized_params.get("max_trendlines", 3), 1),
                6,
            )
    elif indicator_key == "MAJOR_TRENDLINE":
        normalized_params["lookback"] = max(normalized_params["lookback"], 60)
        normalized_params["swing_window"] = min(
            max(normalized_params["swing_window"], 2),
            max(normalized_params["lookback"] // 6, 2),
        )
        normalized_params["max_trendlines"] = min(
            max(normalized_params.get("max_trendlines", 3), 1),
            6,
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


def format_indicator_instance_label(indicator: dict[str, Any]) -> str:
    """Build the compact indicator name shown in the active-indicator controls."""
    custom_display_label = str(indicator.get("display_label") or "").strip()
    if custom_display_label:
        return custom_display_label

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
    if indicator_key == "CANDLE_PATTERN":
        return f"Candle Pattern {params['lookback']}"
    if indicator_key == "CHART_PATTERN":
        return (
            f"Chart Pattern {params['lookback']} / "
            f"{params['pivot_window']} / {params['tolerance_pct']}%"
        )
    if indicator_key == "CONSOLIDATION_AREA":
        return (
            f"Area Konsolidasi {params['lookback']} / "
            f"{params['consolidation_bars']} / {params['max_zones']}"
        )
    if indicator_key == "TRENDLINE":
        return f"Minor Trend {params['lookback']} / {params['swing_window']} / {params['max_trendlines']}"
    if indicator_key == "MAJOR_TRENDLINE":
        return f"Major Trend {params['lookback']} / {params['swing_window']} / {params['max_trendlines']}"
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
        direction_label = "L->H" if params["swing_direction"] == "low_to_high" else "H->L"
        mode_key = str(params.get("swing_mode", "balanced")).strip().lower()
        mode_label = FIBONACCI_SWING_MODE_SHORT_LABELS.get(mode_key, "Bal")
        return f"Fibonacci {params['lookback']} / {direction_label} / {mode_label}"
    if indicator_key == "PIVOT_POINT_STANDARD":
        return "Pivot Point Standard"
    return indicator_key













