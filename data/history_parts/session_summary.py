from __future__ import annotations

import math

import pandas as pd

from data.models import MarketSessionSummary



def _bei_tick_step(price: float) -> int:
    """Return the current BEI tick-size step for one price."""
    if price >= 5000:
        return 25
    if price >= 2000:
        return 10
    if price >= 500:
        return 5
    if price >= 200:
        return 2
    return 1



def _round_to_tick(price: float, method: str = "nearest") -> float:
    """Round one price to the valid tick step of its own price range."""
    if price <= 0:
        return 0.0

    step = _bei_tick_step(price)
    scaled_price = price / step
    if method == "down":
        rounded_price = math.floor(scaled_price) * step
    elif method == "up":
        rounded_price = math.ceil(scaled_price) * step
    else:
        rounded_price = round(scaled_price) * step
    return float(max(rounded_price, step))



def _calculate_bei_ara_arb(reference_price: float | None) -> tuple[float | None, float | None]:
    """Calculate ARA and ARB using the active BEI reference price for the session."""
    if reference_price is None or reference_price <= 0:
        return None, None

    if reference_price <= 200:
        ara_percent = 0.35
    elif reference_price <= 5000:
        ara_percent = 0.25
    else:
        ara_percent = 0.20
    arb_percent = 0.15

    ara_price = _round_to_tick(reference_price * (1 + ara_percent), method="down")
    arb_price = _round_to_tick(reference_price * (1 - arb_percent), method="nearest")
    return ara_price, arb_price



def build_market_session_summary(
    daily_frame: pd.DataFrame,
    uses_bei_price_fractions: bool,
    previous_close_override: float | None = None,
) -> MarketSessionSummary:
    """Build one compact daily session summary for the top insight card."""
    if daily_frame.empty:
        return MarketSessionSummary(
            open_price=None,
            high_price=None,
            low_price=None,
            previous_close=None,
            average_price=None,
            value=None,
            volume=None,
            lot=None,
            ara_price=None,
            arb_price=None,
        )

    session_frame = daily_frame.tail(2).copy()
    latest_row = session_frame.iloc[-1]
    previous_close = (
        float(previous_close_override)
        if previous_close_override is not None
        else float(session_frame["close"].iloc[-2]) if len(session_frame) >= 2 else None
    )
    open_price = float(latest_row["open"]) if pd.notna(latest_row["open"]) else None
    high_price = float(latest_row["high"]) if pd.notna(latest_row["high"]) else None
    low_price = float(latest_row["low"]) if pd.notna(latest_row["low"]) else None
    close_price = float(latest_row["close"]) if pd.notna(latest_row["close"]) else None
    volume = float(latest_row["volume"]) if pd.notna(latest_row["volume"]) else None

    average_price: float | None = None
    if None not in {open_price, high_price, low_price, close_price}:
        average_price = (open_price + high_price + low_price + close_price) / 4
        if uses_bei_price_fractions:
            average_price = _round_to_tick(average_price, method="nearest")

    value = average_price * volume if average_price is not None and volume is not None else None
    lot = (volume / 100) if uses_bei_price_fractions and volume is not None else None
    ara_arb_reference_price = open_price if open_price is not None else previous_close
    ara_price, arb_price = (
        _calculate_bei_ara_arb(ara_arb_reference_price) if uses_bei_price_fractions else (None, None)
    )

    return MarketSessionSummary(
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        previous_close=previous_close,
        average_price=average_price,
        value=value,
        volume=volume,
        lot=lot,
        ara_price=ara_price,
        arb_price=arb_price,
    )


__all__ = ["build_market_session_summary"]

