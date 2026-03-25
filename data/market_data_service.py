from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st
import yfinance as yf
import math

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - transitively installed by yfinance in normal use
    requests = None

from common.time_utils import (
    format_timestamp,
    inclusive_request_end,
    is_intraday_interval,
    period_lookback_days,
    utc_now,
)
from config.chart_options import (
    INTERVAL_LABEL_TO_CODE,
    PERIOD_LABEL_TO_NATIVE,
    INTRADAY_MAX_LOOKBACK_DAYS,
    JAKARTA_TIMEZONE,
)

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]
INDONESIA_SYMBOL_SUFFIX = ".JK"
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
SEARCHABLE_QUOTE_TYPES = {"EQUITY", "ETF", "INDEX", "MUTUALFUND", "WARRANT"}
SYMBOL_ALIASES = {
    "IHSG": "^JKSE",
}
LOCAL_SYMBOL_CATALOG = [
    ("IHSG", "Indeks Harga Saham Gabungan", "^JKSE", "INDEX", "Indonesia"),
    ("PADI", "Minna Padi Investama Sekuritas Tbk.", "PADI.JK", "EQUITY", "Indonesia"),
    ("PADI-W", "Waran Seri I Minna Padi Investama Sekuritas Tbk.", "PADI-W.JK", "WARRANT", "Indonesia"),
    ("MGNA", "Magna Investama Mandiri Tbk", "MGNA.JK", "EQUITY", "Indonesia"),
    ("BISI", "BISI International Tbk.", "BISI.JK", "EQUITY", "Indonesia"),
    ("BBCA", "Bank Central Asia Tbk.", "BBCA.JK", "EQUITY", "Indonesia"),
    ("BIPI", "Astrindo Nusantara Infrastruktur Tbk.", "BIPI.JK", "EQUITY", "Indonesia"),
    ("BBRI", "Bank Rakyat Indonesia (Persero) Tbk.", "BBRI.JK", "EQUITY", "Indonesia"),
    ("BMRI", "Bank Mandiri (Persero) Tbk.", "BMRI.JK", "EQUITY", "Indonesia"),
    ("BBNI", "Bank Negara Indonesia (Persero) Tbk.", "BBNI.JK", "EQUITY", "Indonesia"),
    ("TLKM", "Telkom Indonesia (Persero) Tbk.", "TLKM.JK", "EQUITY", "Indonesia"),
    ("ASII", "Astra International Tbk.", "ASII.JK", "EQUITY", "Indonesia"),
    ("GOTO", "GoTo Gojek Tokopedia Tbk.", "GOTO.JK", "EQUITY", "Indonesia"),
    ("ANTM", "Aneka Tambang Tbk.", "ANTM.JK", "EQUITY", "Indonesia"),
    ("ADRO", "Alamtri Resources Indonesia Tbk.", "ADRO.JK", "EQUITY", "Indonesia"),
    ("MDKA", "Merdeka Copper Gold Tbk.", "MDKA.JK", "EQUITY", "Indonesia"),
    ("INDF", "Indofood Sukses Makmur Tbk.", "INDF.JK", "EQUITY", "Indonesia"),
    ("UNVR", "Unilever Indonesia Tbk.", "UNVR.JK", "EQUITY", "Indonesia"),
    ("AMMN", "Amman Mineral Internasional Tbk.", "AMMN.JK", "EQUITY", "Indonesia"),
]


class DataServiceError(Exception):
    """Raised when market data cannot be prepared for charting."""


@dataclass(frozen=True)
class PeriodRequest:
    """Represents a translated period request for yfinance."""

    requested_label: str
    native_period: str | None = None
    start: pd.Timestamp | None = None
    end: pd.Timestamp | None = None


@dataclass
class DataLoadResult:
    """Container for chart-ready market data and compact summary details."""

    data: pd.DataFrame
    symbol: str
    uses_bei_price_fractions: bool
    interval_label: str
    period_label: str
    rows_loaded: int
    first_timestamp: str
    last_timestamp: str
    company_name: str
    current_price: float
    previous_close: float | None
    session_summary: "MarketSessionSummary"
    warnings: list[str]
    insight: "MarketInsight"


