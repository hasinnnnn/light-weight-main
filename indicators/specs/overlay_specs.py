from __future__ import annotations

OVERLAY_INDICATOR_SPECS = [
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
]