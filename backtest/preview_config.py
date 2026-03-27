from __future__ import annotations

from typing import Any

from backtest.param_normalization import normalize_strategy_backtest_params

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

    if normalized_key == "BREAK_MA":
        ma_period = int(normalized_params["ma_period"])
        return {
            "id": "backtest-preview-break-ma",
            "key": "MA",
            "params": {"length": ma_period},
            "colors": {},
            "visible": True,
            "source": "backtest",
            "title_prefix": "Backtest",
            "display_label": f"Break MA {ma_period}",
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





