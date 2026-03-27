from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from data.models import DataServiceError



def _download_history_kwargs(
    symbol: str,
    interval: str,
    native_period: str | None,
    start_iso: str | None,
    end_iso: str | None,
) -> dict[str, object]:
    """Build one normalized yf.download kwargs payload."""
    kwargs: dict[str, object] = {
        "tickers": symbol,
        "interval": interval,
        "progress": False,
        "auto_adjust": False,
        "actions": False,
        "threads": False,
    }

    if native_period:
        kwargs["period"] = native_period
    else:
        if start_iso is None or end_iso is None:
            raise DataServiceError("A start/end range is required for this request.")
        kwargs["start"] = pd.Timestamp(start_iso).to_pydatetime()
        kwargs["end"] = pd.Timestamp(end_iso).to_pydatetime()

    return kwargs


@st.cache_data(ttl=300, show_spinner=False)
def _download_history_cached(
    symbol: str,
    interval: str,
    native_period: str | None,
    start_iso: str | None,
    end_iso: str | None,
) -> pd.DataFrame:
    """Download raw OHLCV data from yfinance with caching."""
    kwargs = _download_history_kwargs(symbol, interval, native_period, start_iso, end_iso)
    return yf.download(**kwargs)


@st.cache_data(ttl=30, show_spinner=False)
def _download_live_history_cached(
    symbol: str,
    interval: str,
    native_period: str | None,
    start_iso: str | None,
    end_iso: str | None,
) -> pd.DataFrame:
    """Download a fresher market snapshot with a shorter cache window."""
    kwargs = _download_history_kwargs(symbol, interval, native_period, start_iso, end_iso)
    return yf.download(**kwargs)



def download_history_with_fallback(
    symbols: list[str],
    interval: str,
    native_period: str | None,
    start_iso: str | None,
    end_iso: str | None,
) -> tuple[pd.DataFrame, str]:
    """Try candidate symbols in order until one returns non-empty history."""
    last_frame = pd.DataFrame()
    last_symbol = symbols[0]

    for candidate_symbol in symbols:
        frame = _download_history_cached(
            symbol=candidate_symbol,
            interval=interval,
            native_period=native_period,
            start_iso=start_iso,
            end_iso=end_iso,
        )
        last_frame = frame
        last_symbol = candidate_symbol
        if frame is not None and not frame.empty:
            return frame, candidate_symbol

    return last_frame, last_symbol



def download_live_history_with_fallback(
    symbols: list[str],
    interval: str,
    native_period: str | None,
    start_iso: str | None,
    end_iso: str | None,
) -> tuple[pd.DataFrame, str]:
    """Try candidate symbols in order with a shorter cache for live market-card data."""
    last_frame = pd.DataFrame()
    last_symbol = symbols[0]

    for candidate_symbol in symbols:
        frame = _download_live_history_cached(
            symbol=candidate_symbol,
            interval=interval,
            native_period=native_period,
            start_iso=start_iso,
            end_iso=end_iso,
        )
        last_frame = frame
        last_symbol = candidate_symbol
        if frame is not None and not frame.empty:
            return frame, candidate_symbol

    return last_frame, last_symbol


__all__ = ["download_history_with_fallback", "download_live_history_with_fallback"]
