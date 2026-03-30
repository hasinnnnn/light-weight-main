from __future__ import annotations

import html

import streamlit as st

from data.market_data_service import DataLoadResult

from .formatters import (
    format_compact_metric,
    format_metric_value,
    format_price_change_with_percent,
    format_price_value,
)

def build_market_stat_html(
    label: str,
    value_text: str,
    tone_class: str,
) -> str:
    """Build one compact stat row for the market insight card."""
    return (
        '<div class="insight-stat-item">'
        f'<div class="insight-stat-label">{html.escape(label)}</div>'
        f'<div class="insight-stat-value {html.escape(tone_class)}">{html.escape(value_text)}</div>'
        "</div>"
    )


def build_market_stat_tone(
    value: float | None,
    previous_close: float | None,
    kind: str = "price",
) -> str:
    """Choose one text color class for the stat value."""
    if value is None:
        return "stat-neutral"
    if kind in {"limit", "count", "value"}:
        return "stat-soft"
    if previous_close is None or previous_close == 0:
        return "stat-neutral"
    if value > previous_close:
        return "stat-up"
    if value < previous_close:
        return "stat-down"
    return "stat-neutral"


def is_blank_market_stat(value: float | None) -> bool:
    """Return whether one market-stat value should be treated as empty."""
    return value is None or abs(float(value)) < 1e-9