@dataclass(frozen=True)
class SymbolSuggestion:
    """Suggestion row used by the search UI."""

    symbol: str
    company_name: str
    provider_symbol: str
    instrument_type: str
    exchange: str = ""


@dataclass(frozen=True)
class MarketInsight:
    """Compact trend/risk summary shown above the chart."""

    trend_label: str
    risk_label: str
    reason: str


@dataclass(frozen=True)
class MarketSessionSummary:
    """Compact daily summary shown below the company name."""

    open_price: float | None
    high_price: float | None
    low_price: float | None
    previous_close: float | None
    average_price: float | None
    value: float | None
    volume: float | None
    lot: float | None
    ara_price: float | None
    arb_price: float | None


def sanitize_symbol(symbol: str) -> str:
    """Normalize a ticker/symbol from the UI."""
    return (symbol or "").strip().upper()


def display_symbol(symbol: str) -> str:
    """Convert provider symbols into a user-friendly display code."""
    cleaned_symbol = sanitize_symbol(symbol)
    if cleaned_symbol == "^JKSE":
        return "IHSG"
    if cleaned_symbol.endswith(INDONESIA_SYMBOL_SUFFIX):
        return cleaned_symbol[: -len(INDONESIA_SYMBOL_SUFFIX)]
    return cleaned_symbol


def resolve_provider_symbol(symbol: str) -> str:
    """Map friendly UI aliases to the upstream market-data ticker symbol."""
    cleaned_symbol = sanitize_symbol(symbol)
    aliased_symbol = SYMBOL_ALIASES.get(cleaned_symbol)
    if aliased_symbol is not None:
        return aliased_symbol

    local_suggestion = _find_exact_local_suggestion(cleaned_symbol)
    if local_suggestion is not None:
        return local_suggestion.provider_symbol

    return cleaned_symbol


def candidate_provider_symbols(symbol: str) -> list[str]:
    """Build provider-symbol candidates, including common Indonesian stock shorthand."""
    cleaned_symbol = sanitize_symbol(symbol)
    resolved_symbol = resolve_provider_symbol(cleaned_symbol)
    candidates = [resolved_symbol]

    if (
        resolved_symbol == cleaned_symbol
        and cleaned_symbol.isalpha()
        and 3 <= len(cleaned_symbol) <= 5
    ):
        indonesia_symbol = f"{cleaned_symbol}{INDONESIA_SYMBOL_SUFFIX}"
        candidates.append(indonesia_symbol)

    return list(dict.fromkeys(candidates))


def _catalog_entry_to_suggestion(entry: tuple[str, str, str, str, str]) -> SymbolSuggestion:
    symbol, company_name, provider_symbol, instrument_type, exchange = entry
    return SymbolSuggestion(
        symbol=symbol,
        company_name=company_name,
        provider_symbol=provider_symbol,
        instrument_type=instrument_type,
        exchange=exchange,
    )


def _find_exact_local_suggestion(symbol: str) -> SymbolSuggestion | None:
    """Return an exact local-catalog match for either display code or provider symbol."""
    cleaned_symbol = sanitize_symbol(symbol)
    if not cleaned_symbol:
        return None

    display_code = display_symbol(cleaned_symbol)
    for entry in LOCAL_SYMBOL_CATALOG:
        suggestion = _catalog_entry_to_suggestion(entry)
        if cleaned_symbol in {
            sanitize_symbol(suggestion.symbol),
            sanitize_symbol(suggestion.provider_symbol),
        }:
            return suggestion
        if display_code and display_code == sanitize_symbol(suggestion.symbol):
            return suggestion

    return None


