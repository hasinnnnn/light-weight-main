# Financial Charting Streamlit App

This project is a Streamlit app for viewing OHLCV market data in a TradingView-like chart powered by `lightweight-charts-python`. Market data is downloaded from `yfinance`, normalized into a chart-ready dataframe, and rendered with the Streamlit-specific `StreamlitChart` widget.

## Features

- Manual ticker input with automatic trimming and uppercase normalization
- Exact interval options: `5 menit`, `15 menit`, `1 jam`, `4 jam`, `1 hari`
- Exact period options: `1d`, `5d`, `1wk`, `2wk`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `YTD`, `ALL`
- Candlestick OHLCV chart rendered with `lightweight-charts`
- Volume displayed with the main chart configuration
- Compact data summary panel with symbol, interval, period, row count, and timestamps
- Friendly warnings and error messages for invalid symbols, empty responses, fetch failures, and unsupported history ranges

## Project Structure

- `app.py`: Streamlit layout, sidebar controls, session state, and page wiring
- `data_service.py`: symbol sanitization, period translation, yfinance download logic, dataframe normalization, intraday clamping, and 4-hour resampling
- `chart_service.py`: `StreamlitChart` construction, styling, and chart loading
- `utils.py`: shared constants and small date/time helpers

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Example Usage

1. Start the app with `streamlit run app.py`
2. Enter a symbol such as `AAPL`, `MSFT`, `TSLA`, or `BTC-USD`
3. Choose an interval and period from the sidebar
4. Click `Load Chart`

The app auto-loads `AAPL` on first run with:

- Interval: `1 hari`
- Period: `YTD`

## Important Notes

- Intraday history for `5m`, `15m`, `1h`, and derived `4h` data is limited by Yahoo Finance.
- When an intraday request exceeds the app's safe lookback window, the request is automatically clamped to the last `60` calendar days and a Streamlit warning is shown.
- `1wk` and `2wk` use explicit `start` and `end` date logic instead of a native yfinance period string.
- `YTD` maps to `ytd`.
- `ALL` maps to `max`.

## How 4-Hour Candles Work

`4 jam` is not requested directly from yfinance. The app downloads `1h` data first and then resamples it in pandas using:

- `open = first`
- `high = max`
- `low = min`
- `close = last`
- `volume = sum`

Rows without valid OHLC values are dropped after resampling so the chart only receives usable candles.
