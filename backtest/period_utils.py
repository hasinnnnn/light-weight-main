from __future__ import annotations

import pandas as pd

from backtest.strategy_catalog import (
    BACKTEST_PERIOD_DISPLAY,
    BACKTEST_STRATEGY_CATALOG,
    BACKTEST_STRATEGY_LABELS,
)

def get_strategy_label(strategy_key: str) -> str:
    """Return a human-friendly strategy label."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    return BACKTEST_STRATEGY_LABELS.get(normalized_key, normalized_key or "Unknown")


def filter_backtest_strategies(search_query: str) -> list[dict[str, str]]:
    """Return the strategy catalog filtered by the user's search query."""
    normalized_query = str(search_query or "").strip().casefold()
    sorted_catalog = sorted(
        BACKTEST_STRATEGY_CATALOG,
        key=lambda strategy: (
            str(strategy.get("label") or "").casefold(),
            str(strategy.get("key") or "").casefold(),
        ),
    )
    if not normalized_query:
        return list(sorted_catalog)

    return [
        strategy
        for strategy in sorted_catalog
        if normalized_query in strategy["label"].casefold()
        or normalized_query in strategy["description"].casefold()
        or normalized_query in strategy["key"].casefold()
    ]


def display_backtest_period_label(period_label: str) -> str:
    """Return the compact display label used by the backtest UI."""
    normalized_label = str(period_label or "").strip()
    return BACKTEST_PERIOD_DISPLAY.get(normalized_label, normalized_label or "-")


def derive_date_range_from_chart_period(
    period_label: str,
    end_timestamp: pd.Timestamp | None = None,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Translate one chart period label into a timestamp range."""
    normalized_label = str(period_label or "").strip()
    if not normalized_label:
        return None, None

    resolved_end = pd.Timestamp(end_timestamp or pd.Timestamp.utcnow()).tz_localize(None)
    if normalized_label == "ALL":
        return None, resolved_end
    if normalized_label == "YTD":
        return pd.Timestamp(year=resolved_end.year, month=1, day=1), resolved_end

    if normalized_label == "1d":
        return resolved_end - pd.Timedelta(days=1), resolved_end
    if normalized_label == "5d":
        return resolved_end - pd.Timedelta(days=5), resolved_end
    if normalized_label == "1wk":
        return resolved_end - pd.Timedelta(days=7), resolved_end
    if normalized_label == "2wk":
        return resolved_end - pd.Timedelta(days=14), resolved_end

    date_offset_lookup = {
        "1mo": pd.DateOffset(months=1),
        "3mo": pd.DateOffset(months=3),
        "6mo": pd.DateOffset(months=6),
        "1y": pd.DateOffset(years=1),
        "2y": pd.DateOffset(years=2),
        "5y": pd.DateOffset(years=5),
    }
    offset = date_offset_lookup.get(normalized_label)
    if offset is None:
        return None, resolved_end
    return resolved_end - offset, resolved_end


def filter_frame_to_chart_period(frame: pd.DataFrame, period_label: str) -> pd.DataFrame:
    """Clamp one OHLCV frame to the active chart period as a safety net."""
    if frame.empty or "time" not in frame.columns:
        return frame.copy()

    prepared = frame.copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    prepared = prepared.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    if prepared.empty:
        return prepared

    start, end = derive_date_range_from_chart_period(
        period_label=period_label,
        end_timestamp=pd.Timestamp(prepared["time"].iloc[-1]),
    )
    if start is not None:
        prepared = prepared.loc[prepared["time"] >= start]
    if end is not None:
        prepared = prepared.loc[prepared["time"] <= end]
    if prepared.empty:
        return frame.copy()
    return prepared.reset_index(drop=True)