def _suggestion_sort_key(suggestion: SymbolSuggestion, query: str) -> tuple[int, int, int, str]:
    cleaned_query = sanitize_symbol(query)
    symbol = suggestion.symbol.upper()
    company_name = suggestion.company_name.upper()
    exchange = suggestion.exchange.upper()
    is_indonesia = (
        suggestion.provider_symbol.endswith(INDONESIA_SYMBOL_SUFFIX)
        or suggestion.provider_symbol == "^JKSE"
        or "INDONESIA" in exchange
        or "JAKARTA" in exchange
    )
    if symbol == cleaned_query:
        symbol_rank = 0
    elif symbol.startswith(cleaned_query):
        symbol_rank = 1
    elif cleaned_query in symbol:
        symbol_rank = 2
    elif cleaned_query in company_name:
        symbol_rank = 3
    else:
        symbol_rank = 4
    return (symbol_rank, 0 if is_indonesia else 1, len(symbol), symbol)


def _search_local_catalog(query: str) -> list[SymbolSuggestion]:
    cleaned_query = sanitize_symbol(query)
    if not cleaned_query:
        return []

    matches = []
    for entry in LOCAL_SYMBOL_CATALOG:
        suggestion = _catalog_entry_to_suggestion(entry)
        haystack = f"{suggestion.symbol} {suggestion.company_name}".upper()
        if cleaned_query in haystack:
            matches.append(suggestion)

    return sorted(matches, key=lambda item: _suggestion_sort_key(item, cleaned_query))


