from __future__ import annotations

from typing import Any, Iterable

import streamlit as st

from backtest.config import get_default_backtest_general_params, get_default_break_ema_params
from backtest.engine import BacktestError, BacktestResult, run_backtest
from data.market_data_service import DataLoadResult, DataServiceError, load_market_data
from ui.backtest.sections.result_summary import format_rupiah
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


def _fallback_price(result: DataLoadResult) -> float | None:
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


def build_break_ema_strategy_params(
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> dict[str, Any]:
    """Build one normalized BREAK_EMA parameter mapping shared by screener helpers."""
    default_strategy_params = get_default_break_ema_params()
    strategy_params = default_strategy_params.copy()
    strategy_params["ema_period"] = max(int(ema_period), 1)
    strategy_params["breakdown_confirm_mode"] = str(
        breakdown_confirm_mode or default_strategy_params["breakdown_confirm_mode"]
    ).strip()
    strategy_params["exit_mode"] = str(exit_mode or default_strategy_params["exit_mode"]).strip()
    return strategy_params


def _empty_screener_row(symbol: str, error: str) -> dict[str, Any]:
    return {
        "company_name": "-",
        "symbol": str(symbol or "").strip().upper(),
        "current_price": None,
        "current_price_text": "-",
        "price_change_pct": None,
        "price_change_text": "-",
        "total_trades": None,
        "total_trades_text": "-",
        "net_profit": None,
        "net_profit_text": "-",
        "win_rate_pct": None,
        "win_rate_text": "-",
        "error": str(error),
    }


def build_screener_row_from_market_result(
    result: DataLoadResult,
    *,
    interval_label: str,
    period_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> tuple[dict[str, Any], BacktestResult | None]:
    """Build one screener row and optional backtest payload from a loaded market result."""
    current_price = _fallback_price(result)
    previous_close = getattr(result, "previous_close", None)
    previous_close = float(previous_close) if previous_close is not None else None
    current_price_text = format_price_value(current_price) if current_price is not None else "-"
    price_change_pct, price_change_text = _build_price_change_text(
        current_price,
        previous_close,
        use_integer_price=bool(getattr(result, "uses_bei_price_fractions", False)),
    )
    strategy_params = build_break_ema_strategy_params(
        ema_period=ema_period,
        breakdown_confirm_mode=breakdown_confirm_mode,
        exit_mode=exit_mode,
    )
    general_params = get_default_backtest_general_params()

    try:
        backtest_result = run_backtest(
            data=result.data,
            strategy_key="BREAK_EMA",
            general_params=general_params,
            strategy_params=strategy_params,
            symbol=result.symbol,
            interval_label=str(interval_label),
            period_label=str(period_label),
            use_lot_sizing=result.uses_bei_price_fractions,
        )
        total_trades = int(backtest_result.metrics.total_trades)
        net_profit = float(backtest_result.metrics.net_profit)
        win_rate_pct = float(backtest_result.metrics.win_rate_pct)
        row = {
            "company_name": result.company_name or result.symbol,
            "symbol": result.symbol,
            "current_price": current_price,
            "current_price_text": current_price_text,
            "price_change_pct": price_change_pct,
            "price_change_text": price_change_text,
            "total_trades": total_trades,
            "total_trades_text": str(total_trades),
            "net_profit": net_profit,
            "net_profit_text": format_rupiah(net_profit, show_sign=True),
            "win_rate_pct": win_rate_pct,
            "win_rate_text": f"{win_rate_pct:.2f}%",
            "error": "",
        }
        return row, backtest_result
    except BacktestError as exc:
        row = {
            "company_name": result.company_name or result.symbol,
            "symbol": result.symbol,
            "current_price": current_price,
            "current_price_text": current_price_text,
            "price_change_pct": price_change_pct,
            "price_change_text": price_change_text,
            "total_trades": None,
            "total_trades_text": "-",
            "net_profit": None,
            "net_profit_text": "-",
            "win_rate_pct": None,
            "win_rate_text": "-",
            "error": str(exc),
        }
        return row, None


def load_ema_screener_snapshot(
    symbol: str,
    interval_label: str,
    period_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> dict[str, Any]:
    """Load one uncached screener snapshot for worker and alert processing."""
    normalized_symbol = str(symbol or "").strip().upper()
    normalized_interval = str(interval_label or SCREENER_DEFAULT_INTERVAL_LABEL).strip()
    normalized_period = str(period_label or "YTD").strip()
    normalized_ema_period = max(int(ema_period), 1)
    strategy_params = build_break_ema_strategy_params(
        ema_period=normalized_ema_period,
        breakdown_confirm_mode=breakdown_confirm_mode,
        exit_mode=exit_mode,
    )

    try:
        result = load_market_data(
            symbol=normalized_symbol,
            interval_label=normalized_interval,
            period_label=normalized_period,
        )
    except DataServiceError as exc:
        return {
            "row": _empty_screener_row(normalized_symbol, str(exc)),
            "market_result": None,
            "backtest_result": None,
            "strategy_params": strategy_params,
        }

    row, backtest_result = build_screener_row_from_market_result(
        result,
        interval_label=normalized_interval,
        period_label=normalized_period,
        ema_period=normalized_ema_period,
        breakdown_confirm_mode=str(strategy_params["breakdown_confirm_mode"]),
        exit_mode=str(strategy_params["exit_mode"]),
    )
    return {
        "row": row,
        "market_result": result,
        "backtest_result": backtest_result,
        "strategy_params": strategy_params,
    }


@st.cache_data(ttl=600, show_spinner=False)
def load_ema_screener_row(
    symbol: str,
    interval_label: str,
    period_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> dict[str, Any]:
    """Load one symbol snapshot and reuse BREAK_EMA backtest logic for the win rate."""
    snapshot = load_ema_screener_snapshot(
        symbol=symbol,
        interval_label=interval_label,
        period_label=period_label,
        ema_period=ema_period,
        breakdown_confirm_mode=breakdown_confirm_mode,
        exit_mode=exit_mode,
    )
    return dict(snapshot["row"])


def build_ema_screener_rows(
    interval_label: str,
    period_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
    *,
    symbols: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Build the displayed screener rows for the current controls."""
    target_symbols = [
        str(symbol).strip().upper()
        for symbol in (symbols or SCREENER_EMA_SYMBOLS)
        if str(symbol).strip()
    ]

    rows: list[dict[str, Any]] = []
    for index, symbol in enumerate(target_symbols, start=1):
        row = load_ema_screener_row(
            symbol,
            interval_label,
            period_label,
            ema_period,
            breakdown_confirm_mode,
            exit_mode,
        )
        rows.append(
            {
                "no": index,
                "company_name": row["company_name"],
                "symbol": row["symbol"],
                "current_price": row["current_price"],
                "current_price_text": row["current_price_text"],
                "price_change_pct": row["price_change_pct"],
                "price_change_text": row["price_change_text"],
                "total_trades": row["total_trades"],
                "total_trades_text": row["total_trades_text"],
                "net_profit": row["net_profit"],
                "net_profit_text": row["net_profit_text"],
                "win_rate_pct": row["win_rate_pct"],
                "win_rate_text": row["win_rate_text"],
                "error": row.get("error", ""),
            }
        )
    return rows


__all__ = [
    "SCREENER_DEFAULT_INTERVAL_LABEL",
    "SCREENER_EMA_SYMBOLS",
    "build_break_ema_strategy_params",
    "build_ema_screener_rows",
    "build_screener_row_from_market_result",
    "load_ema_screener_row",
    "load_ema_screener_snapshot",
]
