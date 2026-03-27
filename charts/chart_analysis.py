from __future__ import annotations

from charts.chart_core import _indicator_colors, _indicator_params
from indicators.fibonacci import build_fibonacci_analysis
from indicators.support_resistance import (
    _build_nearest_support_resistance_summary,
    _build_strong_support_resistance_summary,
    describe_nearest_support_resistance,
    describe_strong_support_resistance,
)
from indicators.trendlines import (
    _build_auto_trendline_summaries,
    _build_major_trendline_summaries,
    describe_auto_trendline,
    describe_auto_trendlines,
    describe_major_trendline,
    describe_major_trendlines,
)


def describe_fibonacci_levels(data, indicator):
    """Describe Fibonacci levels, swing anchors, and touch or bounce stats for the note card."""
    return build_fibonacci_analysis(
        data=data,
        params=_indicator_params(indicator),
        colors=_indicator_colors(indicator),
    )


__all__ = [
    "_build_auto_trendline_summaries",
    "_build_major_trendline_summaries",
    "_build_nearest_support_resistance_summary",
    "_build_strong_support_resistance_summary",
    "describe_auto_trendline",
    "describe_auto_trendlines",
    "describe_major_trendline",
    "describe_major_trendlines",
    "describe_nearest_support_resistance",
    "describe_strong_support_resistance",
    "describe_fibonacci_levels",
]