def _quote_to_suggestion(quote: dict[str, object]) -> SymbolSuggestion | None:
    raw_symbol = sanitize_symbol(str(quote.get("symbol") or ""))
    quote_type = sanitize_symbol(str(quote.get("quoteType") or ""))
    company_name = str(
        quote.get("longname") or quote.get("shortname") or quote.get("name") or ""
    ).strip()
    exchange = str(quote.get("exchDisp") or quote.get("exchange") or "").strip()

    if not raw_symbol or quote_type not in SEARCHABLE_QUOTE_TYPES:
        return None

    if raw_symbol == "^JKSE" and not company_name:
        company_name = "Indeks Harga Saham Gabungan"

    if not company_name:
        return None

    return SymbolSuggestion(
        symbol=display_symbol(raw_symbol),
        company_name=company_name,
        provider_symbol=raw_symbol,
        instrument_type=quote_type,
        exchange=exchange,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _search_yahoo_quotes(query: str) -> list[SymbolSuggestion]:
    """Search Yahoo Finance for a query and normalize the returned quotes."""
    if requests is None:
        return []

    response = requests.get(
        YAHOO_SEARCH_URL,
        params={
            "q": query,
            "quotesCount": 12,
            "newsCount": 0,
            "listsCount": 0,
            "enableFuzzyQuery": True,
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=4,
    )
    response.raise_for_status()
    payload = response.json()
    quotes = payload.get("quotes") or []

    suggestions: list[SymbolSuggestion] = []
    for quote in quotes:
        if not isinstance(quote, dict):
            continue
        suggestion = _quote_to_suggestion(quote)
        if suggestion is not None:
            suggestions.append(suggestion)

    return suggestions


def _deduplicate_suggestions(suggestions: list[SymbolSuggestion]) -> list[SymbolSuggestion]:
    deduplicated: list[SymbolSuggestion] = []
    seen: set[str] = set()

    for suggestion in suggestions:
        suggestion_key = suggestion.provider_symbol or suggestion.symbol
        if suggestion_key in seen:
            continue
        seen.add(suggestion_key)
        deduplicated.append(suggestion)

    return deduplicated


def resolve_company_name(symbol: str) -> str:
    """Resolve a full company/index name for the displayed symbol."""
    cleaned_symbol = sanitize_symbol(symbol)
    display_code = display_symbol(cleaned_symbol)

    local_suggestion = _find_exact_local_suggestion(cleaned_symbol)
    if local_suggestion is not None:
        return local_suggestion.company_name

    queries = [display_code, cleaned_symbol]
    for query in queries:
        if not query or len(query) < 2:
            continue
        try:
            suggestions = _search_yahoo_quotes(query)
        except Exception:
            continue

        for suggestion in suggestions:
            if cleaned_symbol in {
                sanitize_symbol(suggestion.provider_symbol),
                sanitize_symbol(suggestion.symbol),
            }:
                return suggestion.company_name
            if display_code and display_code == sanitize_symbol(suggestion.symbol):
                return suggestion.company_name

    return display_code or cleaned_symbol


def search_symbol_suggestions(query: str, limit: int = 8) -> list[SymbolSuggestion]:
    """Return user-friendly symbol suggestions with both code and company name."""
    cleaned_query = (query or "").strip()
    if len(cleaned_query) < 2:
        return []

    suggestions: list[SymbolSuggestion] = []
    try:
        suggestions.extend(_search_yahoo_quotes(cleaned_query))
    except Exception:
        pass

    suggestions.extend(_search_local_catalog(cleaned_query))
    suggestions = _deduplicate_suggestions(suggestions)
    suggestions.sort(key=lambda item: _suggestion_sort_key(item, cleaned_query))
    return suggestions[:limit]


def translate_period_selection(period_label: str) -> PeriodRequest:
    """Translate a UI period label into yfinance-compatible arguments."""
    if period_label in {"1wk", "2wk"}:
        lookback_days = 7 if period_label == "1wk" else 14
        end = pd.Timestamp(inclusive_request_end())
        start = end - pd.Timedelta(days=lookback_days)
        return PeriodRequest(requested_label=period_label, start=start, end=end)

    native_period = PERIOD_LABEL_TO_NATIVE.get(period_label)
    if native_period is None:
        raise DataServiceError(f"Unsupported period selection: {period_label}")

    return PeriodRequest(requested_label=period_label, native_period=native_period)


def apply_intraday_guard(
    period_request: PeriodRequest,
    interval_code: str,
) -> tuple[PeriodRequest, list[str]]:
    """Clamp large intraday requests to a predictable, practical lookback."""
    if not is_intraday_interval(interval_code):
        return period_request, []

    requested_days = period_lookback_days(period_request.requested_label, now=utc_now())
    if requested_days is not None and requested_days <= INTRADAY_MAX_LOOKBACK_DAYS:
        return period_request, []

    end = pd.Timestamp(inclusive_request_end())
    start = end - pd.Timedelta(days=INTRADAY_MAX_LOOKBACK_DAYS)
    warning = (
        "Intraday history is limited by Yahoo Finance. "
        f"The selected period was clamped to the last {INTRADAY_MAX_LOOKBACK_DAYS} "
        f"calendar days for {interval_code} data."
    )
    clamped_request = PeriodRequest(
        requested_label=period_request.requested_label,
        start=start,
        end=end,
    )
    return clamped_request, [warning]


@st.cache_data(ttl=300, show_spinner=False)
def _download_history_cached(
    symbol: str,
    interval: str,
    native_period: str | None,
    start_iso: str | None,
    end_iso: str | None,
) -> pd.DataFrame:
    """Download raw OHLCV data from yfinance with caching."""
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

    return yf.download(**kwargs)


def _download_history_with_fallback(
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


def _normalize_datetime_index(index: pd.Index) -> pd.DatetimeIndex:
    """Convert the source index to a timezone-safe, naive UTC DatetimeIndex."""
    timestamps = pd.to_datetime(index, errors="coerce", utc=True)
    if not isinstance(timestamps, pd.DatetimeIndex):
        timestamps = pd.DatetimeIndex(timestamps)
    return timestamps.tz_convert("UTC").tz_localize(None)


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance columns and normalize them to lowercase names."""
    normalized = frame.copy()
    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [str(column[0]).strip().lower() for column in normalized.columns]
    else:
        normalized.columns = [str(column).strip().lower() for column in normalized.columns]

    if "close" not in normalized.columns and "adj close" in normalized.columns:
        normalized["close"] = normalized["adj close"]

    missing = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing:
        raise DataServiceError(
            "The downloaded data is missing required columns: " + ", ".join(missing)
        )

    return normalized[REQUIRED_COLUMNS].copy()


def _normalize_history_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw yfinance output into a clean OHLCV dataframe."""
    if frame is None or frame.empty:
        raise DataServiceError(
            "No market data was returned. Please verify the ticker and try a different period."
        )

    normalized = _normalize_columns(frame)
    normalized.index = _normalize_datetime_index(frame.index)
    normalized = normalized.loc[~normalized.index.isna()].copy()
    normalized = normalized.loc[~normalized.index.duplicated(keep="last")]
    normalized = normalized.sort_index()

    for column in REQUIRED_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized = normalized.dropna(how="all", subset=REQUIRED_COLUMNS)
    normalized = normalized.dropna(subset=["open", "high", "low", "close"])
    normalized["volume"] = normalized["volume"].fillna(0)

    if normalized.empty:
        raise DataServiceError(
            "The response was received, but it did not contain valid OHLCV rows."
        )

    return normalized


def resample_to_4h(frame: pd.DataFrame) -> pd.DataFrame:
    """Build 4-hour candles from 1-hour source data."""
    if frame.empty:
        raise DataServiceError("Cannot resample empty data into 4-hour candles.")

    try:
        resampled = frame.resample("4h").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": lambda values: values.sum(min_count=1),
            }
        )
    except Exception as exc:
        raise DataServiceError("Failed to resample 1-hour data into 4-hour candles.") from exc

    resampled = resampled.dropna(subset=["open", "high", "low", "close"])
    if resampled.empty:
        raise DataServiceError(
            "Unable to construct 4-hour candles from the available 1-hour history."
        )

    return resampled


def _finalize_chart_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure the final dataframe matches lightweight-charts OHLCV expectations."""
    prepared = frame.copy()
    prepared.index.name = "time"
    prepared = prepared.reset_index()
    prepared = prepared[["time", *REQUIRED_COLUMNS]].copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    prepared = prepared.dropna(subset=["time"])
    prepared = prepared.sort_values("time")
    prepared = prepared.drop_duplicates(subset=["time"], keep="last")
    prepared = prepared.dropna(how="all", subset=REQUIRED_COLUMNS)

    if prepared.empty:
        raise DataServiceError("No chartable rows remained after dataframe normalization.")

    is_date_only = (
        prepared["time"].dt.hour.eq(0).all()
        and prepared["time"].dt.minute.eq(0).all()
        and prepared["time"].dt.second.eq(0).all()
    )
    if is_date_only:
        prepared["time"] = prepared["time"].dt.strftime("%Y-%m-%d")
    else:
        prepared["time"] = (
            prepared["time"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(JAKARTA_TIMEZONE)
            .dt.tz_localize(None)
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )

    return prepared


def extract_price_snapshot(frame: pd.DataFrame) -> tuple[float, float | None]:
    """Return the latest close and the previous close for change calculations."""
    close = pd.to_numeric(frame["close"], errors="coerce").dropna()
    if close.empty:
        raise DataServiceError("No valid close prices were available for the selected symbol.")

    current_price = float(close.iloc[-1])
    previous_close = float(close.iloc[-2]) if len(close) >= 2 else None

    if isinstance(close.index, pd.DatetimeIndex) and len(close) >= 2:
        current_day = close.index[-1].date()
        earlier_sessions = close.loc[close.index.date < current_day]
        if not earlier_sessions.empty:
            previous_close = float(earlier_sessions.iloc[-1])

    return current_price, previous_close


def _daily_ohlcv_from_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Build one clean daily OHLCV dataframe from a normalized history frame."""
    if frame.empty:
        return frame

    if not isinstance(frame.index, pd.DatetimeIndex):
        daily_frame = frame.copy()
        return daily_frame.dropna(subset=["open", "high", "low", "close"])

    has_intraday_timestamps = (
        frame.index.hour.any()
        or frame.index.minute.any()
        or frame.index.second.any()
    )
    if not has_intraday_timestamps:
        return frame.dropna(subset=["open", "high", "low", "close"]).copy()

    daily_frame = frame.resample("1D").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": lambda values: values.sum(min_count=1),
        }
    )
    daily_frame = daily_frame.dropna(subset=["open", "high", "low", "close"])
    daily_frame["volume"] = daily_frame["volume"].fillna(0.0)
    return daily_frame


