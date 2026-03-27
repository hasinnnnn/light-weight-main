from __future__ import annotations

from dataclasses import replace

import pandas as pd

from common.time_utils import format_timestamp
from config.chart_options import INTERVAL_LABEL_TO_CODE
from data.history import (
    apply_intraday_guard,
    build_market_insight,
    build_market_session_summary,
    daily_ohlcv_from_history,
    download_history_with_fallback,
    download_live_history_with_fallback,
    extract_price_snapshot,
    finalize_chart_dataframe,
    normalize_history_dataframe,
    resample_to_4h,
    translate_period_selection,
)
from data.models import DataLoadResult, DataServiceError, MarketSessionSummary
from data.search import (
    INDONESIA_SYMBOL_SUFFIX,
    candidate_provider_symbols,
    display_symbol,
    resolve_company_name,
    sanitize_symbol,
)


def _refine_market_card_summary_from_intraday(
    history_frame: pd.DataFrame,
    summary: MarketSessionSummary,
    uses_bei_price_fractions: bool,
) -> MarketSessionSummary:
    """Improve lot/value/avg using the latest intraday session bars when available."""
    if history_frame.empty or not isinstance(history_frame.index, pd.DatetimeIndex):
        return summary

    has_intraday_timestamps = (
        history_frame.index.hour.any()
        or history_frame.index.minute.any()
        or history_frame.index.second.any()
    )
    if not has_intraday_timestamps:
        return summary

    latest_session_date = history_frame.index[-1].date()
    session_frame = history_frame.loc[history_frame.index.date == latest_session_date].copy()
    if session_frame.empty:
        return summary

    for column in ["open", "high", "low", "close", "volume"]:
        session_frame[column] = pd.to_numeric(session_frame[column], errors="coerce")
    session_frame = session_frame.dropna(subset=["open", "high", "low", "close"])
    if session_frame.empty:
        return summary

    session_frame["volume"] = session_frame["volume"].fillna(0.0)
    total_volume = float(session_frame["volume"].sum())
    if total_volume <= 0:
        return summary

    typical_price = (
        session_frame["open"]
        + session_frame["high"]
        + session_frame["low"]
        + session_frame["close"]
    ) / 4.0
    estimated_value = float((typical_price * session_frame["volume"]).sum())
    average_price = estimated_value / total_volume if total_volume else summary.average_price
    lot = (total_volume / 100.0) if uses_bei_price_fractions else summary.lot

    return replace(
        summary,
        average_price=average_price,
        value=estimated_value,
        volume=total_volume,
        lot=lot,
    )



def _build_market_card_from_history(
    history_frame: pd.DataFrame,
    uses_bei_price_fractions: bool,
) -> tuple[float | None, float | None, object]:
    """Build one consistent top-card snapshot from a normalized history frame."""
    if history_frame.empty:
        empty_daily_frame = daily_ohlcv_from_history(history_frame)
        empty_summary = build_market_session_summary(
            empty_daily_frame,
            uses_bei_price_fractions=uses_bei_price_fractions,
        )
        return None, None, empty_summary

    daily_frame = daily_ohlcv_from_history(history_frame)
    current_price, previous_close = extract_price_snapshot(history_frame)
    session_summary = build_market_session_summary(
        daily_frame,
        uses_bei_price_fractions=uses_bei_price_fractions,
    )
    session_summary = _refine_market_card_summary_from_intraday(
        history_frame,
        session_summary,
        uses_bei_price_fractions=uses_bei_price_fractions,
    )
    return current_price, previous_close, session_summary



