from __future__ import annotations

INTERVAL_OPTIONS = ["5 menit", "15 menit", "1 jam", "4 jam", "1 hari", "1 minggu"]
PERIOD_OPTIONS = [
    "1d",
    "5d",
    "1wk",
    "2wk",
    "1mo",
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
    "YTD",
    "ALL",
]

INTERVAL_LABEL_TO_CODE = {
    "5 menit": "5m",
    "15 menit": "15m",
    "1 jam": "1h",
    "4 jam": "4h",
    "1 hari": "1d",
    "1 minggu": "1wk",
}

PERIOD_LABEL_TO_NATIVE = {
    "1d": "1d",
    "5d": "5d",
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    "YTD": "ytd",
    "ALL": "max",
}

INTRADAY_INTERVALS = {"5m", "15m", "1h", "4h"}
INTRADAY_MAX_LOOKBACK_DAYS = 60
JAKARTA_TIMEZONE = "Asia/Jakarta"