def _bei_tick_step(price: float) -> int:
    """Return the current BEI tick-size step for one price."""
    if price >= 5000:
        return 25
    if price >= 2000:
        return 10
    if price >= 500:
        return 5
    if price >= 200:
        return 2
    return 1


def _round_to_tick(price: float, method: str = "nearest") -> float:
    """Round one price to the valid tick step of its own price range."""
    if price <= 0:
        return 0.0

    step = _bei_tick_step(price)
    scaled_price = price / step
    if method == "down":
        rounded_price = math.floor(scaled_price) * step
    elif method == "up":
        rounded_price = math.ceil(scaled_price) * step
    else:
        rounded_price = round(scaled_price) * step
    return float(max(rounded_price, step))


def _calculate_bei_ara_arb(previous_close: float | None) -> tuple[float | None, float | None]:
    """Calculate ARA and ARB using current BEI percentages effective April 8, 2025."""
    if previous_close is None or previous_close <= 0:
        return None, None

    if previous_close <= 200:
        ara_percent = 0.35
    elif previous_close <= 5000:
        ara_percent = 0.25
    else:
        ara_percent = 0.20
    arb_percent = 0.15

    ara_price = _round_to_tick(previous_close * (1 + ara_percent), method="down")
    arb_price = _round_to_tick(previous_close * (1 - arb_percent), method="up")
    return ara_price, arb_price


