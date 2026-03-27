from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


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
