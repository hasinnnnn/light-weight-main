from .fibonacci import build_fibonacci_section
from .moving_averages import build_ema_section, build_sma_section
from .oscillators import build_macd_section, build_rsi_section
from .patterns import build_candle_pattern_section, build_chart_pattern_section
from .structures import (
    build_consolidation_section,
    build_major_trendline_section,
    build_nearest_support_resistance_section,
    build_strong_support_resistance_section,
    build_trendline_section,
)

SECTION_BUILDERS = {
    "EMA": build_ema_section,
    "MA": build_sma_section,
    "RSI": build_rsi_section,
    "MACD": build_macd_section,
    "CANDLE_PATTERN": build_candle_pattern_section,
    "CHART_PATTERN": build_chart_pattern_section,
    "FIBONACCI": build_fibonacci_section,
    "CONSOLIDATION_AREA": build_consolidation_section,
    "TRENDLINE": build_trendline_section,
    "MAJOR_TRENDLINE": build_major_trendline_section,
    "NEAREST_SUPPORT_RESISTANCE": build_nearest_support_resistance_section,
    "STRONG_SUPPORT_RESISTANCE": build_strong_support_resistance_section,
}

__all__ = ["SECTION_BUILDERS"]