def build_market_session_summary(
    daily_frame: pd.DataFrame,
    uses_bei_price_fractions: bool,
) -> MarketSessionSummary:
    """Build one compact daily session summary for the top insight card."""
    if daily_frame.empty:
        return MarketSessionSummary(
            open_price=None,
            high_price=None,
            low_price=None,
            previous_close=None,
            average_price=None,
            value=None,
            volume=None,
            lot=None,
            ara_price=None,
            arb_price=None,
        )

    session_frame = daily_frame.tail(2).copy()
    latest_row = session_frame.iloc[-1]
    previous_close = float(session_frame["close"].iloc[-2]) if len(session_frame) >= 2 else None
    open_price = float(latest_row["open"]) if pd.notna(latest_row["open"]) else None
    high_price = float(latest_row["high"]) if pd.notna(latest_row["high"]) else None
    low_price = float(latest_row["low"]) if pd.notna(latest_row["low"]) else None
    close_price = float(latest_row["close"]) if pd.notna(latest_row["close"]) else None
    volume = float(latest_row["volume"]) if pd.notna(latest_row["volume"]) else None

    average_price: float | None = None
    if None not in {open_price, high_price, low_price, close_price}:
        average_price = (open_price + high_price + low_price + close_price) / 4
        if uses_bei_price_fractions:
            average_price = _round_to_tick(average_price, method="nearest")

    value = average_price * volume if average_price is not None and volume is not None else None
    lot = (volume / 100) if uses_bei_price_fractions and volume is not None else None
    ara_price, arb_price = (
        _calculate_bei_ara_arb(previous_close) if uses_bei_price_fractions else (None, None)
    )

    return MarketSessionSummary(
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        previous_close=previous_close,
        average_price=average_price,
        value=value,
        volume=volume,
        lot=lot,
        ara_price=ara_price,
        arb_price=arb_price,
    )


def _average_true_range(frame: pd.DataFrame, window: int = 14) -> pd.Series:
    """Compute a lightweight ATR series for risk classification."""
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    close = pd.to_numeric(frame["close"], errors="coerce")
    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=window, min_periods=3).mean()


