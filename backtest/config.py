from __future__ import annotations

from typing import Any

import pandas as pd

BACKTEST_STRATEGY_CATALOG = [
    {
        "key": "RSI",
        "label": "RSI",
        "description": "Mean reversion RSI dengan trend filter dan exit fleksibel.",
    },
    {
        "key": "MACD",
        "label": "MACD",
        "description": "Trend-following MACD dengan filter trend dan opsi exit momentum.",
    },
    {
        "key": "BREAK_EMA",
        "label": "Break EMA",
        "description": "Buy saat harga pullback ke EMA dan hold sampai close jebol di bawah EMA.",
    },
    {
        "key": "PARABOLIC_SAR",
        "label": "Parabolic SAR",
        "description": "Trend-following Parabolic SAR dengan filter MA 200 yang lebih simpel dan bersih.",
    },
    {
        "key": "VOLUME_BREAKOUT",
        "label": "Volume Breakout",
        "description": "Breakout dari area konsolidasi sempit dengan volume rendah lalu meledak saat breakout.",
    },
]

BACKTEST_STRATEGY_LABELS = {
    item["key"]: item["label"] for item in BACKTEST_STRATEGY_CATALOG
}

BACKTEST_PERIOD_DISPLAY = {
    "1d": "1D",
    "5d": "5D",
    "1wk": "1W",
    "2wk": "2W",
    "1mo": "1M",
    "3mo": "3M",
    "6mo": "6M",
    "1y": "1Y",
    "2y": "2Y",
    "5y": "5Y",
    "YTD": "YTD",
    "ALL": "ALL",
}

POSITION_SIZING_MODES = [
    "fixed_percent_of_equity",
    "fixed_nominal",
]

RSI_ENTRY_MODES = ["cross_up_oversold"]
RSI_EXIT_MODES = [
    "rsi_above_level",
    "cross_down_overbought",
    "fixed_tp_sl",
]
MACD_ENTRY_MODES = [
    "macd_cross_up_signal",
    "macd_cross_up_zero",
    "histogram_turn_positive",
]
MACD_EXIT_MODES = [
    "macd_cross_down_signal",
    "macd_cross_down_zero",
    "fixed_tp_sl",
]
BREAK_EMA_EXIT_MODES = [
    "ema_breakdown",
    "tp_sl_trailing_only",
]


def get_default_backtest_general_params() -> dict[str, Any]:
    """Return the default general backtest settings."""
    return {
        "initial_capital": 10_000_000.0,
        "position_sizing_mode": "fixed_nominal",
        "position_size_value": 1_000_000.0,
        "buy_fee_pct": 0.15,
        "sell_fee_pct": 0.25,
        "slippage_pct": 0.10,
        "stop_loss_pct": 3.0,
        "take_profit_pct": 6.0,
        "trailing_stop_pct": 0.0,
        "max_holding_bars": 0,
        "cooldown_bars": 0,
        "show_indicator_preview": True,
    }


def get_default_rsi_params() -> dict[str, Any]:
    """Return the default RSI strategy settings."""
    return {
        "rsi_period": 14,
        "oversold_level": 30.0,
        "overbought_level": 70.0,
        "exit_rsi_level": 60.0,
        "trend_filter_enabled": True,
        "trend_ma_period": 50,
        "entry_mode": "cross_up_oversold",
        "exit_mode": "rsi_above_level",
    }


def get_default_macd_params() -> dict[str, Any]:
    """Return the default MACD strategy settings."""
    return {
        "macd_fast_period": 12,
        "macd_slow_period": 26,
        "macd_signal_period": 9,
        "trend_filter_enabled": True,
        "trend_ma_period": 50,
        "entry_mode": "macd_cross_up_signal",
        "exit_mode": "macd_cross_down_signal",
    }


def get_default_break_ema_params() -> dict[str, Any]:
    """Return the default Break EMA strategy settings."""
    return {
        "ema_period": 10,
        "exit_mode": "ema_breakdown",
    }


def get_default_parabolic_sar_params() -> dict[str, Any]:
    """Return the default Parabolic SAR strategy settings."""
    return {
        "psar_acceleration_pct": 2.0,
        "psar_max_acceleration_pct": 20.0,
    }


