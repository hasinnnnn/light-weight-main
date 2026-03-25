from __future__ import annotations

from typing import Any

import pandas as pd

MAIN_CHART_HEIGHT = 680
INDICATOR_CHART_HEIGHT = 240
VOLUME_PANEL_TOP_MARGIN = 0.78
VOLUME_PANEL_BOTTOM_MARGIN = 0.0
VOLUME_MA_WINDOW = 20
OVERLAY_INDICATOR_KEYS = {
    "EMA",
    "EMA_CROSS",
    "DOUBLE_EMA",
    "TRIPLE_EMA",
    "MA",
    "MA_CROSS",
    "DOUBLE_MA",
    "TRIPLE_MA",
    "BOLLINGER_BANDS",
    "VWAP",
    "PARABOLIC_SAR",
    "TRENDLINE",
    "MAJOR_TRENDLINE",
    "NEAREST_SUPPORT_RESISTANCE",
    "STRONG_SUPPORT_RESISTANCE",
    "FIBONACCI",
    "PIVOT_POINT_STANDARD",
}
PANEL_INDICATOR_KEYS = {"ATR", "PRICE_OSCILLATOR", "RSI", "MACD", "STOCHASTIC", "STOCHASTIC_RSI"}
EMA_COLORS = ["#38bdf8", "#f59e0b", "#22c55e"]
MA_COLORS = ["#fb923c", "#a855f7", "#14b8a6"]
BOLLINGER_COLORS = {
    "upper": "#60a5fa",
    "basis": "#f8fafc",
    "lower": "#f472b6",
}
VWAP_COLOR = "#fbbf24"
PARABOLIC_SAR_COLOR = "#38bdf8"
ATR_COLOR = "#f59e0b"
PRICE_OSCILLATOR_COLOR = "#38bdf8"
TRENDLINE_COLORS = {
    "up": "#22c55e",
    "down": "#ef4444",
}
NEAREST_SUPPORT_RESISTANCE_COLORS = {
    "resistance": "#22c55e",
    "support": "#ef4444",
}
NEAREST_SUPPORT_RESISTANCE_FILL_ALPHA = 0.16
NEAREST_SUPPORT_RESISTANCE_LINE_ALPHA = 0.95
STRONG_SUPPORT_RESISTANCE_COLORS = {
    "resistance": "#22c55e",
    "support": "#ef4444",
}
STRONG_SUPPORT_RESISTANCE_FILL_ALPHA = 0.20
STRONG_SUPPORT_RESISTANCE_LINE_ALPHA = 0.98
STRONG_SUPPORT_RESISTANCE_VOLUME_THRESHOLD = 1.15
STOCHASTIC_COLORS = {
    "k": "#38bdf8",
    "d": "#f59e0b",
}
FIBONACCI_LEVELS = [
    (0.0, "#d1d5db"),
    (0.236, "#ef4444"),
    (0.382, "#f59e0b"),
    (0.5, "#22c55e"),
    (0.618, "#14b8a6"),
    (0.786, "#22d3ee"),
    (1.0, "#9ca3af"),
]
FIBONACCI_FILL_ALPHAS = [0.14, 0.12, 0.11, 0.11, 0.11, 0.08]
FIBONACCI_MONOCHROME_DEFAULT = "#60a5fa"
PIVOT_LEVELS = [
    ("PP", "#f8fafc"),
    ("R1", "#fb7185"),
    ("R2", "#ef4444"),
    ("R3", "#b91c1c"),
    ("S1", "#60a5fa"),
    ("S2", "#2563eb"),
    ("S3", "#1d4ed8"),
]


class ChartServiceError(Exception):
    """Raised when the chart layer cannot be initialized."""


def _get_streamlit_chart_class() -> Any:
    """Import the Streamlit chart widget lazily so the app can fail gracefully."""
    try:
        from lightweight_charts.widgets import StreamlitChart
    except ModuleNotFoundError as exc:
        raise ChartServiceError(
            "Package `lightweight-charts` belum terpasang. "
            "Install dulu dengan `pip install -r requirements.txt` "
            "atau `pip install lightweight-charts`, lalu jalankan ulang app."
        ) from exc

    return StreamlitChart


def build_streamlit_chart(
    symbol: str,
    interval_label: str,
    display_name: str | None = None,
    height: int = MAIN_CHART_HEIGHT,
) -> Any:
    """Create and style a TradingView-like Streamlit chart."""
    streamlit_chart_class = _get_streamlit_chart_class()
    chart = streamlit_chart_class(width=None, height=height)
    watermark_text = display_name or symbol

    chart.layout(
        background_color="#0b1220",
        text_color="#d6deeb",
        font_size=13,
        font_family="Trebuchet MS",
    )
    chart.grid(
        vert_enabled=True,
        horz_enabled=True,
        color="rgba(148, 163, 184, 0.15)",
        style="solid",
    )
    chart.candle_style(
        up_color="#22c55e",
        down_color="#ef4444",
        border_up_color="#22c55e",
        border_down_color="#ef4444",
        wick_up_color="#94f4b2",
        wick_down_color="#fca5a5",
    )
    chart.volume_config(
        scale_margin_top=VOLUME_PANEL_TOP_MARGIN,
        scale_margin_bottom=VOLUME_PANEL_BOTTOM_MARGIN,
        up_color="rgba(34, 197, 94, 0.45)",
        down_color="rgba(239, 68, 68, 0.45)",
    )
    chart.crosshair(
        mode="normal",
        vert_visible=True,
        vert_color="rgba(148, 163, 184, 0.35)",
        vert_style="dotted",
        horz_visible=True,
        horz_color="rgba(148, 163, 184, 0.35)",
        horz_style="dotted",
    )
    chart.legend(
        visible=True,
        ohlc=True,
        percent=False,
        lines=True,
        color="#d6deeb",
        font_size=12,
        color_based_on_candle=True,
    )
    chart.price_scale(
        auto_scale=True,
        scale_margin_top=0.08,
        scale_margin_bottom=0.22,
        border_visible=False,
        text_color="#cbd5e1",
    )
    chart.time_scale(
        visible=True,
        time_visible=True,
        seconds_visible=False,
        border_visible=False,
    )
    chart.watermark(
        text=watermark_text,
        font_size=42,
        color="rgba(148, 163, 184, 0.10)",
    )
    chart.price_line(label_visible=True, line_visible=True)

    return chart


def _bei_price_fraction_step(price: float) -> int:
    """Return the BEI tick-size step based on one latest price snapshot."""
    if price >= 5000:
        return 25
    if price >= 2000:
        return 10
    if price >= 500:
        return 5
    if price >= 200:
        return 2
    return 1


def _apply_bei_price_fraction_format(chart: Any, latest_price: float) -> None:
    """Apply BEI tick-size formatting to price scale and crosshair labels."""
    fraction_step = _bei_price_fraction_step(latest_price)
    chart.precision(0)
    chart.run_script(
        f"""
        {chart.id}.__beiFractionStep = {fraction_step};
        {chart.id}.__beiFractionFormatter = (rawPrice) => {{
            const price = Number(rawPrice);
            if (!Number.isFinite(price)) return '';
            const step = Number({chart.id}.__beiFractionStep) || 1;
            const roundedPrice = Math.round(price / step) * step;
            return roundedPrice.toLocaleString('en-US', {{
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }});
        }};
        {chart.id}.series.applyOptions({{
            priceFormat: {{
                type: 'price',
                precision: 0,
                minMove: {fraction_step}
            }}
        }});
        {chart.id}.chart.applyOptions({{
            localization: {{
                priceFormatter: {chart.id}.__beiFractionFormatter
            }}
        }});
        """
    )


def _build_price_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare the candle dataframe without the built-in volume overlay."""
    price_frame = data.drop(columns=["volume"], errors="ignore").copy()
    for column in ["open", "high", "low", "close"]:
        if column in price_frame:
            price_frame[column] = pd.to_numeric(price_frame[column], errors="coerce")
    return price_frame


def _build_indicator_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare a numeric source dataframe for technical indicators."""
    indicator_frame = data[["time", "close"]].copy()
    indicator_frame["close"] = pd.to_numeric(indicator_frame["close"], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["close"])
    return indicator_frame


def _build_moving_average_dataframe(
    data: pd.DataFrame,
    length: int,
    line_name: str,
    method: str,
) -> pd.DataFrame:
    """Prepare one EMA or MA series from close prices."""
    indicator_frame = _build_indicator_source(data)
    close = indicator_frame["close"]

    if method == "ema":
        line_values = close.ewm(span=length, adjust=False, min_periods=1).mean()
    else:
        line_values = close.rolling(window=length, min_periods=1).mean()

    indicator_frame[line_name] = line_values
    indicator_frame = indicator_frame.dropna(subset=[line_name])
    return indicator_frame[["time", line_name]]


def _build_cross_moving_average_dataframe(
    data: pd.DataFrame,
    fast_length: int,
    slow_length: int,
    method: str,
) -> pd.DataFrame:
    """Prepare two moving-average series in one dataframe for cross detection."""
    indicator_frame = _build_indicator_source(data)
    close = indicator_frame["close"]

    if method == "ema":
        indicator_frame["fast"] = close.ewm(
            span=fast_length,
            adjust=False,
            min_periods=1,
        ).mean()
        indicator_frame["slow"] = close.ewm(
            span=slow_length,
            adjust=False,
            min_periods=1,
        ).mean()
    else:
        indicator_frame["fast"] = close.rolling(window=fast_length, min_periods=1).mean()
        indicator_frame["slow"] = close.rolling(window=slow_length, min_periods=1).mean()

    indicator_frame = indicator_frame.dropna(subset=["fast", "slow"])
    return indicator_frame[["time", "fast", "slow"]]


