from __future__ import annotations

import pandas as pd

from data.models import MarketInsight



def _average_true_range(frame: pd.DataFrame, window: int = 14) -> pd.Series:
    """Compute a lightweight ATR series for risk classification."""
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    close = pd.to_numeric(frame["close"], errors="coerce")
    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=window, min_periods=3).mean()



def build_market_insight(frame: pd.DataFrame) -> MarketInsight:
    """Classify the latest price action into a simple trend/risk summary."""
    analysis = frame[["high", "low", "close"]].copy()
    for column in ["high", "low", "close"]:
        analysis[column] = pd.to_numeric(analysis[column], errors="coerce")
    analysis = analysis.dropna(subset=["high", "low", "close"]).tail(120)

    if analysis.empty:
        return MarketInsight(
            trend_label="Downtrend",
            risk_label="High Risk",
            reason="data belum cukup bersih untuk membaca trend dan risk dengan aman.",
        )

    close = analysis["close"]
    high = analysis["high"]
    low = analysis["low"]
    lookback = min(len(close), 20)
    trend_window = min(len(close), max(6, lookback))
    fast_ema = close.ewm(span=8, adjust=False, min_periods=1).mean()
    slow_ema = close.ewm(span=21, adjust=False, min_periods=1).mean()
    atr = _average_true_range(pd.DataFrame({"high": high, "low": low, "close": close}))

    current_price = float(close.iloc[-1])
    earlier_price = float(close.iloc[-trend_window])
    support_level = float(low.tail(lookback).min())
    resistance_level = float(high.tail(lookback).max())
    atr_ratio = float((atr.iloc[-1] / current_price) if current_price and pd.notna(atr.iloc[-1]) else 0.0)
    support_distance = max((current_price - support_level) / current_price, 0.0) if current_price else 0.0
    resistance_distance = (
        max((resistance_level - current_price) / current_price, 0.0) if current_price else 0.0
    )

    trend_is_up = (
        current_price >= float(fast_ema.iloc[-1])
        and float(fast_ema.iloc[-1]) >= float(slow_ema.iloc[-1])
        and current_price >= earlier_price
    )
    trend_label = "Uptrend" if trend_is_up else "Downtrend"

    risk_score = 0
    if trend_label == "Downtrend":
        risk_score += 1
    if atr_ratio >= 0.035:
        risk_score += 1
    if resistance_distance <= 0.04:
        risk_score += 1
    if support_distance <= 0.03:
        risk_score += 1

    risk_label = "High Risk" if risk_score >= 2 else "Low Risk"

    if risk_label == "High Risk":
        reasons = []
        reasons.append("tren masih turun" if trend_label == "Downtrend" else "volatilitas masih cukup tinggi")
        if resistance_distance <= 0.04:
            reasons.append("upside ke resistance cukup sempit")
        if support_distance <= 0.03:
            reasons.append("jarak ke support sudah terlalu dekat")
        reason = ", ".join(reasons) + "."
    else:
        reasons = ["tren mulai naik" if trend_label == "Uptrend" else "risk masih terjaga"]
        if resistance_distance > 0.04:
            reasons.append("ruang ke resistance masih lega")
        if support_distance > 0.03:
            reasons.append("harga belum terlalu mepet ke support")
        reason = ", ".join(reasons) + "."

    return MarketInsight(
        trend_label=trend_label,
        risk_label=risk_label,
        reason=reason,
    )


__all__ = ["build_market_insight"]
