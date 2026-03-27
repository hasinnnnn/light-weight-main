from __future__ import annotations

PATTERN_AND_STRUCTURE_INDICATOR_SPECS = [
    {
        "key": "CANDLE_PATTERN",
        "modal_label": "Candle Pattern",
        "description": "Deteksi pola candle umum dan tampilkan label singkat langsung di atas atau bawah candle.",
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback Candle",
                "default": 180,
                "min_value": 30,
            }
        ],
        "color_fields": [
            {"name": "bullish", "label": "Pattern Bullish", "default": "#22c55e"},
            {"name": "bearish", "label": "Pattern Bearish", "default": "#ef4444"},
            {"name": "neutral", "label": "Pattern Netral", "default": "#f8fafc"},
        ],
    },
    {
        "key": "CHART_PATTERN",
        "modal_label": "Chart Pattern",
        "description": "Deteksi pola chart besar seperti double top, head and shoulders, triangle, wedge, dan cup and handle.",
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback Pattern",
                "default": 220,
                "min_value": 80,
            },
            {
                "name": "pivot_window",
                "label": "Sensitivitas Pivot",
                "default": 3,
                "min_value": 2,
            },
            {
                "name": "tolerance_pct",
                "label": "Toleransi Harga (%)",
                "default": 3,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "bullish", "label": "Pattern Bullish", "default": "#22c55e"},
            {"name": "bearish", "label": "Pattern Bearish", "default": "#ef4444"},
            {"name": "neutral", "label": "Pattern Netral", "default": "#38bdf8"},
            {"name": "line", "label": "Garis Pattern", "default": "#1d4ed8"},
        ],
    },
    {
        "key": "CONSOLIDATION_AREA",
        "modal_label": "Area Konsolidasi",
        "description": "Tandai beberapa area konsolidasi valid langsung di chart utama dengan box transparan.",
        "placement": "overlay",
        "fields": [
            {
                "name": "lookback",
                "label": "Lookback Area",
                "default": 220,
                "min_value": 40,
            },
            {
                "name": "consolidation_bars",
                "label": "Bar Konsolidasi",
                "default": 10,
                "min_value": 3,
            },
            {
                "name": "max_consolidation_range_pct",
                "label": "Rentang Maks (%)",
                "default": 6,
                "min_value": 1,
            },
            {
                "name": "volume_ma_period",
                "label": "MA Volume",
                "default": 20,
                "min_value": 3,
            },
            {
                "name": "consolidation_volume_ratio_max",
                "label": "Volume Konsolidasi Maks. (x)",
                "default": 0.8,
                "min_value": 0.1,
                "step": 0.05,
                "format": "%.2f",
                "value_type": "float",
            },
            {
                "name": "max_zones",
                "label": "Maks. Zona",
                "default": 6,
                "min_value": 1,
            },
        ],
        "color_fields": [
            {"name": "zone", "label": "Zona Historis", "default": "#38bdf8"},
            {"name": "active", "label": "Zona Aktif", "default": "#22c55e"},
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
            {
                "name": "max_trendlines",
                "label": "Maks. Trendline",
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
            {
                "name": "max_trendlines",
                "label": "Maks. Trendline Major",
                "default": 3,
                "min_value": 1,
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
]