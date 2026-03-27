from __future__ import annotations

from typing import Any

FIBONACCI_LEVELS = [
    (0.0, "#d1d5db"),
    (0.236, "#ef4444"),
    (0.382, "#f59e0b"),
    (0.5, "#22c55e"),
    (0.618, "#14b8a6"),
    (0.786, "#22d3ee"),
    (1.0, "#9ca3af"),
]
FIBONACCI_FILL_ALPHAS = [0.14, 0.12, 0.11, 0.11, 0.11, 0.08]
FIBONACCI_MONOCHROME_DEFAULT = "#60a5fa"
FIBONACCI_LEVEL_NOTES = {
    0.236: (
        "Koreksi ringan",
        "Menandakan koreksi ringan dan sering muncul saat tren utama masih kuat.",
    ),
    0.382: (
        "Koreksi umum",
        "Zona koreksi umum dan area support atau resistance awal yang sering dipantau trader.",
    ),
    0.5: (
        "Level psikologis",
        "Bukan rasio Fibonacci asli, tetapi level penting tempat harga sering menguji keseimbangan.",
    ),
    0.618: (
        "Golden Ratio",
        "Level Fibonacci terpenting yang sering dipakai untuk membaca potensi pantulan atau reversal.",
    ),
    0.786: (
        "Koreksi dalam",
        "Menandakan retracement dalam dan sering jadi area uji terakhir sebelum pembalikan arah besar.",
    ),
}
FIBONACCI_SWING_MODE_LABELS = {
    "aggressive": "Agresif",
    "balanced": "Seimbang",
    "major": "Mayor",
}
FIBONACCI_SWING_MODE_SHORT_LABELS = {
    "aggressive": "Agr",
    "balanced": "Bal",
    "major": "Maj",
}
VALID_FIBONACCI_SWING_DIRECTIONS = {"low_to_high", "high_to_low"}
VALID_FIBONACCI_SWING_MODES = set(FIBONACCI_SWING_MODE_LABELS)


def normalize_fibonacci_swing_direction(value: Any) -> str:
    """Return one supported Fibonacci swing direction."""
    normalized_value = str(value or "low_to_high").strip().lower()
    if normalized_value in VALID_FIBONACCI_SWING_DIRECTIONS:
        return normalized_value
    return "low_to_high"


def normalize_fibonacci_swing_mode(value: Any) -> str:
    """Return one supported Fibonacci swing mode."""
    normalized_value = str(value or "balanced").strip().lower()
    if normalized_value in VALID_FIBONACCI_SWING_MODES:
        return normalized_value
    return "balanced"

