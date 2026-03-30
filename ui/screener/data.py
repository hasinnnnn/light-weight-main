from __future__ import annotations

from typing import Any

import streamlit as st

from backtest.config import get_default_backtest_general_params, get_default_break_ema_params
from backtest.engine import BacktestError, run_backtest
from data.market_data_service import DataServiceError, load_market_data
from ui.market_insight_parts.formatters import format_price_change_with_percent, format_price_value


SCREENER_DEFAULT_INTERVAL_LABEL = "1 hari"
SCREENER_EMA_SYMBOLS = [
    "BUMI",
    "MEDC",
    "DEWA",
    "ELSA",
    "BIPI",
    "BKSL",
    "BUVA",
    "MINA",
    "INET",
    "GTSI",
    "ANTM",
    "RLCO",
    "VKTR",
    "ENRG",
    "WIFI",
    "ADRO",
]


def _fallback_price(result: Any) -> float | None:
    current_price = getattr(result, "current_price", None)
    if current_price is not None:
        return float(current_price)

    frame = getattr(result, "data", None)
    if frame is None or getattr(frame, "empty", True):
        return None
    return float(frame.iloc[-1]["close"])


def _build_price_change_text(
    current_price: float | None,
    previous_close: float | None,
    *,
    use_integer_price: bool = False,
) -> tuple[float | None, str]:
    if current_price is None or previous_close is None or previous_close == 0:
        return None, "-"

    change_value = float(current_price) - float(previous_close)
    change_pct = (change_value / float(previous_close)) * 100.0
    return (
        change_pct,
        format_price_change_with_percent(
            change_value,
            change_pct,
            use_integer_price=use_integer_price,
            include_sign=False,
        ),
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_ema_screener_row(
    symbol: str,
    interval_label: str,
    period_label: str,
    ema_period: int,
) -> dict[str, Any]:
    """Load one symbol snapshot and reuse BREAK_EMA backtest logic for the win rate."""
    normalized_symbol = str(symbol or "").strip().upper()
    normalized_interval = str(interval_label or SCREENER_DEFAULT_INTERVAL_LABEL).strip()
    normalized_period = str(period_label or "YTD").strip()
    normalized_ema_period = max(int(ema_period), 1)

    try:
        result = load_market_data(
            symbol=normalized_symbol,
            interval_label=normalized_interval,
            period_label=normalized_period,
        )
    except DataServiceError as exc:
        return {
            "company_name": "-",
            "symbol": normalized_symbol,
            "current_price": None,
            "current_price_text": "-",
            "price_change_pct": None,
            "price_change_text": "-",
            "win_rate_pct": None,
            "win_rate_text": "-",
            "error": str(exc),
        }

    current_price = _fallback_price(result)
    previous_close = getattr(result, "previous_close", None)
    previous_close = float(previous_close) if previous_close is not None else None
    current_price_text = format_price_value(current_price) if current_price is not None else "-"
    price_change_pct, price_change_text = _build_price_change_text(
        current_price,
        previous_close,
        use_integer_price=bool(getattr(result, "uses_bei_price_fractions", False)),
    )
    general_params = get_default_backtest_general_params()
    strategy_params = get_default_break_ema_params()
    strategy_params["ema_period"] = normalized_ema_period

    try:
        backtest_result = run_backtest(
            data=result.data,
            strategy_key="BREAK_EMA",
            general_params=general_params,
            strategy_params=strategy_params,
            symbol=result.symbol,
            interval_label=normalized_interval,
            period_label=normalized_period,
            use_lot_sizing=result.uses_bei_price_fractions,
        )
        win_rate_pct = float(backtest_result.metrics.win_rate_pct)
        win_rate_text = f"{win_rate_pct:.2f}%"
    except BacktestError as exc:
        win_rate_pct = None
        win_rate_text = "-"
        return {
            "company_name": result.company_name or normalized_symbol,
            "symbol": result.symbol,
            "current_price": current_price,
            "current_price_text": current_price_text,
            "price_change_pct": price_change_pct,
            "price_change_text": price_change_text,
            "win_rate_pct": win_rate_pct,
            "win_rate_text": win_rate_text,
            "error": str(exc),
        }

    return {
        "company_name": result.company_name or normalized_symbol,
        "symbol": result.symbol,
        "current_price": current_price,
        "current_price_text": current_price_text,
        "price_change_pct": price_change_pct,
        "price_change_text": price_change_text,
        "win_rate_pct": win_rate_pct,
        "win_rate_text": win_rate_text,
        "error": "",
    }


def build_ema_screener_rows(
    interval_label: str,
    period_label: str,
    ema_period: int,
) -> list[dict[str, Any]]:
    """Build the displayed screener rows for the current controls."""
    rows: list[dict[str, Any]] = []
    for index, symbol in enumerate(SCREENER_EMA_SYMBOLS, start=1):
        row = load_ema_screener_row(symbol, interval_label, period_label, ema_period)
        rows.append(
            {
                "no": index,
                "company_name": row["company_name"],
                "symbol": row["symbol"],
                "current_price": row["current_price"],
                "current_price_text": row["current_price_text"],
                "price_change_pct": row["price_change_pct"],
                "price_change_text": row["price_change_text"],
                "win_rate_pct": row["win_rate_pct"],
                "win_rate_text": row["win_rate_text"],
                "error": row.get("error", ""),
            }
        )
    return rows


__all__ = [
    "SCREENER_DEFAULT_INTERVAL_LABEL",
    "SCREENER_EMA_SYMBOLS",
    "build_ema_screener_rows",
    "load_ema_screener_row",
]
