from __future__ import annotations

from typing import Any

import pandas as pd
def _indicator_key(indicator: dict[str, Any]) -> str:
    """Return one normalized indicator key."""
    return str(indicator.get("key") or "").strip().upper()


def _indicator_params(indicator: dict[str, Any]) -> dict[str, Any]:
    """Return the parameter dictionary for one indicator config."""
    raw_params = indicator.get("params") or {}
    normalized_params: dict[str, Any] = {}
    for name, value in raw_params.items():
        key = str(name)
        if isinstance(value, bool):
            normalized_params[key] = value
            continue
        if isinstance(value, int):
            normalized_params[key] = int(value)
            continue
        if isinstance(value, float):
            normalized_params[key] = float(value)
            continue

        text_value = str(value).strip()
        try:
            normalized_params[key] = int(text_value)
            continue
        except (TypeError, ValueError):
            pass

        try:
            normalized_params[key] = float(text_value)
            continue
        except (TypeError, ValueError):
            pass

        lowered = text_value.lower()
        if lowered in {"true", "false"}:
            normalized_params[key] = lowered == "true"
        else:
            normalized_params[key] = text_value
    return normalized_params

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
                "shape": "square",
                "color": color,
                "text": "+",
            }
        )
    return markers

def _style_indicator_chart(chart: Any) -> None:
    """Apply panel-specific styling tweaks on top of the base chart theme."""
    chart.price_scale(
        auto_scale=True,
        scale_margin_top=0.10,
        scale_margin_bottom=0.10,
        border_visible=False,
        text_color="#cbd5e1",
    )
    chart.time_scale(
        visible=True,
        time_visible=True,
        seconds_visible=False,
        border_visible=False,
    )
__all__ = [name for name in globals() if name != '__builtins__' and not name.startswith('__')]

