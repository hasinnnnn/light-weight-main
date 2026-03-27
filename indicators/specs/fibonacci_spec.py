from __future__ import annotations

FIBONACCI_INDICATOR_SPEC = {
    "key": "FIBONACCI",
    "modal_label": "Fibonacci",
    "description": "Level retracement Fibonacci dari range harga terbaru dengan pilihan arah dan mode swing.",
    "placement": "overlay",
    "fields": [
        {
            "name": "lookback",
            "label": "Lookback",
            "default": 120,
            "min_value": 5,
        },
        {
            "name": "swing_direction",
            "label": "Arah Swing",
            "default": "low_to_high",
            "input_type": "select",
            "options": [
                {"value": "low_to_high", "label": "Swing Low -> Swing High"},
                {"value": "high_to_low", "label": "Swing High -> Swing Low"},
            ],
        },
        {
            "name": "swing_mode",
            "label": "Mode Swing",
            "default": "balanced",
            "input_type": "select",
            "options": [
                {"value": "aggressive", "label": "Agresif"},
                {"value": "balanced", "label": "Seimbang"},
                {"value": "major", "label": "Mayor"},
            ],
        },
    ],
    "color_fields": [
        {"name": "line", "label": "Fibonacci", "default": "#60a5fa"},
    ],
}
