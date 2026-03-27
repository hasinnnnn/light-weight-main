from data.history_parts.download import download_history_with_fallback
from data.history_parts.normalize import normalize_history_dataframe, daily_ohlcv_from_history, extract_price_snapshot
raw, symbol = download_history_with_fallback(['BUMI.JK'], '1d', '1mo', None, None)
print('symbol', symbol)
normalized = normalize_history_dataframe(raw)
daily = daily_ohlcv_from_history(normalized)
print(daily.tail().to_string())
print('price snapshot', extract_price_snapshot(normalized))