def _download_latest_market_card_history(resolved_symbol: str) -> pd.DataFrame:
    """Download one consistent latest-session snapshot for the top market card."""
    snapshot_candidates = [
        ("1m", "5d"),
        ("15m", "5d"),
        ("1d", "1mo"),
    ]

    for interval, native_period in snapshot_candidates:
        try:
            snapshot_history, _ = download_live_history_with_fallback(
                symbols=[resolved_symbol],
                interval=interval,
                native_period=native_period,
                start_iso=None,
                end_iso=None,
            )
            normalized_snapshot_history = normalize_history_dataframe(snapshot_history)
        except Exception:
            continue

        if normalized_snapshot_history is not None and not normalized_snapshot_history.empty:
            return normalized_snapshot_history

    return pd.DataFrame()


def load_market_data(
    symbol: str,
    interval_label: str,
    period_label: str,
) -> DataLoadResult:
    """Fetch, validate, normalize, and prepare chart-ready market data."""
    requested_symbol = sanitize_symbol(symbol)
    if not requested_symbol:
        raise DataServiceError("Please enter a ticker symbol before loading the chart.")
    provider_symbols = candidate_provider_symbols(requested_symbol)
    display_code = display_symbol(requested_symbol)

    try:
        interval_code = INTERVAL_LABEL_TO_CODE[interval_label]
    except KeyError as exc:
        raise DataServiceError(f"Unsupported interval selection: {interval_label}") from exc

    period_request = translate_period_selection(period_label)
    resolved_request, warnings = apply_intraday_guard(period_request, interval_code)

    download_interval = "1h" if interval_code == "4h" else interval_code
    start_iso = resolved_request.start.isoformat() if resolved_request.start is not None else None
    end_iso = resolved_request.end.isoformat() if resolved_request.end is not None else None

    try:
        raw_history, resolved_symbol = download_history_with_fallback(
            symbols=provider_symbols,
            interval=download_interval,
            native_period=resolved_request.native_period,
            start_iso=start_iso,
            end_iso=end_iso,
        )
    except DataServiceError:
        raise
    except Exception as exc:
        raise DataServiceError(
            "Unable to download market data right now. Please check your connection and try again."
        ) from exc

    normalized_history = normalize_history_dataframe(raw_history)
    if interval_code == "4h":
        normalized_history = resample_to_4h(normalized_history)

    resolved_display_code = display_symbol(resolved_symbol)
    if not display_code:
        display_code = resolved_display_code

    if (
        resolved_symbol != requested_symbol
        and resolved_symbol not in {"^JKSE"}
        and resolved_display_code != display_code
    ):
        warnings.append(
            f"Ticker `{display_code}` otomatis dibaca sebagai `{resolved_display_code}`."
        )

    first_timestamp = format_timestamp(normalized_history.index[0])
    last_timestamp = format_timestamp(normalized_history.index[-1])
    company_name = resolve_company_name(resolved_symbol)
    uses_bei_price_fractions = resolved_symbol.endswith(INDONESIA_SYMBOL_SUFFIX)

    chart_daily_frame = daily_ohlcv_from_history(normalized_history)
    current_price, previous_close = extract_price_snapshot(normalized_history)
    session_summary = build_market_session_summary(
        chart_daily_frame,
        uses_bei_price_fractions=uses_bei_price_fractions,
    )

    market_card_history = _download_latest_market_card_history(resolved_symbol)
    if not market_card_history.empty:
        snapshot_price, snapshot_prev_close, session_summary = _build_market_card_from_history(
            market_card_history,
            uses_bei_price_fractions=uses_bei_price_fractions,
        )
        if snapshot_price is not None:
            current_price = snapshot_price
            previous_close = snapshot_prev_close

    chart_frame = finalize_chart_dataframe(normalized_history)
    insight = build_market_insight(normalized_history)

    return DataLoadResult(
        data=chart_frame,
        symbol=display_code,
        uses_bei_price_fractions=uses_bei_price_fractions,
        interval_label=interval_label,
        period_label=period_label,
        rows_loaded=len(chart_frame),
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        company_name=company_name,
        current_price=current_price,
        previous_close=previous_close,
        session_summary=session_summary,
        warnings=warnings,
        insight=insight,
    )
