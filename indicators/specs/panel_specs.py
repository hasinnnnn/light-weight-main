from __future__ import annotations

PANEL_AND_MISC_INDICATOR_SPECS = [
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