def build_market_session_stats_html(result: DataLoadResult) -> str:
    """Build the compact daily market stats shown under the company name."""
    summary = result.session_summary
    uses_bei = bool(result.uses_bei_price_fractions)
    previous_close = summary.previous_close
    is_ihsg = (result.symbol or "").strip().upper() == "IHSG"

    if is_ihsg:
        ihsg_stats = [
            (
                "Open",
                summary.open_price,
                format_metric_value(summary.open_price, use_integer_price=False),
                build_market_stat_tone(summary.open_price, previous_close),
            ),
            (
                "High",
                summary.high_price,
                format_metric_value(summary.high_price, use_integer_price=False),
                build_market_stat_tone(summary.high_price, previous_close),
            ),
            (
                "Low",
                summary.low_price,
                format_metric_value(summary.low_price, use_integer_price=False),
                build_market_stat_tone(summary.low_price, previous_close),
            ),
            (
                "Prev",
                summary.previous_close,
                format_metric_value(summary.previous_close, use_integer_price=False),
                "stat-neutral",
            ),
            (
                "Vol",
                summary.volume,
                format_compact_metric(summary.volume),
                "stat-soft",
            ),
            (
                "Val",
                summary.value,
                format_compact_metric(summary.value),
                "stat-soft",
            ),
            (
                "Avg",
                summary.average_price,
                format_metric_value(summary.average_price, use_integer_price=False),
                build_market_stat_tone(summary.average_price, previous_close, kind="average"),
            ),
        ]

        visible_stats = [
            build_market_stat_html(label, value_text, tone_class)
            for label, raw_value, value_text, tone_class in ihsg_stats
            if not is_blank_market_stat(raw_value)
        ]
        if not visible_stats:
            return ""

        column_count = 3 if len(visible_stats) >= 6 else 2 if len(visible_stats) >= 4 else 1
        rows_per_column = max(1, (len(visible_stats) + column_count - 1) // column_count)
        columns_html = []
        for start_index in range(0, len(visible_stats), rows_per_column):
            column_items = visible_stats[start_index : start_index + rows_per_column]
            columns_html.append(
                f'<div class="insight-stats-column">{"".join(column_items)}</div>'
            )

        return (
            f'<div class="insight-stats-grid" style="--insight-stat-columns: {column_count};">'
            f'{"".join(columns_html)}'
            "</div>"
        )

    first_column = [
        build_market_stat_html(
            "Open",
            format_metric_value(summary.open_price, use_integer_price=uses_bei),
            build_market_stat_tone(summary.open_price, previous_close),
        ),
        build_market_stat_html(
            "High",
            format_metric_value(summary.high_price, use_integer_price=uses_bei),
            build_market_stat_tone(summary.high_price, previous_close),
        ),
        build_market_stat_html(
            "Low",
            format_metric_value(summary.low_price, use_integer_price=uses_bei),
            build_market_stat_tone(summary.low_price, previous_close),
        ),
    ]

    if uses_bei:
        second_column = [
            build_market_stat_html(
                "Prev",
                format_metric_value(summary.previous_close, use_integer_price=True),
                "stat-neutral",
            ),
            build_market_stat_html(
                "ARA",
                format_metric_value(summary.ara_price, use_integer_price=True),
                "stat-neutral",
            ),
            build_market_stat_html(
                "ARB",
                format_metric_value(summary.arb_price, use_integer_price=True),
                "stat-neutral",
            ),
        ]

        third_column = [
            build_market_stat_html(
                "Lot",
                format_compact_metric(summary.lot),
                "stat-soft",
            ),
            build_market_stat_html(
                "Val",
                format_compact_metric(summary.value),
                "stat-soft",
            ),
            build_market_stat_html(
                "Avg",
                format_metric_value(summary.average_price, use_integer_price=True),
                build_market_stat_tone(summary.average_price, previous_close, kind="average"),
            ),
        ]
    else:
        second_column = [
            build_market_stat_html(
                "Prev",
                format_metric_value(summary.previous_close, use_integer_price=False),
                "stat-neutral",
            ),
            build_market_stat_html(
                "Vol",
                format_compact_metric(summary.volume),
                "stat-soft",
            ),
            build_market_stat_html(
                "Avg",
                format_metric_value(summary.average_price, use_integer_price=False),
                build_market_stat_tone(summary.average_price, previous_close, kind="average"),
            ),
        ]

        third_column = [
            build_market_stat_html(
                "Val",
                format_compact_metric(summary.value),
                "stat-soft",
            ),
        ]

    return (
        '<div class="insight-stats-grid">'
        f'<div class="insight-stats-column">{"".join(first_column)}</div>'
        f'<div class="insight-stats-column">{"".join(second_column)}</div>'
        f'<div class="insight-stats-column">{"".join(third_column)}</div>'
        "</div>"
    )


def build_price_change_state(
    current_price: float,
    previous_close: float | None,
    *,
    use_integer_price: bool = False,
) -> tuple[str, str]:
    """Return direction class and formatted change text."""
    if previous_close is None or previous_close == 0:
        return "change-flat", "-"

    change_value = current_price - previous_close
    change_ratio = ((current_price - previous_close) / previous_close) * 100
    arrow = "▲" if change_ratio > 0 else "▼" if change_ratio < 0 else "—"
    change_text = format_price_change_with_percent(
        change_value,
        change_ratio,
        use_integer_price=use_integer_price,
        include_sign=False,
    )
    if change_ratio > 0:
        return "change-up", f"{arrow} {change_text}"
    if change_ratio < 0:
        return "change-down", f"{arrow} {change_text}"
    return "change-flat", f"{arrow} {change_text}"





def render_market_insight_card() -> None:
    """Render the trend/risk summary card above the chart."""
    result = st.session_state.loaded_result
    if result is None:
        return

    insight = result.insight
    symbol = html.escape(result.symbol)
    company_name = (result.company_name or st.session_state.selected_company_name or "").strip()
    subtitle = html.escape(company_name) if company_name else ""
    subtitle_html = f'<div class="insight-subtitle">{subtitle}</div>' if subtitle else ""
    trend_class = "trend-up" if insight.trend_label == "Uptrend" else "trend-down"
    risk_class = "risk-low" if insight.risk_label == "Low Risk" else "risk-high"
    change_class, change_text = build_price_change_state(
        current_price=result.current_price,
        previous_close=result.previous_close,
        use_integer_price=bool(result.uses_bei_price_fractions),
    )
    formatted_price = html.escape(format_price_value(result.current_price))
    market_stats_html = build_market_session_stats_html(result)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-header">
                <div class="insight-title">{symbol}</div>
                <div class="insight-price">{formatted_price}</div>
                <div class="insight-change {change_class}">{html.escape(change_text)}</div>
            </div>
            {subtitle_html}
            {market_stats_html}
            <div class="insight-pill-row">
                <span class="insight-pill {trend_class}">Trend: {html.escape(insight.trend_label)}</span>
                <span class="insight-pill {risk_class}">Risk: {html.escape(insight.risk_label)}</span>
            </div>
            <div class="insight-reason">
                Alasan: {html.escape(insight.reason)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )




























