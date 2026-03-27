from __future__ import annotations

BACKTEST_STRATEGY_CATALOG = [
    {
        "key": "RSI",
        "label": "RSI",
        "description": "Mean reversion RSI dengan trend filter dan exit fleksibel.",
    },
    {
        "key": "MACD",
        "label": "MACD",
        "description": "Trend-following MACD dengan filter trend dan opsi exit momentum.",
    },
    {
        "key": "BREAK_EMA",
        "label": "Break EMA",
        "description": "Buy saat harga pullback ke EMA dan hold sampai harga breakdown valid di bawah EMA.",
    },
    {
        "key": "BREAK_MA",
        "label": "Break MA",
        "description": "Buy saat harga pullback ke MA dan hold sampai harga breakdown valid di bawah MA.",
    },
    {
        "key": "PARABOLIC_SAR",
        "label": "Parabolic SAR",
        "description": "Trend-following Parabolic SAR dengan filter MA 200 yang lebih simpel dan bersih.",
    },
    {
        "key": "VOLUME_BREAKOUT",
        "label": "Volume Breakout",
        "description": "Breakout dari area konsolidasi sempit dengan volume rendah lalu meledak saat breakout.",
    },
]

BACKTEST_STRATEGY_LABELS = {
    item["key"]: item["label"] for item in BACKTEST_STRATEGY_CATALOG
}

BACKTEST_PERIOD_DISPLAY = {
    "1d": "1D",
    "5d": "5D",
    "1wk": "1W",
    "2wk": "2W",
    "1mo": "1M",
    "3mo": "3M",
    "6mo": "6M",
    "1y": "1Y",
    "2y": "2Y",
    "5y": "5Y",
    "YTD": "YTD",
    "ALL": "ALL",
}

POSITION_SIZING_MODES = [
    "fixed_percent_of_equity",
    "fixed_nominal",
]

RSI_ENTRY_MODES = ["cross_up_oversold"]
RSI_EXIT_MODES = [
    "rsi_above_level",
    "cross_down_overbought",
    "fixed_tp_sl",
]
MACD_ENTRY_MODES = [
    "macd_cross_up_signal",
    "macd_cross_up_zero",
    "histogram_turn_positive",
]
MACD_EXIT_MODES = [
    "macd_cross_down_signal",
    "macd_cross_down_zero",
    "fixed_tp_sl",
]
BREAK_EMA_EXIT_MODES = [
    "ema_breakdown",
    "tp_sl_trailing_only",
]
BREAK_EMA_CONFIRMATION_MODES = [
    "body_breakdown",
    "marubozu_breakdown",
]
BREAK_MA_EXIT_MODES = [
    "ma_breakdown",
    "tp_sl_trailing_only",
]
BREAK_MA_CONFIRMATION_MODES = [
    "body_breakdown",
    "marubozu_breakdown",
]


