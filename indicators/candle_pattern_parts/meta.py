from __future__ import annotations

from typing import Any

CANDLE_PATTERN_DEFINITIONS: dict[str, dict[str, str]] = {
    "bullish_engulfing": {
        "label": "Bullish Engulfing",
        "short_label": "BU",
        "description": "Body candle bullish menelan body candle sebelumnya dan sering menandai reversal naik.",
        "direction": "bullish",
    },
    "bearish_engulfing": {
        "label": "Bearish Engulfing",
        "short_label": "BE",
        "description": "Body candle bearish menelan body candle sebelumnya dan sering menandai reversal turun.",
        "direction": "bearish",
    },
    "doji": {
        "label": "Doji",
        "short_label": "DJ",
        "description": "Body sangat kecil, menandakan kebimbangan pelaku pasar setelah pergerakan sebelumnya.",
        "direction": "neutral",
    },
    "hammer": {
        "label": "Hammer",
        "short_label": "HM",
        "description": "Ekor bawah panjang dengan body kecil, sering dibaca sebagai sinyal pantulan bullish.",
        "direction": "bullish",
    },
    "hanging_man": {
        "label": "Hanging Man",
        "short_label": "HGM",
        "description": "Bentuk mirip hammer di area atas tren naik dan sering mengisyaratkan tekanan jual mulai masuk.",
        "direction": "bearish",
    },
    "shooting_star": {
        "label": "Shooting Star",
        "short_label": "SS",
        "description": "Ekor atas panjang di area puncak, sering dibaca sebagai penolakan harga dan sinyal bearish.",
        "direction": "bearish",
    },
    "inverted_hammer": {
        "label": "Inverted Hammer",
        "short_label": "IH",
        "description": "Body kecil dengan ekor atas panjang setelah tekanan turun, menandakan minat beli mulai muncul.",
        "direction": "bullish",
    },
    "bullish_harami": {
        "label": "Bullish Harami",
        "short_label": "BH",
        "description": "Candle kecil bullish berada di dalam body bearish sebelumnya, menandakan pelemahan tekanan jual.",
        "direction": "bullish",
    },
    "bearish_harami": {
        "label": "Bearish Harami",
        "short_label": "BRH",
        "description": "Candle kecil bearish berada di dalam body bullish sebelumnya, menandakan pelemahan dorongan naik.",
        "direction": "bearish",
    },
    "piercing_line": {
        "label": "Piercing Line",
        "short_label": "PL",
        "description": "Candle bullish menutup lebih dari separuh body bearish sebelumnya dan sering dibaca sebagai reversal naik.",
        "direction": "bullish",
    },
    "dark_cloud_cover": {
        "label": "Dark Cloud Cover",
        "short_label": "DCC",
        "description": "Candle bearish menutup lebih dari separuh body bullish sebelumnya dan sering menandai reversal turun.",
        "direction": "bearish",
    },
    "morning_star": {
        "label": "Morning Star",
        "short_label": "MS",
        "description": "Pola tiga candle yang sering menandai akhir tekanan turun dan awal pemulihan bullish.",
        "direction": "bullish",
    },
    "evening_star": {
        "label": "Evening Star",
        "short_label": "ES",
        "description": "Pola tiga candle yang sering menandai akhir dorongan naik dan awal tekanan bearish.",
        "direction": "bearish",
    },
    "bullish_marubozu": {
        "label": "Bullish Marubozu",
        "short_label": "MBU",
        "description": "Body bullish dominan hampir tanpa shadow, menandakan pembeli menguasai sesi dengan kuat.",
        "direction": "bullish",
    },
    "bearish_marubozu": {
        "label": "Bearish Marubozu",
        "short_label": "MBE",
        "description": "Body bearish dominan hampir tanpa shadow, menandakan penjual menguasai sesi dengan kuat.",
        "direction": "bearish",
    },
}


BULLISH_CANDLE_PATTERNS = [
    "bullish_engulfing",
    "hammer",
    "inverted_hammer",
    "bullish_harami",
    "piercing_line",
    "morning_star",
    "bullish_marubozu",
]
BEARISH_CANDLE_PATTERNS = [
    "bearish_engulfing",
    "hanging_man",
    "shooting_star",
    "bearish_harami",
    "dark_cloud_cover",
    "evening_star",
    "bearish_marubozu",
]
NEUTRAL_CANDLE_PATTERNS = ["doji"]
ALL_CANDLE_PATTERN_KEYS = [
    *BULLISH_CANDLE_PATTERNS,
    *BEARISH_CANDLE_PATTERNS,
    *NEUTRAL_CANDLE_PATTERNS,
]


def get_default_candle_pattern_params() -> dict[str, Any]:
    """Return the default Candle Pattern indicator settings."""
    defaults: dict[str, Any] = {
        "lookback": 180,
    }
    for pattern_key in ALL_CANDLE_PATTERN_KEYS:
        defaults[f"show_{pattern_key}"] = True
    return defaults


def normalize_candle_pattern_params(raw_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize Candle Pattern settings into safe runtime values."""
    defaults = get_default_candle_pattern_params()
    raw_params = raw_params or {}

    try:
        lookback = int(raw_params.get("lookback", defaults["lookback"]))
    except (TypeError, ValueError):
        lookback = int(defaults["lookback"])
    normalized: dict[str, Any] = {
        "lookback": max(lookback, 30),
    }

    for pattern_key in ALL_CANDLE_PATTERN_KEYS:
        param_key = f"show_{pattern_key}"
        normalized[param_key] = bool(raw_params.get(param_key, defaults[param_key]))

    return normalized