def get_default_volume_breakout_params() -> dict[str, Any]:
    """Return the default Volume Breakout strategy settings."""
    return {
        "consolidation_bars": 10,
        "max_consolidation_range_pct": 6.0,
        "volume_ma_period": 20,
        "consolidation_volume_ratio_max": 0.80,
        "breakout_volume_ratio_min": 1.80,
        "breakout_buffer_pct": 0.20,
        "exit_after_bars": 1,
    }


def get_default_strategy_params(strategy_key: str) -> dict[str, Any]:
    """Return the default settings for one strategy."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if normalized_key == "RSI":
        return get_default_rsi_params()
    if normalized_key == "MACD":
        return get_default_macd_params()
    if normalized_key == "BREAK_EMA":
        return get_default_break_ema_params()
    if normalized_key == "PARABOLIC_SAR":
        return get_default_parabolic_sar_params()
    if normalized_key == "VOLUME_BREAKOUT":
        return get_default_volume_breakout_params()
    raise ValueError(f"Unsupported backtest strategy: {strategy_key}")


def get_strategy_label(strategy_key: str) -> str:
    """Return a human-friendly strategy label."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    return BACKTEST_STRATEGY_LABELS.get(normalized_key, normalized_key or "Unknown")


def filter_backtest_strategies(search_query: str) -> list[dict[str, str]]:
    """Return the strategy catalog filtered by the user's search query."""
    normalized_query = str(search_query or "").strip().casefold()
    if not normalized_query:
        return list(BACKTEST_STRATEGY_CATALOG)

    return [
        strategy
        for strategy in BACKTEST_STRATEGY_CATALOG
        if normalized_query in strategy["label"].casefold()
        or normalized_query in strategy["description"].casefold()
        or normalized_query in strategy["key"].casefold()
    ]


def display_backtest_period_label(period_label: str) -> str:
    """Return the compact display label used by the backtest UI."""
    normalized_label = str(period_label or "").strip()
    return BACKTEST_PERIOD_DISPLAY.get(normalized_label, normalized_label or "-")


