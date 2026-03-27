from __future__ import annotations

import pandas as pd

from common.time_utils import inclusive_request_end, is_intraday_interval, period_lookback_days, utc_now
from config.chart_options import INTRADAY_MAX_LOOKBACK_DAYS, PERIOD_LABEL_TO_NATIVE
from data.models import DataServiceError, PeriodRequest


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


__all__ = ["apply_intraday_guard", "translate_period_selection"]