def build_market_insight(frame: pd.DataFrame) -> MarketInsight:
    """Classify the latest price action into a simple trend/risk summary."""
    analysis = frame[["high", "low", "close"]].copy()
    for column in ["high", "low", "close"]:
        analysis[column] = pd.to_numeric(analysis[column], errors="coerce")
    analysis = analysis.dropna(subset=["high", "low", "close"]).tail(120)

    if analysis.empty:
        return MarketInsight(
            trend_label="Downtrend",
            risk_label="High Risk",
            reason="data belum cukup bersih untuk membaca trend dan risk dengan aman.",
        )

    close = analysis["close"]
    high = analysis["high"]
    low = analysis["low"]
    lookback = min(len(close), 20)
    trend_window = min(len(close), max(6, lookback))
    fast_ema = close.ewm(span=8, adjust=False, min_periods=1).mean()
    slow_ema = close.ewm(span=21, adjust=False, min_periods=1).mean()
    atr = _average_true_range(pd.DataFrame({"high": high, "low": low, "close": close}))

    current_price = float(close.iloc[-1])
    earlier_price = float(close.iloc[-trend_window])
    support_level = float(low.tail(lookback).min())
    resistance_level = float(high.tail(lookback).max())
    atr_ratio = float((atr.iloc[-1] / current_price) if current_price and pd.notna(atr.iloc[-1]) else 0.0)
    support_distance = max((current_price - support_level) / current_price, 0.0) if current_price else 0.0
    resistance_distance = (
        max((resistance_level - current_price) / current_price, 0.0) if current_price else 0.0
    )

    trend_is_up = (
        current_price >= float(fast_ema.iloc[-1])
        and float(fast_ema.iloc[-1]) >= float(slow_ema.iloc[-1])
        and current_price >= earlier_price
    )
    trend_label = "Uptrend" if trend_is_up else "Downtrend"

    risk_score = 0
    if trend_label == "Downtrend":
        risk_score += 1
    if atr_ratio >= 0.035:
        risk_score += 1
    if resistance_distance <= 0.04:
        risk_score += 1
    if support_distance <= 0.03:
        risk_score += 1

    risk_label = "High Risk" if risk_score >= 2 else "Low Risk"

    if risk_label == "High Risk":
        reasons = []
        reasons.append("tren masih turun" if trend_label == "Downtrend" else "volatilitas masih cukup tinggi")
        if resistance_distance <= 0.04:
            reasons.append("upside ke resistance cukup sempit")
        if support_distance <= 0.03:
            reasons.append("jarak ke support tipis")
        if atr_ratio >= 0.035 and len(reasons) < 3:
            reasons.append("range pergerakan masih lebar")
    else:
        reasons = []
        reasons.append("tren masih naik" if trend_label == "Uptrend" else "tekanan jual mulai mereda")
        if resistance_distance > 0.04:
            reasons.append("ruang ke resistance masih terbuka")
        if support_distance > 0.03:
            reasons.append("jarak ke support masih aman")
        if atr_ratio < 0.035 and len(reasons) < 3:
            reasons.append("volatilitas relatif terjaga")

    return MarketInsight(
        trend_label=trend_label,
        risk_label=risk_label,
        reason="; ".join(reasons[:3]),
    )


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
        raw_history, resolved_symbol = _download_history_with_fallback(
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

    normalized_history = _normalize_history_dataframe(raw_history)
    if interval_code == "4h":
        normalized_history = resample_to_4h(normalized_history)

    resolved_display_code = display_symbol(resolved_symbol)
    if not display_code:
        display_code = resolved_display_code

    if (
        resolved_symbol != requested_symbol
        and resolved_symbol not in SYMBOL_ALIASES.values()
        and resolved_display_code != display_code
    ):
        warnings.append(
            f"Ticker `{display_code}` otomatis dibaca sebagai `{resolved_display_code}`."
        )

    first_timestamp = format_timestamp(normalized_history.index[0])
    last_timestamp = format_timestamp(normalized_history.index[-1])
    company_name = resolve_company_name(resolved_symbol)
    current_price, previous_close = extract_price_snapshot(normalized_history)
    uses_bei_price_fractions = resolved_symbol.endswith(INDONESIA_SYMBOL_SUFFIX)

    try:
        snapshot_history = _download_history_cached(
            symbol=resolved_symbol,
            interval="1d",
            native_period="1mo",
            start_iso=None,
            end_iso=None,
        )
        normalized_snapshot_history = _normalize_history_dataframe(snapshot_history)
        snapshot_daily_frame = _daily_ohlcv_from_history(normalized_snapshot_history)
    except Exception:
        snapshot_daily_frame = _daily_ohlcv_from_history(normalized_history)

    session_summary = build_market_session_summary(
        snapshot_daily_frame,
        uses_bei_price_fractions=uses_bei_price_fractions,
    )
    chart_frame = _finalize_chart_dataframe(normalized_history)
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