def _build_high_low_close_volume_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare a numeric dataframe for indicators that need HLCV data."""
    indicator_frame = data[["time", "high", "low", "close", "volume"]].copy()
    for column in ["high", "low", "close", "volume"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["high", "low", "close"])
    return indicator_frame


def _build_datetime_ohlcv_source(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare one datetime-aware OHLCV dataframe for higher-timeframe analysis."""
    indicator_frame = data[["time", "open", "high", "low", "close", "volume"]].copy()
    indicator_frame["time"] = pd.to_datetime(indicator_frame["time"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame["volume"] = indicator_frame["volume"].fillna(0.0)
    indicator_frame = indicator_frame.dropna(subset=["time", "open", "high", "low", "close"])
    indicator_frame = indicator_frame.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    return indicator_frame.reset_index(drop=True)


def _is_date_only_chart_data(data: pd.DataFrame) -> bool:
    """Return whether the chart uses date-only timestamps."""
    if data.empty:
        return False
    first_time_value = str(data["time"].iloc[0])
    return " " not in first_time_value


def _resample_datetime_ohlcv_frame(
    frame: pd.DataFrame,
    rule: str,
) -> pd.DataFrame:
    """Resample one datetime OHLCV frame into a higher timeframe."""
    if frame.empty:
        return frame

    resampled = (
        frame.set_index("time")
        .resample(rule)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": lambda values: values.sum(min_count=1),
            }
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return resampled


def _select_strong_sr_analysis_frame(
    frame: pd.DataFrame,
    interval_label: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """Choose the higher-timeframe source used for strong support/resistance analysis."""
    normalized_interval = str(interval_label or "").strip().casefold()

    if normalized_interval in {"5 menit", "15 menit", "1 jam"}:
        resampled_frame = _resample_datetime_ohlcv_frame(frame, "4h")
        if not resampled_frame.empty:
            return resampled_frame, "4H"
    elif normalized_interval == "4 jam":
        resampled_frame = _resample_datetime_ohlcv_frame(frame, "1D")
        if not resampled_frame.empty:
            return resampled_frame, "Daily"
    elif normalized_interval == "1 hari":
        return frame, "Daily"
    elif normalized_interval == "1 minggu":
        return frame, "Weekly"

    if frame.empty:
        return frame, "Current"

    has_intraday_timestamps = (
        frame["time"].dt.hour.ne(0)
        | frame["time"].dt.minute.ne(0)
        | frame["time"].dt.second.ne(0)
    ).any()
    if has_intraday_timestamps:
        resampled_frame = _resample_datetime_ohlcv_frame(frame, "4h")
        if not resampled_frame.empty:
            return resampled_frame, "4H"
        return frame, "Intraday"
    return frame, "Daily"


def _select_major_trend_analysis_frame(
    frame: pd.DataFrame,
    interval_label: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """Choose the higher-timeframe source used for major trendline analysis."""
    normalized_interval = str(interval_label or "").strip().casefold()

    if normalized_interval in {"5 menit", "15 menit", "1 jam", "4 jam"}:
        daily_frame = _resample_datetime_ohlcv_frame(frame, "1D")
        weekly_frame = _resample_datetime_ohlcv_frame(daily_frame, "W-FRI")
        if len(weekly_frame) >= 12:
            return weekly_frame, "Weekly"
        if not daily_frame.empty:
            return daily_frame, "Daily"
    elif normalized_interval == "1 hari":
        weekly_frame = _resample_datetime_ohlcv_frame(frame, "W-FRI")
        if len(weekly_frame) >= 12:
            return weekly_frame, "Weekly"
        return frame, "Daily"
    elif normalized_interval == "1 minggu":
        return frame, "Weekly"

    if frame.empty:
        return frame, "Current"

    has_intraday_timestamps = (
        frame["time"].dt.hour.ne(0)
        | frame["time"].dt.minute.ne(0)
        | frame["time"].dt.second.ne(0)
    ).any()
    if has_intraday_timestamps:
        daily_frame = _resample_datetime_ohlcv_frame(frame, "1D")
        weekly_frame = _resample_datetime_ohlcv_frame(daily_frame, "W-FRI")
        if len(weekly_frame) >= 12:
            return weekly_frame, "Weekly"
        if not daily_frame.empty:
            return daily_frame, "Daily"
        return frame, "Intraday"

    weekly_frame = _resample_datetime_ohlcv_frame(frame, "W-FRI")
    if len(weekly_frame) >= 12:
        return weekly_frame, "Weekly"
    return frame, "Daily"


def _build_volume_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare custom volume bars and a volume moving average line."""
    volume_frame = data[["time", "open", "close", "volume"]].copy()
    for column in ["open", "close", "volume"]:
        volume_frame[column] = pd.to_numeric(volume_frame[column], errors="coerce")
    volume_frame = volume_frame.dropna(subset=["volume"])
    volume_frame["color"] = "rgba(239, 68, 68, 0.45)"
    volume_frame.loc[
        volume_frame["close"] >= volume_frame["open"], "color"
    ] = "rgba(34, 197, 94, 0.45)"
    line_name = f"Volume MA {VOLUME_MA_WINDOW}"
    volume_frame[line_name] = volume_frame["volume"].rolling(
        window=VOLUME_MA_WINDOW,
        min_periods=1,
    ).mean()
    return volume_frame[["time", "volume", "color", line_name]]


def _build_bollinger_bands_dataframe(
    data: pd.DataFrame,
    length: int,
    deviation: int,
) -> pd.DataFrame:
    """Prepare Bollinger Bands values from close prices."""
    indicator_frame = _build_indicator_source(data)
    close = indicator_frame["close"]
    basis_name = f"BB Basis {length}"
    upper_name = f"BB Upper {length}"
    lower_name = f"BB Lower {length}"

    basis = close.rolling(window=length, min_periods=1).mean()
    standard_deviation = close.rolling(window=length, min_periods=1).std(ddof=0)
    indicator_frame[basis_name] = basis
    indicator_frame[upper_name] = basis + (standard_deviation * deviation)
    indicator_frame[lower_name] = basis - (standard_deviation * deviation)
    return indicator_frame[["time", upper_name, basis_name, lower_name]]


def _build_vwap_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare VWAP values from price and volume data."""
    indicator_frame = _build_high_low_close_volume_source(data)
    if indicator_frame.empty:
        return indicator_frame

    timestamps = pd.to_datetime(indicator_frame["time"], errors="coerce")
    typical_price = (
        indicator_frame["high"] + indicator_frame["low"] + indicator_frame["close"]
    ) / 3
    weighted_price = typical_price * indicator_frame["volume"].fillna(0)
    is_intraday = (
        timestamps.dt.hour.ne(0)
        | timestamps.dt.minute.ne(0)
        | timestamps.dt.second.ne(0)
    ).any()

    if is_intraday:
        groups = timestamps.dt.date.astype(str)
    else:
        groups = pd.Series(["all"] * len(indicator_frame), index=indicator_frame.index)

    cumulative_weighted_price = weighted_price.groupby(groups).cumsum()
    cumulative_volume = indicator_frame["volume"].fillna(0).groupby(groups).cumsum()
    indicator_frame["VWAP"] = cumulative_weighted_price.div(cumulative_volume.replace(0, pd.NA))
    indicator_frame["VWAP"] = indicator_frame["VWAP"].fillna(indicator_frame["close"])
    return indicator_frame[["time", "VWAP"]]


def _build_parabolic_sar_dataframe(
    data: pd.DataFrame,
    acceleration: float = 0.02,
    max_acceleration: float = 0.2,
) -> pd.DataFrame:
    """Prepare Parabolic SAR values from high/low price action."""
    indicator_frame = _build_high_low_close_volume_source(data)[["time", "high", "low", "close"]].copy()
    if len(indicator_frame) < 2:
        return indicator_frame.iloc[0:0]

    high_series = pd.to_numeric(indicator_frame["high"], errors="coerce").reset_index(drop=True)
    low_series = pd.to_numeric(indicator_frame["low"], errors="coerce").reset_index(drop=True)
    close_series = pd.to_numeric(indicator_frame["close"], errors="coerce").reset_index(drop=True)

    is_uptrend = bool(close_series.iloc[1] >= close_series.iloc[0])
    extreme_point = float(high_series.iloc[0] if is_uptrend else low_series.iloc[0])
    acceleration_factor = float(acceleration)
    sar_values = [float(low_series.iloc[0] if is_uptrend else high_series.iloc[0])]
    positions = ["below" if is_uptrend else "above"]

    for index in range(1, len(indicator_frame)):
        previous_sar = sar_values[-1]
        current_sar = previous_sar + (acceleration_factor * (extreme_point - previous_sar))

        if is_uptrend:
            if index >= 2:
                current_sar = min(
                    current_sar,
                    float(low_series.iloc[index - 1]),
                    float(low_series.iloc[index - 2]),
                )
            else:
                current_sar = min(current_sar, float(low_series.iloc[index - 1]))

            if float(low_series.iloc[index]) < current_sar:
                is_uptrend = False
                current_sar = extreme_point
                extreme_point = float(low_series.iloc[index])
                acceleration_factor = float(acceleration)
            else:
                if float(high_series.iloc[index]) > extreme_point:
                    extreme_point = float(high_series.iloc[index])
                    acceleration_factor = min(
                        acceleration_factor + float(acceleration),
                        float(max_acceleration),
                    )
        else:
            if index >= 2:
                current_sar = max(
                    current_sar,
                    float(high_series.iloc[index - 1]),
                    float(high_series.iloc[index - 2]),
                )
            else:
                current_sar = max(current_sar, float(high_series.iloc[index - 1]))

            if float(high_series.iloc[index]) > current_sar:
                is_uptrend = True
                current_sar = extreme_point
                extreme_point = float(high_series.iloc[index])
                acceleration_factor = float(acceleration)
            else:
                if float(low_series.iloc[index]) < extreme_point:
                    extreme_point = float(low_series.iloc[index])
                    acceleration_factor = min(
                        acceleration_factor + float(acceleration),
                        float(max_acceleration),
                    )

        sar_values.append(float(current_sar))
        positions.append("below" if is_uptrend else "above")

    candle_range = (high_series - low_series).abs()
    median_candle_range = float(candle_range.dropna().median()) if not candle_range.dropna().empty else 0.0
    latest_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0
    display_offset = max(median_candle_range * 0.22, abs(latest_close) * 0.0012, 0.01)

    psar_series = pd.Series(sar_values, index=indicator_frame.index, dtype="float64")
    position_series = pd.Series(positions, index=indicator_frame.index, dtype="object")
    psar_series.loc[position_series.eq("above")] = (
        psar_series.loc[position_series.eq("above")] + display_offset
    )
    psar_series.loc[position_series.eq("below")] = (
        psar_series.loc[position_series.eq("below")] - display_offset
    )

    indicator_frame["Parabolic SAR"] = psar_series
    indicator_frame["position"] = positions
    indicator_frame = indicator_frame.dropna(subset=["Parabolic SAR"])
    return indicator_frame[["time", "Parabolic SAR", "position"]]


def _split_parabolic_sar_segments(psar_frame: pd.DataFrame) -> list[pd.DataFrame]:
    """Split PSAR runs whenever the side flips so dots do not connect across reversals."""
    if psar_frame.empty:
        return []

    segmented_frame = psar_frame.copy().reset_index(drop=True)
    segmented_frame["segment"] = segmented_frame["position"].ne(
        segmented_frame["position"].shift(1)
    ).cumsum()

    segments: list[pd.DataFrame] = []
    for _, segment_frame in segmented_frame.groupby("segment", sort=True):
        if segment_frame.empty:
            continue
        segments.append(segment_frame[["time", "Parabolic SAR"]].copy())
    return segments


def _build_rsi_series(close: pd.Series, window: int) -> pd.Series:
    """Calculate RSI values from one close-price series."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    average_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    relative_strength = average_gain.div(average_loss.replace(0, pd.NA))
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.where(average_loss.ne(0), 100.0)
    rsi = rsi.where(~((average_gain == 0) & (average_loss == 0)), 50.0)
    return rsi


def _indicator_key(indicator: dict[str, Any]) -> str:
    """Return one normalized indicator key."""
    return str(indicator.get("key") or "").strip().upper()


def _indicator_params(indicator: dict[str, Any]) -> dict[str, int]:
    """Return the parameter dictionary for one indicator config."""
    raw_params = indicator.get("params") or {}
    return {str(name): int(value) for name, value in raw_params.items()}


def _indicator_colors(indicator: dict[str, Any]) -> dict[str, str]:
    """Return the color dictionary for one indicator config."""
    raw_colors = indicator.get("colors") or {}
    return {str(name): str(value) for name, value in raw_colors.items()}


def _indicator_visible(indicator: dict[str, Any]) -> bool:
    """Return whether this indicator should be rendered."""
    return bool(indicator.get("visible", True))


def _with_alpha(color: str, alpha: float) -> str:
    """Convert one hex/rgb color string into rgba with a custom alpha."""
    normalized_color = str(color).strip()
    bounded_alpha = max(0.0, min(1.0, float(alpha)))

    if normalized_color.startswith("#"):
        hex_value = normalized_color.lstrip("#")
        if len(hex_value) == 3:
            hex_value = "".join(character * 2 for character in hex_value)
        if len(hex_value) == 6:
            red = int(hex_value[0:2], 16)
            green = int(hex_value[2:4], 16)
            blue = int(hex_value[4:6], 16)
            return f"rgba({red}, {green}, {blue}, {bounded_alpha:.2f})"

    if normalized_color.lower().startswith("rgba("):
        raw_values = normalized_color[5:-1].split(",")
        if len(raw_values) >= 3:
            red, green, blue = [int(float(value.strip())) for value in raw_values[:3]]
            return f"rgba({red}, {green}, {blue}, {bounded_alpha:.2f})"

    if normalized_color.lower().startswith("rgb("):
        raw_values = normalized_color[4:-1].split(",")
        if len(raw_values) >= 3:
            red, green, blue = [int(float(value.strip())) for value in raw_values[:3]]
            return f"rgba({red}, {green}, {blue}, {bounded_alpha:.2f})"

    return normalized_color


def _format_indicator_title(indicator: dict[str, Any]) -> str:
    """Build a compact title for indicator panels."""
    indicator_key = _indicator_key(indicator)
    params = _indicator_params(indicator)
    title_prefix = str(indicator.get("title_prefix") or "").strip()

    if indicator_key == "ATR":
        title = f"ATR {params.get('length', 14)}"
    elif indicator_key == "PRICE_OSCILLATOR":
        title = (
            f"Price Oscillator {params.get('fast_length', 12)} / "
            f"{params.get('slow_length', 26)}"
        )
    elif indicator_key == "RSI":
        title = f"RSI {params.get('length', 14)}"
    elif indicator_key == "MACD":
        title = (
            f"MACD {params.get('fast_length', 12)} / "
            f"{params.get('slow_length', 26)} / {params.get('signal_length', 9)}"
        )
    elif indicator_key == "STOCHASTIC":
        title = (
            f"Stochastic {params.get('k_length', 14)} / "
            f"{params.get('k_smoothing', 3)} / {params.get('d_length', 3)}"
        )
    elif indicator_key == "STOCHASTIC_RSI":
        title = (
            f"Stochastic RSI {params.get('rsi_length', 14)} / "
            f"{params.get('stoch_length', 14)} / {params.get('k_smoothing', 3)} / "
            f"{params.get('d_length', 3)}"
        )
    else:
        title = indicator_key

    return f"{title_prefix} - {title}" if title_prefix else title


def _build_cross_markers(
    series_frame: pd.DataFrame,
    fast_column: str,
    slow_column: str,
    color: str,
) -> list[dict[str, Any]]:
    """Build marker definitions for cross events between two series."""
    if series_frame.empty or len(series_frame) < 2:
        return []

    cross_frame = series_frame[["time", fast_column, slow_column]].copy()
    cross_frame["difference"] = cross_frame[fast_column] - cross_frame[slow_column]
    cross_frame["state"] = 0.0
    cross_frame.loc[cross_frame["difference"] > 0, "state"] = 1.0
    cross_frame.loc[cross_frame["difference"] < 0, "state"] = -1.0
    cross_frame["state"] = cross_frame["state"].replace(0.0, float("nan")).ffill()
    cross_frame["previous_state"] = cross_frame["state"].shift(1)
    cross_points = cross_frame.loc[
        cross_frame["state"].notna()
        & cross_frame["previous_state"].notna()
        & cross_frame["state"].ne(cross_frame["previous_state"])
    ]

    markers = []
    for row in cross_points.itertuples(index=False):
        markers.append(
            {
                "time": row.time,
                "position": "below" if row.state > 0 else "above",
                "shape": "circle",
                "color": color,
                "text": "+",
            }
        )
    return markers


def _collect_pivot_points(
    frame: pd.DataFrame,
    column: str,
    window: int,
) -> list[dict[str, Any]]:
    """Collect local swing highs or lows from a recent price frame."""
    if frame.empty or len(frame) < (window * 2) + 1:
        return []

    price_series = pd.to_numeric(frame[column], errors="coerce").reset_index(drop=True)
    time_series = frame["time"].reset_index(drop=True)
    pivot_points: list[dict[str, Any]] = []

    for index in range(window, len(price_series) - window):
        current_price = price_series.iloc[index]
        if pd.isna(current_price):
            continue

        local_slice = price_series.iloc[index - window : index + window + 1]
        local_extreme = local_slice.min() if column == "low" else local_slice.max()
        if current_price != local_extreme:
            continue

        if index > 0 and price_series.iloc[index - 1] == current_price:
            continue

        pivot_points.append(
            {
                "index": index,
                "time": time_series.iloc[index],
                "price": float(current_price),
            }
        )

    return pivot_points


def _trendline_tolerance(frame: pd.DataFrame) -> float:
    """Return a small tolerance so minor wick noise does not invalidate a trendline."""
    high_series = pd.to_numeric(frame["high"], errors="coerce")
    low_series = pd.to_numeric(frame["low"], errors="coerce")
    close_series = pd.to_numeric(frame["close"], errors="coerce")
    price_range = float(high_series.max() - low_series.min())
    latest_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0
    if price_range > 0:
        return price_range * 0.015
    return max(abs(latest_close) * 0.002, 0.01)


def _true_cluster_event_dates(mask: pd.Series, time_series: pd.Series) -> list[str]:
    """Return one date label for each contiguous True cluster."""
    normalized_mask = mask.fillna(False).astype(bool)
    if normalized_mask.empty:
        return []

    transition_mask = normalized_mask & ~normalized_mask.shift(1, fill_value=False)
    raw_event_times = time_series.loc[transition_mask]
    event_dates: list[str] = []
    seen_dates: set[str] = set()

    for raw_time in raw_event_times:
        parsed_time = pd.to_datetime(raw_time, errors="coerce")
        if pd.isna(parsed_time):
            date_label = str(raw_time).replace("T", " ").split(" ")[0]
        else:
            date_label = parsed_time.strftime("%Y-%m-%d")

        if date_label and date_label not in seen_dates:
            seen_dates.add(date_label)
            event_dates.append(date_label)

    return event_dates


def _score_trendline_candidate(
    frame: pd.DataFrame,
    start_pivot: dict[str, Any],
    end_pivot: dict[str, Any],
    direction: str,
) -> dict[str, Any] | None:
    """Score one trendline candidate so the most recent clean line can be selected."""
    start_index = int(start_pivot["index"])
    end_index = int(end_pivot["index"])
    if end_index <= start_index:
        return None

    span = end_index - start_index
    slope = (float(end_pivot["price"]) - float(start_pivot["price"])) / span
    if direction == "up" and slope <= 0:
        return None
    if direction == "down" and slope >= 0:
        return None

    last_index = len(frame) - 1
    projected_end_price = float(end_pivot["price"]) + (slope * (last_index - end_index))
    if pd.isna(projected_end_price) or projected_end_price <= 0:
        return None

    comparison_frame = frame.iloc[start_index : last_index + 1]
    line_values = pd.Series(
        [
            float(start_pivot["price"]) + (slope * (index - start_index))
            for index in range(start_index, last_index + 1)
        ],
        index=comparison_frame.index,
        dtype="float64",
    )
    tolerance = _trendline_tolerance(frame)

    if direction == "up":
        reference_series = pd.to_numeric(comparison_frame["low"], errors="coerce")
        violations = int(reference_series.lt(line_values - tolerance).sum())
    else:
        reference_series = pd.to_numeric(comparison_frame["high"], errors="coerce")
        violations = int(reference_series.gt(line_values + tolerance).sum())

    close_series = pd.to_numeric(comparison_frame["close"], errors="coerce")
    latest_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    latest_line_value = float(line_values.iloc[-1])
    breakout_dates = _true_cluster_event_dates(
        close_series.gt(line_values + tolerance),
        comparison_frame["time"],
    )
    breakdown_dates = _true_cluster_event_dates(
        close_series.lt(line_values - tolerance),
        comparison_frame["time"],
    )
    breakout_count = len(breakout_dates)
    breakdown_count = len(breakdown_dates)

    previous_close = float(close_series.iloc[-2]) if len(close_series) >= 2 else latest_close
    previous_line_value = float(line_values.iloc[-2]) if len(line_values) >= 2 else latest_line_value
    previous_above = previous_close > previous_line_value + tolerance
    previous_below = previous_close < previous_line_value - tolerance
    latest_above = latest_close > latest_line_value + tolerance
    latest_below = latest_close < latest_line_value - tolerance

    if direction == "up":
        if latest_below and not previous_below:
            latest_signal = "fresh_breakdown"
        elif latest_below:
            latest_signal = "breakdown"
        elif breakdown_count > 0:
            latest_signal = "reclaimed"
        elif abs(latest_close - latest_line_value) <= tolerance:
            latest_signal = "retest"
        else:
            latest_signal = "holding"
    else:
        if latest_above and not previous_above:
            latest_signal = "fresh_breakout"
        elif latest_above:
            latest_signal = "breakout"
        elif breakout_count > 0:
            latest_signal = "rejected"
        elif abs(latest_close - latest_line_value) <= tolerance:
            latest_signal = "retest"
        else:
            latest_signal = "holding"

    return {
        "direction": direction,
        "start_index": start_index,
        "end_index": end_index,
        "start_time": start_pivot["time"],
        "start_value": float(start_pivot["price"]),
        "end_pivot_time": end_pivot["time"],
        "end_pivot_value": float(end_pivot["price"]),
        "end_time": frame["time"].iloc[-1],
        "end_value": projected_end_price,
        "slope": slope,
        "tolerance": tolerance,
        "line_value": latest_line_value,
        "violations": violations,
        "breakout_count": breakout_count,
        "breakdown_count": breakdown_count,
        "breakout_dates": breakout_dates,
        "breakdown_dates": breakdown_dates,
        "latest_signal": latest_signal,
        "last_pivot_gap": last_index - end_index,
        "distance": abs(latest_close - projected_end_price),
        "span": span,
    }


def _build_fallback_trendline_candidate(
    frame: pd.DataFrame,
    direction: str,
) -> dict[str, Any] | None:
    """Fallback to broad recent extremes if pivot detection finds no clean pair."""
    if len(frame) < 6:
        return None

    split_index = max(len(frame) // 2, 2)
    first_half = frame.iloc[:split_index]
    second_half = frame.iloc[split_index:-1]
    if first_half.empty or second_half.empty:
        return None

    pivot_column = "low" if direction == "up" else "high"
    first_series = pd.to_numeric(first_half[pivot_column], errors="coerce")
    second_series = pd.to_numeric(second_half[pivot_column], errors="coerce")
    if first_series.empty or second_series.empty:
        return None

    first_index = int(first_series.idxmin() if direction == "up" else first_series.idxmax())
    second_index = int(second_series.idxmin() if direction == "up" else second_series.idxmax())
    if second_index <= first_index:
        return None

    start_pivot = {
        "index": first_index,
        "time": frame["time"].iloc[first_index],
        "price": float(pd.to_numeric(frame[pivot_column], errors="coerce").iloc[first_index]),
    }
    end_pivot = {
        "index": second_index,
        "time": frame["time"].iloc[second_index],
        "price": float(pd.to_numeric(frame[pivot_column], errors="coerce").iloc[second_index]),
    }
    return _score_trendline_candidate(frame, start_pivot, end_pivot, direction)


def _build_trendline_candidate(
    frame: pd.DataFrame,
    direction: str,
    pivot_window: int,
) -> dict[str, Any] | None:
    """Build the best recent uptrend or downtrend line candidate."""
    pivot_column = "low" if direction == "up" else "high"
    pivot_points = _collect_pivot_points(frame, pivot_column, pivot_window)
    if len(pivot_points) < 2:
        return _build_fallback_trendline_candidate(frame, direction)

    recent_gap_limit = max(pivot_window * 4, len(frame) // 4, 6)
    recent_start_floor = max(pivot_window, len(frame) // 3)

    for require_recent in (True, False):
        candidates: list[dict[str, Any]] = []
        pivot_start_index = max(0, len(pivot_points) - 6)
        for first_index in range(pivot_start_index, len(pivot_points) - 1):
            for second_index in range(first_index + 1, len(pivot_points)):
                start_pivot = pivot_points[first_index]
                end_pivot = pivot_points[second_index]
                if require_recent:
                    if int(start_pivot["index"]) < recent_start_floor:
                        continue
                    if (len(frame) - 1) - int(end_pivot["index"]) > recent_gap_limit:
                        continue

                candidate = _score_trendline_candidate(
                    frame=frame,
                    start_pivot=start_pivot,
                    end_pivot=end_pivot,
                    direction=direction,
                )
                if candidate is not None:
                    candidates.append(candidate)

        if candidates:
            return min(
                candidates,
                key=lambda item: (
                    item["violations"],
                    item["last_pivot_gap"],
                    item["distance"],
                    -item["span"],
                ),
            )

    return _build_fallback_trendline_candidate(frame, direction)


def _select_auto_trendline_candidate(
    frame: pd.DataFrame,
    pivot_window: int,
) -> dict[str, Any] | None:
    """Choose the most relevant recent trendline, up or down, for the chart tail."""
    if frame.empty or len(frame) < max((pivot_window * 2) + 3, 8):
        return None

    up_candidate = _build_trendline_candidate(frame, "up", pivot_window)
    down_candidate = _build_trendline_candidate(frame, "down", pivot_window)
    candidates = [candidate for candidate in [up_candidate, down_candidate] if candidate is not None]
    if not candidates:
        return None

    recent_span = min(max(pivot_window * 4, 6), len(frame) - 1)
    baseline_index = max(len(frame) - recent_span - 1, 0)
    close_series = pd.to_numeric(frame["close"], errors="coerce")
    preferred_direction = (
        "up"
        if float(close_series.iloc[-1] - close_series.iloc[baseline_index]) >= 0
        else "down"
    )
    return min(
        candidates,
        key=lambda item: (
            item["violations"],
            0 if item["direction"] == preferred_direction else 1,
            item["last_pivot_gap"],
            item["distance"],
            -item["span"],
        ),
    )


def _trendline_status_label(direction: str, latest_signal: str) -> str:
    """Return one human-friendly trendline status label."""
    if direction == "up":
        labels = {
            "fresh_breakdown": "Harga baru breakdown di bawah trendline support.",
            "breakdown": "Harga masih breakdown di bawah trendline support.",
            "reclaimed": "Sempat breakdown, tapi sekarang kembali di atas trendline support.",
            "retest": "Harga sedang mengetes trendline support.",
            "holding": "Harga masih bertahan di atas trendline support.",
        }
    else:
        labels = {
            "fresh_breakout": "Harga baru breakout di atas trendline resistance.",
            "breakout": "Harga masih breakout di atas trendline resistance.",
            "rejected": "Sempat breakout, tapi sekarang kembali di bawah trendline resistance.",
            "retest": "Harga sedang mengetes trendline resistance.",
            "holding": "Harga masih tertahan di bawah trendline resistance.",
        }
    return labels.get(latest_signal, "Status trendline belum terbaca dengan jelas.")


def _build_auto_trendline_summary(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Build one auto-trendline summary for chart rendering and UI details."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 80), 20)
    pivot_window = max(params.get("swing_window", 3), 1)
    frame = _build_high_low_close_volume_source(data).tail(lookback).reset_index(drop=True)
    trendline_candidate = _select_auto_trendline_candidate(frame, pivot_window)
    if trendline_candidate is None:
        return None

    direction = str(trendline_candidate["direction"])
    start_index = int(trendline_candidate["start_index"])
    end_index = int(trendline_candidate["end_index"])
    last_index = len(frame) - 1
    if start_index < 0 or last_index < start_index:
        return None

    comparison_frame = frame.iloc[start_index : last_index + 1]
    line_values = pd.Series(
        [
            float(trendline_candidate["start_value"])
            + (float(trendline_candidate["slope"]) * (index - start_index))
            for index in range(start_index, last_index + 1)
        ],
        index=comparison_frame.index,
        dtype="float64",
    )
    tolerance = float(trendline_candidate["tolerance"])
    current_price = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    current_line_value = float(line_values.iloc[-1])
    pivot_column = "low" if direction == "up" else "high"
    pivot_points = _collect_pivot_points(frame, pivot_column, pivot_window)

    touch_indices = {start_index, end_index}
    for pivot_point in pivot_points:
        pivot_index = int(pivot_point["index"])
        if pivot_index < start_index or pivot_index > last_index:
            continue
        line_value_at_pivot = float(trendline_candidate["start_value"]) + (
            float(trendline_candidate["slope"]) * (pivot_index - start_index)
        )
        if abs(float(pivot_point["price"]) - line_value_at_pivot) <= tolerance:
            touch_indices.add(pivot_index)

    last_touch_index = max(touch_indices) if touch_indices else end_index
    latest_signal = str(trendline_candidate.get("latest_signal") or "")
    is_breakout_active = latest_signal in {"fresh_breakout", "breakout"}
    is_breakdown_active = latest_signal in {"fresh_breakdown", "breakdown"}

    return {
        **trendline_candidate,
        "start_time": frame["time"].iloc[start_index],
        "end_time": frame["time"].iloc[-1],
        "lookback": lookback,
        "pivot_window": pivot_window,
        "role": "support" if direction == "up" else "resistance",
        "touch_count": len(touch_indices),
        "last_touch_gap": last_index - last_touch_index,
        "current_price": current_price,
        "line_value": current_line_value,
        "distance_to_line": abs(current_price - current_line_value),
        "status_label": _trendline_status_label(direction, latest_signal),
        "is_breakout_active": is_breakout_active,
        "is_breakdown_active": is_breakdown_active,
    }


def describe_auto_trendline(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the auto-trendline summary for UI display."""
    return _build_auto_trendline_summary(data, indicator)


def _build_major_trendline_summary(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Build one higher-timeframe major trendline summary for chart rendering and UI details."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 260), 60)
    pivot_window = max(params.get("swing_window", 4), 2)
    source_frame = _build_datetime_ohlcv_source(data)
    if source_frame.empty:
        return None

    analysis_frame, analysis_timeframe = _select_major_trend_analysis_frame(source_frame, interval_label)
    analysis_frame = analysis_frame.tail(lookback).reset_index(drop=True)
    if len(analysis_frame) < max((pivot_window * 2) + 3, 12):
        return None

    trendline_candidate = _select_auto_trendline_candidate(analysis_frame, pivot_window)
    if trendline_candidate is None:
        return None

    direction = str(trendline_candidate["direction"])
    start_index = int(trendline_candidate["start_index"])
    end_index = int(trendline_candidate["end_index"])
    last_index = len(analysis_frame) - 1
    if start_index < 0 or last_index < start_index:
        return None

    comparison_frame = analysis_frame.iloc[start_index : last_index + 1]
    line_values = pd.Series(
        [
            float(trendline_candidate["start_value"])
            + (float(trendline_candidate["slope"]) * (index - start_index))
            for index in range(start_index, last_index + 1)
        ],
        index=comparison_frame.index,
        dtype="float64",
    )
    tolerance = float(trendline_candidate["tolerance"])
    chart_frame = _build_high_low_close_volume_source(data).reset_index(drop=True)
    if chart_frame.empty:
        return None

    chart_times = pd.to_datetime(chart_frame["time"], errors="coerce")
    analysis_start_time = pd.to_datetime(analysis_frame["time"].iloc[start_index], errors="coerce")
    aligned_start_mask = chart_times.ge(analysis_start_time)
    if aligned_start_mask.any():
        aligned_start_index = int(aligned_start_mask.idxmax())
    else:
        aligned_start_index = 0

    current_price = float(pd.to_numeric(chart_frame["close"], errors="coerce").iloc[-1])
    current_line_value = float(line_values.iloc[-1])
    pivot_column = "low" if direction == "up" else "high"
    pivot_points = _collect_pivot_points(analysis_frame, pivot_column, pivot_window)

    touch_indices = {start_index, end_index}
    for pivot_point in pivot_points:
        pivot_index = int(pivot_point["index"])
        if pivot_index < start_index or pivot_index > last_index:
            continue
        line_value_at_pivot = float(trendline_candidate["start_value"]) + (
            float(trendline_candidate["slope"]) * (pivot_index - start_index)
        )
        if abs(float(pivot_point["price"]) - line_value_at_pivot) <= tolerance:
            touch_indices.add(pivot_index)

    last_touch_index = max(touch_indices) if touch_indices else end_index
    latest_signal = str(trendline_candidate.get("latest_signal") or "")
    is_breakout_active = latest_signal in {"fresh_breakout", "breakout"}
    is_breakdown_active = latest_signal in {"fresh_breakdown", "breakdown"}

    return {
        **trendline_candidate,
        "start_time": chart_frame["time"].iloc[aligned_start_index],
        "end_time": chart_frame["time"].iloc[-1],
        "lookback": lookback,
        "pivot_window": pivot_window,
        "analysis_timeframe": analysis_timeframe,
        "role": "support" if direction == "up" else "resistance",
        "touch_count": len(touch_indices),
        "last_touch_gap": last_index - last_touch_index,
        "current_price": current_price,
        "line_value": current_line_value,
        "distance_to_line": abs(current_price - current_line_value),
        "status_label": _trendline_status_label(direction, latest_signal),
        "is_breakout_active": is_breakout_active,
        "is_breakdown_active": is_breakdown_active,
    }


def describe_major_trendline(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Return the major trendline summary for UI display."""
    return _build_major_trendline_summary(data, indicator, interval_label)


def _nearest_support_resistance_zone_half_height(frame: pd.DataFrame) -> float:
    """Estimate one reasonable half-zone size from recent volatility."""
    high_series = pd.to_numeric(frame["high"], errors="coerce")
    low_series = pd.to_numeric(frame["low"], errors="coerce")
    close_series = pd.to_numeric(frame["close"], errors="coerce")
    candle_ranges = (high_series - low_series).dropna()
    median_range = float(candle_ranges.median()) if not candle_ranges.empty else 0.0
    full_range = float(high_series.max() - low_series.min()) if not frame.empty else 0.0
    latest_close = float(close_series.iloc[-1]) if not close_series.empty else 0.0

    zone_half_height = max(
        median_range * 0.6,
        full_range * 0.008,
        abs(latest_close) * 0.0025,
        0.01,
    )
    zone_half_height_cap = max(
        median_range * 1.8,
        full_range * 0.05,
        abs(latest_close) * 0.02,
        0.05,
    )
    return min(zone_half_height, zone_half_height_cap)


def _fallback_nearest_level(
    frame: pd.DataFrame,
    direction: str,
    zone_half_height: float,
) -> dict[str, Any] | None:
    """Fallback to the nearest raw candle extreme when pivot clustering is sparse."""
    current_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    source_column = "low" if direction == "support" else "high"
    source_series = pd.to_numeric(frame[source_column], errors="coerce")

    if direction == "support":
        candidate_series = source_series[source_series <= current_close]
        if candidate_series.empty:
            candidate_series = source_series
        level_index = int(candidate_series.idxmax())
    else:
        candidate_series = source_series[source_series >= current_close]
        if candidate_series.empty:
            candidate_series = source_series
        level_index = int(candidate_series.idxmin())

    level_price = float(source_series.iloc[level_index])
    return {
        "direction": direction,
        "price": level_price,
        "zone_bottom": level_price - zone_half_height,
        "zone_top": level_price + zone_half_height,
        "bounces": 1,
        "distance": abs(current_close - level_price),
        "last_touch_gap": (len(frame) - 1) - level_index,
    }


def _build_nearest_level_candidate(
    frame: pd.DataFrame,
    pivot_points: list[dict[str, Any]],
    direction: str,
    zone_half_height: float,
) -> dict[str, Any] | None:
    """Build the nearest support or resistance level from clustered pivots."""
    if frame.empty:
        return None

    current_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    if not pivot_points:
        return _fallback_nearest_level(frame, direction, zone_half_height)

    candidates: list[dict[str, Any]] = []
    seen_signatures: set[tuple[int, ...]] = set()
    side_tolerance = zone_half_height * 0.4

    for seed_point in pivot_points:
        cluster_points = [
            point
            for point in pivot_points
            if abs(float(point["price"]) - float(seed_point["price"])) <= zone_half_height
        ]
        cluster_signature = tuple(sorted(int(point["index"]) for point in cluster_points))
        if not cluster_signature or cluster_signature in seen_signatures:
            continue
        seen_signatures.add(cluster_signature)

        cluster_price = float(
            sum(float(point["price"]) for point in cluster_points) / len(cluster_points)
        )
        if direction == "support" and cluster_price > current_close + side_tolerance:
            continue
        if direction == "resistance" and cluster_price < current_close - side_tolerance:
            continue

        last_touch_index = max(int(point["index"]) for point in cluster_points)
        candidates.append(
            {
                "direction": direction,
                "price": cluster_price,
                "zone_bottom": cluster_price - zone_half_height,
                "zone_top": cluster_price + zone_half_height,
                "bounces": len(cluster_points),
                "distance": abs(current_close - cluster_price),
                "last_touch_gap": (len(frame) - 1) - last_touch_index,
            }
        )

    if not candidates:
        return _fallback_nearest_level(frame, direction, zone_half_height)

    return min(
        candidates,
        key=lambda item: (
            item["distance"],
            -item["bounces"],
            item["last_touch_gap"],
        ),
    )


def _build_nearest_support_resistance_summary(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Build one support/resistance summary for both chart rendering and UI details."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 120), 20)
    swing_window = max(params.get("swing_window", 3), 1)
    frame = _build_high_low_close_volume_source(data).tail(lookback).reset_index(drop=True)
    if frame.empty or len(frame) < max((swing_window * 2) + 3, 8):
        return None

    zone_half_height = _nearest_support_resistance_zone_half_height(frame)
    support = _build_nearest_level_candidate(
        frame=frame,
        pivot_points=_collect_pivot_points(frame, "low", swing_window),
        direction="support",
        zone_half_height=zone_half_height,
    )
    resistance = _build_nearest_level_candidate(
        frame=frame,
        pivot_points=_collect_pivot_points(frame, "high", swing_window),
        direction="resistance",
        zone_half_height=zone_half_height,
    )

    return {
        "start_time": frame["time"].iloc[0],
        "end_time": frame["time"].iloc[-1],
        "current_price": float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1]),
        "zone_half_height": zone_half_height,
        "support": support,
        "resistance": resistance,
    }


def describe_nearest_support_resistance(
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the nearest support/resistance summary for UI display."""
    return _build_nearest_support_resistance_summary(data, indicator)


def _build_strong_sr_pivot_points(
    frame: pd.DataFrame,
    column: str,
    window: int,
) -> list[dict[str, Any]]:
    """Collect significant pivots together with reversal-volume context."""
    pivot_points = _collect_pivot_points(frame, column, window)
    if not pivot_points:
        return []

    volume_series = pd.to_numeric(frame["volume"], errors="coerce").fillna(0.0)
    volume_average = volume_series.rolling(window=20, min_periods=3).mean()
    volume_ratio = volume_series.div(volume_average.replace(0, pd.NA)).fillna(1.0)

    enriched_pivots: list[dict[str, Any]] = []
    for pivot_point in pivot_points:
        pivot_index = int(pivot_point["index"])
        enriched_pivots.append(
            {
                **pivot_point,
                "volume_ratio": float(volume_ratio.iloc[pivot_index]),
            }
        )
    return enriched_pivots


def _strong_support_resistance_zone_half_height(frame: pd.DataFrame) -> float:
    """Return a slightly wider zone for strong support/resistance areas."""
    return _nearest_support_resistance_zone_half_height(frame) * 1.15


def _build_strong_level_candidate(
    frame: pd.DataFrame,
    pivot_points: list[dict[str, Any]],
    direction: str,
    zone_half_height: float,
    min_bounces: int,
) -> dict[str, Any] | None:
    """Build one strong support or resistance candidate from repeated higher-timeframe pivots."""
    if frame.empty or not pivot_points:
        return None

    current_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
    side_tolerance = zone_half_height * 0.45
    candidates: list[dict[str, Any]] = []
    seen_signatures: set[tuple[int, ...]] = set()
    close_series = pd.to_numeric(frame["close"], errors="coerce")

    for seed_point in pivot_points:
        cluster_points = [
            point
            for point in pivot_points
            if abs(float(point["price"]) - float(seed_point["price"])) <= zone_half_height
        ]
        cluster_signature = tuple(sorted(int(point["index"]) for point in cluster_points))
        if (
            len(cluster_points) < min_bounces
            or not cluster_signature
            or cluster_signature in seen_signatures
        ):
            continue
        seen_signatures.add(cluster_signature)

        cluster_price = float(
            sum(float(point["price"]) for point in cluster_points) / len(cluster_points)
        )
        if direction == "support" and cluster_price > current_close + side_tolerance:
            continue
        if direction == "resistance" and cluster_price < current_close - side_tolerance:
            continue

        first_touch_index = min(int(point["index"]) for point in cluster_points)
        last_touch_index = max(int(point["index"]) for point in cluster_points)
        zone_bottom = cluster_price - zone_half_height
        zone_top = cluster_price + zone_half_height
        post_touch_close = close_series.iloc[first_touch_index:]
        if direction == "support":
            breakout_count = int(post_touch_close.lt(zone_bottom).sum())
        else:
            breakout_count = int(post_touch_close.gt(zone_top).sum())

        high_volume_reversals = sum(
            1
            for point in cluster_points
            if float(point.get("volume_ratio", 1.0)) >= STRONG_SUPPORT_RESISTANCE_VOLUME_THRESHOLD
        )
        average_volume_ratio = (
            sum(float(point.get("volume_ratio", 1.0)) for point in cluster_points) / len(cluster_points)
        )
        candidates.append(
            {
                "direction": direction,
                "price": cluster_price,
                "zone_bottom": zone_bottom,
                "zone_top": zone_top,
                "bounces": len(cluster_points),
                "breakout_count": breakout_count,
                "high_volume_reversals": high_volume_reversals,
                "average_volume_ratio": average_volume_ratio,
                "distance": abs(current_close - cluster_price),
                "last_touch_gap": (len(frame) - 1) - last_touch_index,
                "span": last_touch_index - first_touch_index,
            }
        )

    if not candidates:
        return None

    clean_candidates = [candidate for candidate in candidates if candidate["breakout_count"] == 0]
    if clean_candidates:
        candidates = clean_candidates
    else:
        candidates = sorted(candidates, key=lambda item: item["breakout_count"])[:3]

    return min(
        candidates,
        key=lambda item: (
            item["breakout_count"],
            -item["bounces"],
            -item["high_volume_reversals"],
            -item["average_volume_ratio"],
            item["distance"],
            item["last_touch_gap"],
            -item["span"],
        ),
    )


def _build_strong_support_resistance_summary(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Build strong support/resistance levels from repeated higher-timeframe tests."""
    params = _indicator_params(indicator)
    lookback = max(params.get("lookback", 160), 40)
    swing_window = max(params.get("swing_window", 3), 1)
    min_bounces = max(params.get("min_bounces", 3), 2)
    source_frame = _build_datetime_ohlcv_source(data)
    if source_frame.empty:
        return None

    analysis_frame, analysis_timeframe = _select_strong_sr_analysis_frame(source_frame, interval_label)
    analysis_frame = analysis_frame.tail(lookback).reset_index(drop=True)
    if len(analysis_frame) < max((swing_window * 2) + 3, min_bounces + 2):
        return None

    zone_half_height = _strong_support_resistance_zone_half_height(analysis_frame)
    support = _build_strong_level_candidate(
        frame=analysis_frame,
        pivot_points=_build_strong_sr_pivot_points(analysis_frame, "low", swing_window),
        direction="support",
        zone_half_height=zone_half_height,
        min_bounces=min_bounces,
    )
    resistance = _build_strong_level_candidate(
        frame=analysis_frame,
        pivot_points=_build_strong_sr_pivot_points(analysis_frame, "high", swing_window),
        direction="resistance",
        zone_half_height=zone_half_height,
        min_bounces=min_bounces,
    )

    chart_frame = _build_high_low_close_volume_source(data).reset_index(drop=True)
    chart_times = pd.to_datetime(chart_frame["time"], errors="coerce")
    analysis_start_time = analysis_frame["time"].iloc[0]
    visible_chart_frame = chart_frame.loc[chart_times >= analysis_start_time]
    if visible_chart_frame.empty:
        visible_chart_frame = chart_frame

    return {
        "start_time": visible_chart_frame["time"].iloc[0],
        "end_time": chart_frame["time"].iloc[-1],
        "current_price": float(pd.to_numeric(chart_frame["close"], errors="coerce").iloc[-1]),
        "analysis_timeframe": analysis_timeframe,
        "minimum_bounces": min_bounces,
        "support": support,
        "resistance": resistance,
    }


def describe_strong_support_resistance(
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> dict[str, Any] | None:
    """Return the strong support/resistance summary for UI display."""
    return _build_strong_support_resistance_summary(data, indicator, interval_label)


def _overlay_series_specs(indicator: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the line-rendering instructions for overlay indicators."""
    indicator_key = _indicator_key(indicator)
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)

    if indicator_key == "EMA":
        return [
            {
                "method": "ema",
                "length": params.get("length", 10),
                "name": f"EMA {params.get('length', 10)}",
                "color": colors.get("line", EMA_COLORS[0]),
            }
        ]
    if indicator_key == "EMA_CROSS":
        return [
            {
                "method": "ema",
                "length": params.get("fast_length", 9),
                "name": f"EMA {params.get('fast_length', 9)}",
                "color": colors.get("fast", EMA_COLORS[0]),
            },
            {
                "method": "ema",
                "length": params.get("slow_length", 21),
                "name": f"EMA {params.get('slow_length', 21)}",
                "color": colors.get("slow", EMA_COLORS[1]),
            },
        ]
    if indicator_key == "DOUBLE_EMA":
        return [
            {
                "method": "ema",
                "length": params.get("length_one", 20),
                "name": f"EMA {params.get('length_one', 20)}",
                "color": colors.get("line_one", EMA_COLORS[0]),
            },
            {
                "method": "ema",
                "length": params.get("length_two", 50),
                "name": f"EMA {params.get('length_two', 50)}",
                "color": colors.get("line_two", EMA_COLORS[1]),
            },
        ]
    if indicator_key == "TRIPLE_EMA":
        return [
            {
                "method": "ema",
                "length": params.get("length_one", 5),
                "name": f"EMA {params.get('length_one', 5)}",
                "color": colors.get("line_one", EMA_COLORS[0]),
            },
            {
                "method": "ema",
                "length": params.get("length_two", 10),
                "name": f"EMA {params.get('length_two', 10)}",
                "color": colors.get("line_two", EMA_COLORS[1]),
            },
            {
                "method": "ema",
                "length": params.get("length_three", 20),
                "name": f"EMA {params.get('length_three', 20)}",
                "color": colors.get("line_three", EMA_COLORS[2]),
            },
        ]
    if indicator_key == "MA":
        return [
            {
                "method": "ma",
                "length": params.get("length", 20),
                "name": f"MA {params.get('length', 20)}",
                "color": colors.get("line", MA_COLORS[0]),
            }
        ]
    if indicator_key == "MA_CROSS":
        return [
            {
                "method": "ma",
                "length": params.get("fast_length", 20),
                "name": f"MA {params.get('fast_length', 20)}",
                "color": colors.get("fast", MA_COLORS[0]),
            },
            {
                "method": "ma",
                "length": params.get("slow_length", 50),
                "name": f"MA {params.get('slow_length', 50)}",
                "color": colors.get("slow", MA_COLORS[1]),
            },
        ]
    if indicator_key == "DOUBLE_MA":
        return [
            {
                "method": "ma",
                "length": params.get("length_one", 20),
                "name": f"MA {params.get('length_one', 20)}",
                "color": colors.get("line_one", MA_COLORS[0]),
            },
            {
                "method": "ma",
                "length": params.get("length_two", 50),
                "name": f"MA {params.get('length_two', 50)}",
                "color": colors.get("line_two", MA_COLORS[1]),
            },
        ]
    if indicator_key == "TRIPLE_MA":
        return [
            {
                "method": "ma",
                "length": params.get("length_one", 10),
                "name": f"MA {params.get('length_one', 10)}",
                "color": colors.get("line_one", MA_COLORS[0]),
            },
            {
                "method": "ma",
                "length": params.get("length_two", 20),
                "name": f"MA {params.get('length_two', 20)}",
                "color": colors.get("line_two", MA_COLORS[1]),
            },
            {
                "method": "ma",
                "length": params.get("length_three", 50),
                "name": f"MA {params.get('length_three', 50)}",
                "color": colors.get("line_three", MA_COLORS[2]),
            },
        ]
    if indicator_key == "BOLLINGER_BANDS":
        length = params.get("length", 20)
        return [
            {
                "method": "bollinger",
                "length": length,
                "name": f"BB Upper {length}",
                "color": colors.get("upper", BOLLINGER_COLORS["upper"]),
            },
            {
                "method": "bollinger",
                "length": length,
                "name": f"BB Basis {length}",
                "color": colors.get("basis", BOLLINGER_COLORS["basis"]),
            },
            {
                "method": "bollinger",
                "length": length,
                "name": f"BB Lower {length}",
                "color": colors.get("lower", BOLLINGER_COLORS["lower"]),
            },
        ]
    if indicator_key == "VWAP":
        return [
            {
                "method": "vwap",
                "name": "VWAP",
                "color": colors.get("line", VWAP_COLOR),
            }
        ]
    return []


def _build_rsi_dataframe(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Prepare RSI values from close prices."""
    indicator_frame = _build_indicator_source(data)
    close = indicator_frame["close"]
    rsi = _build_rsi_series(close, window)
    line_name = f"RSI {window}"
    indicator_frame[line_name] = rsi
    indicator_frame = indicator_frame.dropna(subset=[line_name])
    return indicator_frame[["time", line_name]]


def _build_atr_dataframe(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Prepare ATR values from high, low, and close prices."""
    indicator_frame = _build_high_low_close_volume_source(data)[["time", "high", "low", "close"]].copy()
    if indicator_frame.empty:
        return indicator_frame

    previous_close = indicator_frame["close"].shift(1)
    true_range = pd.concat(
        [
            indicator_frame["high"] - indicator_frame["low"],
            (indicator_frame["high"] - previous_close).abs(),
            (indicator_frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    line_name = f"ATR {window}"
    indicator_frame[line_name] = true_range.ewm(
        alpha=1 / window,
        adjust=False,
        min_periods=window,
    ).mean()
    indicator_frame = indicator_frame.dropna(subset=[line_name])
    return indicator_frame[["time", line_name]]


def _build_macd_dataframe(
    data: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    signal_window: int,
) -> pd.DataFrame:
    """Prepare MACD, signal, and histogram values from close prices."""
    indicator_frame = _build_indicator_source(data)
    close = indicator_frame["close"]
    fast_ema = close.ewm(span=fast_window, adjust=False, min_periods=1).mean()
    slow_ema = close.ewm(span=slow_window, adjust=False, min_periods=1).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(
        span=signal_window,
        adjust=False,
        min_periods=1,
    ).mean()
    histogram = macd_line - signal_line

    indicator_frame["MACD"] = macd_line
    indicator_frame["Signal"] = signal_line
    indicator_frame["Histogram"] = histogram
    indicator_frame["color"] = "rgba(239, 68, 68, 0.50)"
    indicator_frame.loc[
        indicator_frame["Histogram"] >= 0, "color"
    ] = "rgba(34, 197, 94, 0.50)"
    indicator_frame = indicator_frame.dropna(subset=["MACD", "Signal", "Histogram"])
    return indicator_frame[["time", "MACD", "Signal", "Histogram", "color"]]


def _build_price_oscillator_dataframe(
    data: pd.DataFrame,
    fast_window: int,
    slow_window: int,
) -> pd.DataFrame:
    """Prepare Price Oscillator values from two EMA lengths."""
    indicator_frame = _build_indicator_source(data)
    close = indicator_frame["close"]
    fast_ema = close.ewm(span=fast_window, adjust=False, min_periods=1).mean()
    slow_ema = close.ewm(span=slow_window, adjust=False, min_periods=1).mean()
    indicator_frame["Price Oscillator"] = fast_ema - slow_ema
    indicator_frame = indicator_frame.dropna(subset=["Price Oscillator"])
    return indicator_frame[["time", "Price Oscillator"]]


def _build_stochastic_dataframe(
    data: pd.DataFrame,
    k_length: int,
    k_smoothing: int,
    d_length: int,
) -> pd.DataFrame:
    """Prepare Stochastic %K and %D values."""
    indicator_frame = _build_high_low_close_volume_source(data)
    highest_high = indicator_frame["high"].rolling(window=k_length, min_periods=1).max()
    lowest_low = indicator_frame["low"].rolling(window=k_length, min_periods=1).min()
    denominator = (highest_high - lowest_low).replace(0, pd.NA)
    raw_k = 100 * (indicator_frame["close"] - lowest_low).div(denominator)
    smooth_k = raw_k.rolling(window=k_smoothing, min_periods=1).mean()
    d_line = smooth_k.rolling(window=d_length, min_periods=1).mean()
    indicator_frame["%K"] = smooth_k
    indicator_frame["%D"] = d_line
    indicator_frame = indicator_frame.dropna(subset=["%K", "%D"])
    return indicator_frame[["time", "%K", "%D"]]


def _build_stochastic_rsi_dataframe(
    data: pd.DataFrame,
    rsi_length: int,
    stoch_length: int,
    k_smoothing: int,
    d_length: int,
) -> pd.DataFrame:
    """Prepare Stochastic RSI values."""
    indicator_frame = _build_indicator_source(data)
    rsi = _build_rsi_series(indicator_frame["close"], rsi_length)
    lowest_rsi = rsi.rolling(window=stoch_length, min_periods=1).min()
    highest_rsi = rsi.rolling(window=stoch_length, min_periods=1).max()
    denominator = (highest_rsi - lowest_rsi).replace(0, pd.NA)
    raw_stoch = 100 * (rsi - lowest_rsi).div(denominator)
    smooth_k = raw_stoch.rolling(window=k_smoothing, min_periods=1).mean()
    d_line = smooth_k.rolling(window=d_length, min_periods=1).mean()
    indicator_frame["%K"] = smooth_k
    indicator_frame["%D"] = d_line
    indicator_frame = indicator_frame.dropna(subset=["%K", "%D"])
    return indicator_frame[["time", "%K", "%D"]]


def _style_indicator_chart(chart: Any) -> None:
    """Apply a consistent visual style to indicator charts."""
    chart.layout(
        background_color="#0b1220",
        text_color="#d6deeb",
        font_size=11,
        font_family="Trebuchet MS",
    )
    chart.grid(
        vert_enabled=True,
        horz_enabled=True,
        color="rgba(148, 163, 184, 0.12)",
        style="solid",
    )
    chart.crosshair(
        mode="normal",
        vert_visible=True,
        vert_color="rgba(148, 163, 184, 0.30)",
        vert_style="dotted",
        horz_visible=True,
        horz_color="rgba(148, 163, 184, 0.30)",
        horz_style="dotted",
    )
    chart.legend(
        visible=True,
        ohlc=False,
        percent=False,
        lines=True,
        color="#d6deeb",
        font_size=11,
    )
    chart.price_scale(
        auto_scale=True,
        scale_margin_top=0.12,
        scale_margin_bottom=0.12,
        border_visible=False,
        text_color="#cbd5e1",
    )
    chart.time_scale(
        visible=True,
        time_visible=True,
        seconds_visible=False,
        border_visible=False,
    )


def _render_bollinger_bands(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Bollinger Bands on the main chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    length = params.get("length", 20)
    deviation = params.get("deviation", 2)
    bollinger_frame = _build_bollinger_bands_dataframe(data, length, deviation)
    if bollinger_frame.empty:
        return

    for line_name, color in [
        (f"BB Upper {length}", colors.get("upper", BOLLINGER_COLORS["upper"])),
        (f"BB Basis {length}", colors.get("basis", BOLLINGER_COLORS["basis"])),
        (f"BB Lower {length}", colors.get("lower", BOLLINGER_COLORS["lower"])),
    ]:
        line = chart.create_line(
            name=line_name,
            color=color,
            width=2,
            price_line=False,
            price_label=False,
        )
        line.set(bollinger_frame[["time", line_name]])


def _render_vwap(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render VWAP on the main chart."""
    colors = _indicator_colors(indicator)
    vwap_frame = _build_vwap_dataframe(data)
    if vwap_frame.empty:
        return

    line = chart.create_line(
        name="VWAP",
        color=colors.get("line", VWAP_COLOR),
        width=2,
        price_line=False,
        price_label=False,
    )
    line.set(vwap_frame)


def _render_parabolic_sar(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Parabolic SAR on the main chart."""
    colors = _indicator_colors(indicator)
    psar_frame = _build_parabolic_sar_dataframe(data)
    if psar_frame.empty:
        return

    psar_color = colors.get("line", PARABOLIC_SAR_COLOR)
    psar_segments = _split_parabolic_sar_segments(psar_frame)
    for index, segment_frame in enumerate(psar_segments):
        series_name = "Parabolic SAR" if index == 0 else ""
        sar_line = chart.create_line(
            name=series_name,
            color=psar_color,
            width=1,
            price_line=False,
            price_label=False,
        )
        if series_name:
            sar_line.set(segment_frame)
        else:
            sar_line.set(
                segment_frame.rename(columns={"Parabolic SAR": "value"}),
            )
        sar_line.run_script(
            f"""
            {sar_line.id}.series.applyOptions({{
                lineVisible: false,
                pointMarkersVisible: true,
                pointMarkersRadius: 2,
                crosshairMarkerVisible: false,
                lastValueVisible: false,
                priceLineVisible: false
            }})
            """
        )


def _render_auto_trendline(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render a single automatically detected trendline near the latest candles."""
    colors = _indicator_colors(indicator)
    trendline_summary = _build_auto_trendline_summary(data, indicator)
    if trendline_summary is None:
        return

    direction = str(trendline_summary["direction"])
    chart.trend_line(
        start_time=trendline_summary["start_time"],
        start_value=trendline_summary["start_value"],
        end_time=trendline_summary["end_time"],
        end_value=trendline_summary["end_value"],
        line_color=colors.get(direction, TRENDLINE_COLORS[direction]),
        width=2,
        style="solid",
    )


def _render_major_trendline(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> None:
    """Render one major higher-timeframe trendline on the main chart."""
    colors = _indicator_colors(indicator)
    trendline_summary = _build_major_trendline_summary(data, indicator, interval_label)
    if trendline_summary is None:
        return

    direction = str(trendline_summary["direction"])
    chart.trend_line(
        start_time=trendline_summary["start_time"],
        start_value=trendline_summary["start_value"],
        end_time=trendline_summary["end_time"],
        end_value=trendline_summary["end_value"],
        line_color=colors.get(direction, TRENDLINE_COLORS[direction]),
        width=3,
        style="solid",
    )


def _render_nearest_support_resistance(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
) -> None:
    """Render the nearest support and resistance areas across the recent chart range."""
    colors = _indicator_colors(indicator)
    summary = _build_nearest_support_resistance_summary(data, indicator)
    if summary is None:
        return

    for direction, label in [("support", "Support"), ("resistance", "Resistance")]:
        level = summary.get(direction)
        if level is None:
            continue

        color = colors.get(direction, NEAREST_SUPPORT_RESISTANCE_COLORS[direction])
        chart.box(
            start_time=summary["start_time"],
            start_value=float(level["zone_top"]),
            end_time=summary["end_time"],
            end_value=float(level["zone_bottom"]),
            color=_with_alpha(color, 0.35),
            fill_color=_with_alpha(color, NEAREST_SUPPORT_RESISTANCE_FILL_ALPHA),
            width=1,
            style="solid",
        )
        chart.horizontal_line(
            price=float(level["price"]),
            color=_with_alpha(color, NEAREST_SUPPORT_RESISTANCE_LINE_ALPHA),
            width=2,
            style="solid",
            text=f"{label} x{int(level['bounces'])}",
            axis_label_visible=False,
        )


def _render_strong_support_resistance(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> None:
    """Render strong support and resistance areas from repeated higher-timeframe tests."""
    colors = _indicator_colors(indicator)
    summary = _build_strong_support_resistance_summary(data, indicator, interval_label)
    if summary is None:
        return

    for direction, label in [("support", "Strong Support"), ("resistance", "Strong Resistance")]:
        level = summary.get(direction)
        if level is None:
            continue

        color = colors.get(direction, STRONG_SUPPORT_RESISTANCE_COLORS[direction])
        chart.box(
            start_time=summary["start_time"],
            start_value=float(level["zone_top"]),
            end_time=summary["end_time"],
            end_value=float(level["zone_bottom"]),
            color=_with_alpha(color, 0.42),
            fill_color=_with_alpha(color, STRONG_SUPPORT_RESISTANCE_FILL_ALPHA),
            width=1,
            style="solid",
        )
        chart.horizontal_line(
            price=float(level["price"]),
            color=_with_alpha(color, STRONG_SUPPORT_RESISTANCE_LINE_ALPHA),
            width=2,
            style="solid",
            text=(
                f"{label} x{int(level['bounces'])}"
                f" Vol {float(level['average_volume_ratio']):.2f}x"
            ),
            axis_label_visible=False,
        )


def _render_fibonacci_levels(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Fibonacci retracement levels on the main chart."""
    lookback = _indicator_params(indicator).get("lookback", 120)
    colors = _indicator_colors(indicator)
    indicator_frame = _build_high_low_close_volume_source(data).tail(lookback)
    if indicator_frame.empty or len(indicator_frame) < 2:
        return

    highest_high = float(indicator_frame["high"].max())
    lowest_low = float(indicator_frame["low"].min())
    price_range = highest_high - lowest_low
    if price_range <= 0:
        return

    start_time = indicator_frame["time"].iloc[0]
    end_time = indicator_frame["time"].iloc[-1]
    line_override = colors.get("line", "").strip().lower()
    use_monochrome = bool(
        line_override and line_override != FIBONACCI_MONOCHROME_DEFAULT.lower()
    )
    level_configs = []

    for ratio, default_color in FIBONACCI_LEVELS:
        level_color = line_override if use_monochrome else default_color
        level_price = highest_high - (price_range * ratio)
        level_configs.append(
            {
                "ratio": ratio,
                "price": level_price,
                "color": level_color,
                "label": f"{ratio * 100:.2f}%",
            }
        )

    for index in range(1, len(level_configs)):
        upper_level = level_configs[index - 1]
        lower_level = level_configs[index]
        band_color = (
            line_override if use_monochrome else lower_level["color"]
        )
        band_alpha = FIBONACCI_FILL_ALPHAS[min(index - 1, len(FIBONACCI_FILL_ALPHAS) - 1)]
        chart.box(
            start_time=start_time,
            start_value=upper_level["price"],
            end_time=end_time,
            end_value=lower_level["price"],
            color="rgba(0, 0, 0, 0)",
            fill_color=_with_alpha(band_color, band_alpha),
            width=1,
            style="solid",
        )

    for level in level_configs:
        chart.trend_line(
            start_time=start_time,
            start_value=level["price"],
            end_time=end_time,
            end_value=level["price"],
            line_color=level["color"],
            width=1,
            style="solid",
        )
        chart.horizontal_line(
            price=level["price"],
            color=_with_alpha(level["color"], 0.18),
            width=1,
            style="solid",
            text=level["label"],
            axis_label_visible=False,
        )


def _render_pivot_point_standard(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render standard pivot point levels from the previous completed candle."""
    line_color = _indicator_colors(indicator).get("line")
    indicator_frame = _build_high_low_close_volume_source(data)
    if len(indicator_frame) < 2:
        return

    previous_bar = indicator_frame.iloc[-2]
    high = float(previous_bar["high"])
    low = float(previous_bar["low"])
    close = float(previous_bar["close"])
    pivot_point = (high + low + close) / 3
    price_range = high - low

    levels = {
        "PP": pivot_point,
        "R1": (2 * pivot_point) - low,
        "R2": pivot_point + price_range,
        "R3": high + (2 * (pivot_point - low)),
        "S1": (2 * pivot_point) - high,
        "S2": pivot_point - price_range,
        "S3": low - (2 * (high - pivot_point)),
    }

    for label, color in PIVOT_LEVELS:
        chart.horizontal_line(
            price=levels[label],
            color=line_color or color,
            width=1,
            style="dashed",
            text=label,
            axis_label_visible=False,
        )


def _render_overlay_indicator(
    chart: Any,
    data: pd.DataFrame,
    indicator: dict[str, Any],
    interval_label: str | None = None,
) -> None:
    """Render one overlay indicator into the main price chart."""
    indicator_key = _indicator_key(indicator)
    colors = _indicator_colors(indicator)
    if indicator_key == "BOLLINGER_BANDS":
        _render_bollinger_bands(chart, data, indicator)
        return
    if indicator_key == "VWAP":
        _render_vwap(chart, data, indicator)
        return
    if indicator_key == "PARABOLIC_SAR":
        _render_parabolic_sar(chart, data, indicator)
        return
    if indicator_key == "TRENDLINE":
        _render_auto_trendline(chart, data, indicator)
        return
    if indicator_key == "MAJOR_TRENDLINE":
        _render_major_trendline(chart, data, indicator, interval_label)
        return
    if indicator_key == "NEAREST_SUPPORT_RESISTANCE":
        _render_nearest_support_resistance(chart, data, indicator)
        return
    if indicator_key == "STRONG_SUPPORT_RESISTANCE":
        _render_strong_support_resistance(chart, data, indicator, interval_label)
        return
    if indicator_key == "FIBONACCI":
        _render_fibonacci_levels(chart, data, indicator)
        return
    if indicator_key == "PIVOT_POINT_STANDARD":
        _render_pivot_point_standard(chart, data, indicator)
        return

    rendered_lines: list[Any] = []
    for series_spec in _overlay_series_specs(indicator):
        line_frame = _build_moving_average_dataframe(
            data=data,
            length=int(series_spec["length"]),
            line_name=str(series_spec["name"]),
            method=str(series_spec["method"]),
        )
        if line_frame.empty:
            continue

        line = chart.create_line(
            name=str(series_spec["name"]),
            color=str(series_spec["color"]),
            width=2,
            price_line=False,
            price_label=False,
        )
        line.set(line_frame)
        rendered_lines.append(line)

    if indicator_key in {"EMA_CROSS", "MA_CROSS"} and len(rendered_lines) >= 1:
        params = _indicator_params(indicator)
        cross_frame = _build_cross_moving_average_dataframe(
            data=data,
            fast_length=params.get("fast_length", 9 if indicator_key == "EMA_CROSS" else 20),
            slow_length=params.get("slow_length", 21 if indicator_key == "EMA_CROSS" else 50),
            method="ema" if indicator_key == "EMA_CROSS" else "ma",
        )
        cross_markers = _build_cross_markers(
            series_frame=cross_frame,
            fast_column="fast",
            slow_column="slow",
            color=colors.get("cross", "#f8fafc"),
        )
        if cross_markers:
            rendered_lines[0].marker_list(cross_markers)


def _render_rsi_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render RSI into a dedicated chart."""
    window = _indicator_params(indicator).get("length", 14)
    colors = _indicator_colors(indicator)
    rsi_frame = _build_rsi_dataframe(data, window)
    if rsi_frame.empty:
        return

    line_name = f"RSI {window}"
    rsi_line = chart.create_line(
        name=line_name,
        color=colors.get("line", "#a78bfa"),
        width=2,
        price_line=False,
        price_label=True,
    )
    rsi_line.set(rsi_frame)
    chart.horizontal_line(
        price=70,
        color="rgba(248, 113, 113, 0.55)",
        width=1,
        style="dashed",
        text="70",
        axis_label_visible=False,
    )
    chart.horizontal_line(
        price=30,
        color="rgba(96, 165, 250, 0.55)",
        width=1,
        style="dashed",
        text="30",
        axis_label_visible=False,
    )


def _render_atr_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render ATR into a dedicated chart."""
    window = _indicator_params(indicator).get("length", 14)
    colors = _indicator_colors(indicator)
    atr_frame = _build_atr_dataframe(data, window)
    if atr_frame.empty:
        return

    line_name = f"ATR {window}"
    atr_line = chart.create_line(
        name=line_name,
        color=colors.get("line", ATR_COLOR),
        width=2,
        price_line=False,
        price_label=True,
    )
    atr_line.set(atr_frame)


def _render_price_oscillator_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Price Oscillator into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    oscillator_frame = _build_price_oscillator_dataframe(
        data=data,
        fast_window=params.get("fast_length", 12),
        slow_window=params.get("slow_length", 26),
    )
    if oscillator_frame.empty:
        return

    oscillator_line = chart.create_line(
        name="Price Oscillator",
        color=colors.get("line", PRICE_OSCILLATOR_COLOR),
        width=2,
        price_line=False,
        price_label=True,
    )
    oscillator_line.set(oscillator_frame)
    chart.horizontal_line(
        price=0,
        color="rgba(148, 163, 184, 0.45)",
        width=1,
        style="dashed",
        axis_label_visible=False,
    )


def _render_macd_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render MACD lines and histogram into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    macd_frame = _build_macd_dataframe(
        data=data,
        fast_window=params.get("fast_length", 12),
        slow_window=params.get("slow_length", 26),
        signal_window=params.get("signal_length", 9),
    )
    if macd_frame.empty:
        return

    histogram = chart.create_histogram(
        name="MACD Histogram",
        color="rgba(148, 163, 184, 0.45)",
        price_line=False,
        price_label=False,
        scale_margin_top=0.12,
        scale_margin_bottom=0.12,
    )
    histogram.set(
        macd_frame.assign(
            color=macd_frame["Histogram"].ge(0).map(
                {
                    True: colors.get("histogram_up", "#22c55e"),
                    False: colors.get("histogram_down", "#ef4444"),
                }
            )
        )[["time", "Histogram", "color"]].rename(columns={"Histogram": "MACD Histogram"})
    )

    macd_line = chart.create_line(
        name="MACD",
        color=colors.get("macd", "#38bdf8"),
        width=2,
        price_line=False,
        price_label=False,
        price_scale_id=histogram.id,
    )
    macd_line.set(macd_frame[["time", "MACD"]])

    signal_line = chart.create_line(
        name="Signal",
        color=colors.get("signal", "#f59e0b"),
        width=2,
        price_line=False,
        price_label=False,
        price_scale_id=histogram.id,
    )
    signal_line.set(macd_frame[["time", "Signal"]])

    macd_cross_markers = _build_cross_markers(
        series_frame=macd_frame,
        fast_column="MACD",
        slow_column="Signal",
        color=colors.get("cross", "#f8fafc"),
    )
    if macd_cross_markers:
        macd_line.marker_list(macd_cross_markers)

    chart.horizontal_line(
        price=0,
        color="rgba(148, 163, 184, 0.45)",
        width=1,
        style="dashed",
        axis_label_visible=False,
    )


def _render_stochastic_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Stochastic indicator into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    stochastic_frame = _build_stochastic_dataframe(
        data=data,
        k_length=params.get("k_length", 14),
        k_smoothing=params.get("k_smoothing", 3),
        d_length=params.get("d_length", 3),
    )
    if stochastic_frame.empty:
        return

    k_line = chart.create_line(
        name="%K",
        color=colors.get("k", STOCHASTIC_COLORS["k"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    k_line.set(stochastic_frame[["time", "%K"]])

    d_line = chart.create_line(
        name="%D",
        color=colors.get("d", STOCHASTIC_COLORS["d"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    d_line.set(stochastic_frame[["time", "%D"]])

    for level, color in [(80, "rgba(248, 113, 113, 0.55)"), (20, "rgba(96, 165, 250, 0.55)")]:
        chart.horizontal_line(
            price=level,
            color=color,
            width=1,
            style="dashed",
            text=str(level),
            axis_label_visible=False,
        )


def _render_stochastic_rsi_indicator(chart: Any, data: pd.DataFrame, indicator: dict[str, Any]) -> None:
    """Render Stochastic RSI indicator into a dedicated chart."""
    params = _indicator_params(indicator)
    colors = _indicator_colors(indicator)
    stochastic_rsi_frame = _build_stochastic_rsi_dataframe(
        data=data,
        rsi_length=params.get("rsi_length", 14),
        stoch_length=params.get("stoch_length", 14),
        k_smoothing=params.get("k_smoothing", 3),
        d_length=params.get("d_length", 3),
    )
    if stochastic_rsi_frame.empty:
        return

    k_line = chart.create_line(
        name="%K",
        color=colors.get("k", STOCHASTIC_COLORS["k"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    k_line.set(stochastic_rsi_frame[["time", "%K"]])

    d_line = chart.create_line(
        name="%D",
        color=colors.get("d", STOCHASTIC_COLORS["d"]),
        width=2,
        price_line=False,
        price_label=False,
    )
    d_line.set(stochastic_rsi_frame[["time", "%D"]])

    for level, color in [(80, "rgba(248, 113, 113, 0.55)"), (20, "rgba(96, 165, 250, 0.55)")]:
        chart.horizontal_line(
            price=level,
            color=color,
            width=1,
            style="dashed",
            text=str(level),
            axis_label_visible=False,
        )


def _render_single_indicator_chart(indicator: dict[str, Any], data: pd.DataFrame) -> None:
    """Render one standalone indicator chart beneath the main price chart."""
    title = _format_indicator_title(indicator)
    chart = build_streamlit_chart(
        symbol=title,
        interval_label="",
        display_name=title,
        height=INDICATOR_CHART_HEIGHT,
    )
    _style_indicator_chart(chart)

    indicator_key = _indicator_key(indicator)
    if indicator_key == "ATR":
        _render_atr_indicator(chart, data, indicator)
    elif indicator_key == "PRICE_OSCILLATOR":
        _render_price_oscillator_indicator(chart, data, indicator)
    elif indicator_key == "RSI":
        _render_rsi_indicator(chart, data, indicator)
    elif indicator_key == "MACD":
        _render_macd_indicator(chart, data, indicator)
    elif indicator_key == "STOCHASTIC":
        _render_stochastic_indicator(chart, data, indicator)
    elif indicator_key == "STOCHASTIC_RSI":
        _render_stochastic_rsi_indicator(chart, data, indicator)
    else:
        return

    chart.fit()
    chart.load()


def _render_backtest_trade_markers(chart: Any, trade_log: pd.DataFrame | None) -> None:
    """Render buy and sell labels on the main price chart for completed trades."""
    if trade_log is None or trade_log.empty:
        return

    marker_points: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    for row in trade_log.itertuples(index=False):
        entry_time = getattr(row, "entry_datetime", None)
        entry_price = getattr(row, "entry_price", None)
        if entry_time is not None and entry_price is not None:
            marker_points.append({"time": entry_time, "Backtest Signal": float(entry_price)})
            markers.append(
                {
                    "time": entry_time,
                    "position": "below",
                    "shape": "circle",
                    "color": "#22c55e",
                    "text": "Buy",
                }
            )

        exit_time = getattr(row, "exit_datetime", None)
        exit_price = getattr(row, "exit_price", None)
        if exit_time is not None and exit_price is not None:
            marker_points.append({"time": exit_time, "Backtest Signal": float(exit_price)})
            markers.append(
                {
                    "time": exit_time,
                    "position": "above",
                    "shape": "circle",
                    "color": "#ef4444",
                    "text": "Sell",
                }
            )

    if not marker_points:
        return

    marker_series = chart.create_line(
        name="Backtest Signal",
        color="rgba(0, 0, 0, 0)",
        width=1,
        price_line=False,
        price_label=False,
    )
    marker_series.set(pd.DataFrame(marker_points))
    marker_series.marker_list(markers)


def render_candlestick_chart(
    data: pd.DataFrame,
    symbol: str,
    interval_label: str,
    display_name: str | None = None,
    indicator_configs: list[dict[str, Any]] | None = None,
    use_bei_price_fractions: bool = False,
    backtest_trade_log: pd.DataFrame | None = None,
) -> None:
    """Load prepared OHLCV data into the Streamlit chart and render it."""
    chart = build_streamlit_chart(
        symbol=symbol,
        interval_label=interval_label,
        display_name=display_name,
        height=MAIN_CHART_HEIGHT,
    )
    price_frame = _build_price_dataframe(data)
    volume_frame = _build_volume_dataframe(data)

    chart.set(price_frame)
    latest_close = float(pd.to_numeric(price_frame["close"], errors="coerce").iloc[-1])
    if use_bei_price_fractions and latest_close > 0:
        _apply_bei_price_fraction_format(chart, latest_close)
    if not volume_frame.empty:
        volume_histogram = chart.create_histogram(
            name="Volume",
            color="rgba(148, 163, 184, 0.45)",
            price_line=False,
            price_label=False,
            scale_margin_top=VOLUME_PANEL_TOP_MARGIN,
            scale_margin_bottom=VOLUME_PANEL_BOTTOM_MARGIN,
        )
        volume_histogram.set(
            volume_frame[["time", "volume", "color"]].rename(columns={"volume": "Volume"})
        )

        volume_ma_line = chart.create_line(
            name=f"Volume MA {VOLUME_MA_WINDOW}",
            color="#f59e0b",
            width=2,
            price_line=False,
            price_label=False,
            price_scale_id=volume_histogram.id,
        )
        volume_ma_line.set(volume_frame[["time", f"Volume MA {VOLUME_MA_WINDOW}"]])
        chart.run_script(
            f"""
            {volume_histogram.id}.series.priceScale().applyOptions({{
                visible: false,
                ticksVisible: false,
                borderVisible: false
            }})
            """
        )

    for indicator in indicator_configs or []:
        if not _indicator_visible(indicator):
            continue
        if _indicator_key(indicator) not in OVERLAY_INDICATOR_KEYS:
            continue
        _render_overlay_indicator(
            chart,
            data,
            indicator,
            interval_label=interval_label,
        )

    _render_backtest_trade_markers(chart, backtest_trade_log)

    chart.fit()
    chart.load()


def render_indicator_charts(
    data: pd.DataFrame,
    indicator_configs: list[dict[str, Any]] | None = None,
) -> None:
    """Render selected panel indicators as dedicated charts under the main chart."""
    for indicator in indicator_configs or []:
        if not _indicator_visible(indicator):
            continue
        if _indicator_key(indicator) not in PANEL_INDICATOR_KEYS:
            continue
        _render_single_indicator_chart(indicator, data)



