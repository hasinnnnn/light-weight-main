from __future__ import annotations

import pandas as pd

from indicators.parabolic_sar import calculate_parabolic_sar
from indicators.sma import calculate_sma
from strategies.base_strategy import StrategyPreparation


PSAR_TREND_MA_PERIOD = 200


def prepare_parabolic_sar_strategy(
    frame: pd.DataFrame,
    params: dict[str, object],
) -> StrategyPreparation:
    """Prepare the Parabolic SAR trend-following strategy with an MA 200 filter."""
    prepared = frame.copy()
    psar_acceleration = max(float(params["psar_acceleration_pct"]), 0.01) / 100.0
    psar_max_acceleration = max(
        float(params["psar_max_acceleration_pct"]),
        float(params["psar_acceleration_pct"]),
    ) / 100.0

    psar_frame = calculate_parabolic_sar(
        prepared[["time", "high", "low", "close"]],
        acceleration=psar_acceleration,
        max_acceleration=psar_max_acceleration,
    )
    prepared = prepared.merge(
        psar_frame[["time", "psar", "position", "flip_up", "flip_down"]],
        on="time",
        how="left",
    )

    prepared["trend_ma"] = calculate_sma(prepared["close"], period=PSAR_TREND_MA_PERIOD)
    prepared["trend_alignment"] = prepared["close"].gt(prepared["trend_ma"])
    prepared["close_above_trend_ma"] = prepared["close"].ge(prepared["trend_ma"])
    prepared["psar_position"] = prepared["position"].fillna("")
    prepared["psar_flip_up"] = prepared["flip_up"].fillna(False)
    prepared["psar_flip_down"] = prepared["flip_down"].fillna(False)

    indicator_ready = (
        prepared["psar"].notna()
        & prepared["trend_ma"].notna()
    )

    prepared["entry_signal"] = (
        prepared["psar_flip_up"]
        & prepared["trend_alignment"]
        & prepared["close_above_trend_ma"]
        & indicator_ready
    )
    prepared["exit_signal"] = (
        prepared["psar_flip_down"]
        & indicator_ready
    )
    prepared["indicator_ready"] = indicator_ready.fillna(False)

    return StrategyPreparation(
        frame=prepared,
        warmup_bars=max(PSAR_TREND_MA_PERIOD, 2),
        entry_rule_summary=(
            "Buy saat titik pertama Parabolic SAR pindah ke bawah harga "
            f"dan close tetap di atas MA {PSAR_TREND_MA_PERIOD}."
        ),
        exit_rule_summary="Exit saat titik pertama Parabolic SAR kembali pindah ke atas harga.",
    )
