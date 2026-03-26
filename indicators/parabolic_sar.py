from __future__ import annotations

import pandas as pd


def calculate_parabolic_sar(
    frame: pd.DataFrame,
    acceleration: float = 0.02,
    max_acceleration: float = 0.2,
) -> pd.DataFrame:
    """Calculate Parabolic SAR values, position side, and flip events."""
    indicator_frame = frame[["time", "high", "low", "close"]].copy()
    for column in ["high", "low", "close"]:
        indicator_frame[column] = pd.to_numeric(indicator_frame[column], errors="coerce")
    indicator_frame = indicator_frame.dropna(subset=["time", "high", "low", "close"]).reset_index(drop=True)
    if len(indicator_frame) < 2:
        return indicator_frame.iloc[0:0].assign(
            psar=pd.Series(dtype="float64"),
            position=pd.Series(dtype="object"),
            flip_up=pd.Series(dtype="bool"),
            flip_down=pd.Series(dtype="bool"),
        )

    step = max(float(acceleration), 0.0001)
    max_step = max(float(max_acceleration), step)

    high_series = indicator_frame["high"].reset_index(drop=True)
    low_series = indicator_frame["low"].reset_index(drop=True)
    close_series = indicator_frame["close"].reset_index(drop=True)

    is_uptrend = bool(close_series.iloc[1] >= close_series.iloc[0])
    extreme_point = float(high_series.iloc[0] if is_uptrend else low_series.iloc[0])
    acceleration_factor = float(step)
    sar_values = [float(low_series.iloc[0] if is_uptrend else high_series.iloc[0])]
    positions = ["below" if is_uptrend else "above"]
    flip_up = [False]
    flip_down = [False]

    for index in range(1, len(indicator_frame)):
        previous_sar = sar_values[-1]
        current_sar = previous_sar + (acceleration_factor * (extreme_point - previous_sar))
        flipped_up = False
        flipped_down = False

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
                flipped_down = True
                current_sar = extreme_point
                extreme_point = float(low_series.iloc[index])
                acceleration_factor = float(step)
            else:
                if float(high_series.iloc[index]) > extreme_point:
                    extreme_point = float(high_series.iloc[index])
                    acceleration_factor = min(acceleration_factor + float(step), max_step)
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
                flipped_up = True
                current_sar = extreme_point
                extreme_point = float(high_series.iloc[index])
                acceleration_factor = float(step)
            else:
                if float(low_series.iloc[index]) < extreme_point:
                    extreme_point = float(low_series.iloc[index])
                    acceleration_factor = min(acceleration_factor + float(step), max_step)

        sar_values.append(float(current_sar))
        positions.append("below" if is_uptrend else "above")
        flip_up.append(flipped_up)
        flip_down.append(flipped_down)

    indicator_frame["psar"] = pd.Series(sar_values, index=indicator_frame.index, dtype="float64")
    indicator_frame["position"] = pd.Series(positions, index=indicator_frame.index, dtype="object")
    indicator_frame["flip_up"] = pd.Series(flip_up, index=indicator_frame.index, dtype="bool")
    indicator_frame["flip_down"] = pd.Series(flip_down, index=indicator_frame.index, dtype="bool")
    return indicator_frame[["time", "high", "low", "close", "psar", "position", "flip_up", "flip_down"]]