def derive_date_range_from_chart_period(
    period_label: str,
    end_timestamp: pd.Timestamp | None = None,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Translate one chart period label into a timestamp range."""
    normalized_label = str(period_label or "").strip()
    if not normalized_label:
        return None, None

    resolved_end = pd.Timestamp(end_timestamp or pd.Timestamp.utcnow()).tz_localize(None)
    if normalized_label == "ALL":
        return None, resolved_end
    if normalized_label == "YTD":
        return pd.Timestamp(year=resolved_end.year, month=1, day=1), resolved_end

    if normalized_label == "1d":
        return resolved_end - pd.Timedelta(days=1), resolved_end
    if normalized_label == "5d":
        return resolved_end - pd.Timedelta(days=5), resolved_end
    if normalized_label == "1wk":
        return resolved_end - pd.Timedelta(days=7), resolved_end
    if normalized_label == "2wk":
        return resolved_end - pd.Timedelta(days=14), resolved_end

    date_offset_lookup = {
        "1mo": pd.DateOffset(months=1),
        "3mo": pd.DateOffset(months=3),
        "6mo": pd.DateOffset(months=6),
        "1y": pd.DateOffset(years=1),
        "2y": pd.DateOffset(years=2),
        "5y": pd.DateOffset(years=5),
    }
    offset = date_offset_lookup.get(normalized_label)
    if offset is None:
        return None, resolved_end
    return resolved_end - offset, resolved_end


def filter_frame_to_chart_period(frame: pd.DataFrame, period_label: str) -> pd.DataFrame:
    """Clamp one OHLCV frame to the active chart period as a safety net."""
    if frame.empty or "time" not in frame.columns:
        return frame.copy()

    prepared = frame.copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    prepared = prepared.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    if prepared.empty:
        return prepared

    start, end = derive_date_range_from_chart_period(
        period_label=period_label,
        end_timestamp=pd.Timestamp(prepared["time"].iloc[-1]),
    )
    if start is not None:
        prepared = prepared.loc[prepared["time"] >= start]
    if end is not None:
        prepared = prepared.loc[prepared["time"] <= end]
    if prepared.empty:
        return frame.copy()
    return prepared.reset_index(drop=True)


def _coerce_float(value: Any, fallback: float, minimum: float = 0.0) -> float:
    """Convert a raw value into a safe bounded float."""
    try:
        normalized_value = float(value)
    except (TypeError, ValueError):
        normalized_value = float(fallback)
    return max(normalized_value, minimum)


def _coerce_int(value: Any, fallback: int, minimum: int = 0) -> int:
    """Convert a raw value into a safe bounded integer."""
    try:
        normalized_value = int(value)
    except (TypeError, ValueError):
        normalized_value = int(fallback)
    return max(normalized_value, minimum)


def _coerce_bool(value: Any, fallback: bool) -> bool:
    """Convert one raw value into a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return bool(fallback)


def normalize_general_backtest_params(raw_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize the general backtest settings into safe runtime values."""
    defaults = get_default_backtest_general_params()
    raw_params = raw_params or {}

    position_mode = str(
        raw_params.get("position_sizing_mode", defaults["position_sizing_mode"])
    ).strip()
    if position_mode not in POSITION_SIZING_MODES:
        position_mode = defaults["position_sizing_mode"]

    position_size_value = _coerce_float(
        raw_params.get("position_size_value"),
        float(defaults["position_size_value"]),
        minimum=0.01,
    )
    if position_mode == "fixed_percent_of_equity":
        position_size_value = min(position_size_value, 100.0)

    return {
        "initial_capital": _coerce_float(
            raw_params.get("initial_capital"),
            float(defaults["initial_capital"]),
            minimum=1.0,
        ),
        "position_sizing_mode": position_mode,
        "position_size_value": position_size_value,
        "buy_fee_pct": _coerce_float(raw_params.get("buy_fee_pct"), defaults["buy_fee_pct"]),
        "sell_fee_pct": _coerce_float(raw_params.get("sell_fee_pct"), defaults["sell_fee_pct"]),
        "slippage_pct": _coerce_float(raw_params.get("slippage_pct"), defaults["slippage_pct"]),
        "stop_loss_pct": _coerce_float(raw_params.get("stop_loss_pct"), defaults["stop_loss_pct"]),
        "take_profit_pct": _coerce_float(raw_params.get("take_profit_pct"), defaults["take_profit_pct"]),
        "trailing_stop_pct": _coerce_float(
            raw_params.get("trailing_stop_pct"),
            defaults["trailing_stop_pct"],
        ),
        "max_holding_bars": _coerce_int(
            raw_params.get("max_holding_bars"),
            defaults["max_holding_bars"],
        ),
        "cooldown_bars": _coerce_int(
            raw_params.get("cooldown_bars"),
            defaults["cooldown_bars"],
        ),
        "show_indicator_preview": _coerce_bool(
            raw_params.get("show_indicator_preview"),
            bool(defaults["show_indicator_preview"]),
        ),
    }


def normalize_strategy_backtest_params(
    strategy_key: str,
    raw_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one strategy parameter dictionary."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    raw_params = raw_params or {}

    if normalized_key == "RSI":
        defaults = get_default_rsi_params()
        oversold_level = min(
            _coerce_float(raw_params.get("oversold_level"), defaults["oversold_level"], minimum=1.0),
            49.0,
        )
        overbought_level = max(
            _coerce_float(
                raw_params.get("overbought_level"),
                defaults["overbought_level"],
                minimum=oversold_level + 5.0,
            ),
            oversold_level + 5.0,
        )
        overbought_level = min(overbought_level, 99.0)
        exit_rsi_level = _coerce_float(
            raw_params.get("exit_rsi_level"),
            defaults["exit_rsi_level"],
            minimum=oversold_level + 1.0,
        )
        exit_rsi_level = min(exit_rsi_level, 99.0)
        entry_mode = str(raw_params.get("entry_mode", defaults["entry_mode"])).strip()
        if entry_mode not in RSI_ENTRY_MODES:
            entry_mode = defaults["entry_mode"]
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in RSI_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        return {
            "rsi_period": _coerce_int(raw_params.get("rsi_period"), defaults["rsi_period"], minimum=2),
            "oversold_level": oversold_level,
            "overbought_level": overbought_level,
            "exit_rsi_level": exit_rsi_level,
            "trend_filter_enabled": _coerce_bool(
                raw_params.get("trend_filter_enabled"),
                defaults["trend_filter_enabled"],
            ),
            "trend_ma_period": _coerce_int(
                raw_params.get("trend_ma_period"),
                defaults["trend_ma_period"],
                minimum=2,
            ),
            "entry_mode": entry_mode,
            "exit_mode": exit_mode,
        }

    if normalized_key == "MACD":
        defaults = get_default_macd_params()
        fast_period = _coerce_int(
            raw_params.get("macd_fast_period"),
            defaults["macd_fast_period"],
            minimum=1,
        )
        slow_period = _coerce_int(
            raw_params.get("macd_slow_period"),
            defaults["macd_slow_period"],
            minimum=fast_period + 1,
        )
        signal_period = _coerce_int(
            raw_params.get("macd_signal_period"),
            defaults["macd_signal_period"],
            minimum=1,
        )
        entry_mode = str(raw_params.get("entry_mode", defaults["entry_mode"])).strip()
        if entry_mode not in MACD_ENTRY_MODES:
            entry_mode = defaults["entry_mode"]
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in MACD_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        return {
            "macd_fast_period": fast_period,
            "macd_slow_period": slow_period,
            "macd_signal_period": signal_period,
            "trend_filter_enabled": _coerce_bool(
                raw_params.get("trend_filter_enabled"),
                defaults["trend_filter_enabled"],
            ),
            "trend_ma_period": _coerce_int(
                raw_params.get("trend_ma_period"),
                defaults["trend_ma_period"],
                minimum=2,
            ),
            "entry_mode": entry_mode,
            "exit_mode": exit_mode,
        }

    if normalized_key == "BREAK_EMA":
        defaults = get_default_break_ema_params()
        exit_mode = str(raw_params.get("exit_mode", defaults["exit_mode"])).strip()
        if exit_mode not in BREAK_EMA_EXIT_MODES:
            exit_mode = defaults["exit_mode"]
        return {
            "ema_period": _coerce_int(
                raw_params.get("ema_period"),
                defaults["ema_period"],
                minimum=1,
            ),
            "exit_mode": exit_mode,
        }

    if normalized_key == "PARABOLIC_SAR":
        defaults = get_default_parabolic_sar_params()
        acceleration_pct = _coerce_float(
            raw_params.get("psar_acceleration_pct"),
            defaults["psar_acceleration_pct"],
            minimum=0.1,
        )
        return {
            "psar_acceleration_pct": acceleration_pct,
            "psar_max_acceleration_pct": _coerce_float(
                raw_params.get("psar_max_acceleration_pct"),
                defaults["psar_max_acceleration_pct"],
                minimum=acceleration_pct,
            ),
        }

    if normalized_key == "VOLUME_BREAKOUT":
        defaults = get_default_volume_breakout_params()
        return {
            "consolidation_bars": _coerce_int(
                raw_params.get("consolidation_bars"),
                defaults["consolidation_bars"],
                minimum=3,
            ),
            "max_consolidation_range_pct": _coerce_float(
                raw_params.get("max_consolidation_range_pct"),
                defaults["max_consolidation_range_pct"],
                minimum=0.1,
            ),
            "volume_ma_period": _coerce_int(
                raw_params.get("volume_ma_period"),
                defaults["volume_ma_period"],
                minimum=3,
            ),
            "consolidation_volume_ratio_max": _coerce_float(
                raw_params.get("consolidation_volume_ratio_max"),
                defaults["consolidation_volume_ratio_max"],
                minimum=0.1,
            ),
            "breakout_volume_ratio_min": _coerce_float(
                raw_params.get("breakout_volume_ratio_min"),
                defaults["breakout_volume_ratio_min"],
                minimum=1.0,
            ),
            "breakout_buffer_pct": _coerce_float(
                raw_params.get("breakout_buffer_pct"),
                defaults["breakout_buffer_pct"],
                minimum=0.0,
            ),
            "exit_after_bars": _coerce_int(
                raw_params.get("exit_after_bars"),
                defaults["exit_after_bars"],
                minimum=1,
            ),
        }

    raise ValueError(f"Unsupported backtest strategy: {strategy_key}")


def build_backtest_preview_indicator_config(
    strategy_key: str,
    strategy_params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Build one temporary indicator config or overlay bundle for chart preview."""
    normalized_key = str(strategy_key or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    normalized_params = normalize_strategy_backtest_params(normalized_key, strategy_params)

    if normalized_key == "RSI":
        rsi_period = int(normalized_params["rsi_period"])
        return {
            "id": "backtest-preview-rsi",
            "key": "RSI",
            "params": {"length": rsi_period},
            "colors": {},
            "visible": True,
            "source": "backtest",
            "title_prefix": "Backtest",
            "display_label": f"RSI {rsi_period}",
        }

    if normalized_key == "MACD":
        fast_length = int(normalized_params["macd_fast_period"])
        slow_length = int(normalized_params["macd_slow_period"])
        signal_length = int(normalized_params["macd_signal_period"])
        return {
            "id": "backtest-preview-macd",
            "key": "MACD",
            "params": {
                "fast_length": fast_length,
                "slow_length": slow_length,
                "signal_length": signal_length,
            },
            "colors": {},
            "visible": True,
            "source": "backtest",
            "title_prefix": "Backtest",
            "display_label": f"MACD {fast_length} / {slow_length} / {signal_length}",
        }

    if normalized_key == "BREAK_EMA":
        ema_period = int(normalized_params["ema_period"])
        return {
            "id": "backtest-preview-break-ema",
            "key": "EMA",
            "params": {"length": ema_period},
            "colors": {},
            "visible": True,
            "source": "backtest",
            "title_prefix": "Backtest",
            "display_label": f"Break EMA {ema_period}",
        }

    if normalized_key == "PARABOLIC_SAR":
        return [
            {
                "id": "backtest-preview-psar",
                "key": "PARABOLIC_SAR",
                "params": {
                    "acceleration_pct": int(round(float(normalized_params["psar_acceleration_pct"]))),
                    "max_acceleration_pct": int(round(float(normalized_params["psar_max_acceleration_pct"]))),
                },
                "colors": {},
                "visible": True,
                "source": "backtest",
                "title_prefix": "Backtest",
                "display_label": "Parabolic SAR",
            },
            {
                "id": "backtest-preview-psar-ma-200",
                "key": "MA",
                "params": {"length": 200},
                "colors": {"line": "#e2e8f0"},
                "visible": True,
                "source": "backtest_helper",
            },
        ]

    if normalized_key == "VOLUME_BREAKOUT":
        consolidation_bars = int(normalized_params["consolidation_bars"])
        volume_ma_period = int(normalized_params["volume_ma_period"])
        return {
            "id": "backtest-preview-volume-breakout",
            "key": "VOLUME_BREAKOUT_ZONE",
            "params": {
                "consolidation_bars": consolidation_bars,
                "max_consolidation_range_pct": float(normalized_params["max_consolidation_range_pct"]),
                "volume_ma_period": volume_ma_period,
                "consolidation_volume_ratio_max": float(normalized_params["consolidation_volume_ratio_max"]),
                "breakout_volume_ratio_min": float(normalized_params["breakout_volume_ratio_min"]),
                "breakout_buffer_pct": float(normalized_params["breakout_buffer_pct"]),
                "exit_after_bars": int(normalized_params["exit_after_bars"]),
            },
            "colors": {
                "zone": "#38bdf8",
                "breakout": "#22c55e",
                "low_volume": "#94a3b8",
            },
            "visible": True,
            "source": "backtest",
            "title_prefix": "Backtest",
            "display_label": f"Volume Breakout {consolidation_bars} / {volume_ma_period}",
        }

    raise ValueError(f"Unsupported backtest strategy: {strategy_key}")





