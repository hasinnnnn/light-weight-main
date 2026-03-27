from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from backtest.models import BacktestResult

SUMMARY_TONES = {
    "positive": {
        "text": "#22c55e",
    },
    "negative": {
        "text": "#f87171",
    },
    "neutral": {
        "text": "#e2e8f0",
    },
}

METRIC_CARD_BACKGROUND = "rgba(15, 23, 42, 0.58)"
METRIC_CARD_BORDER = "rgba(148, 163, 184, 0.20)"
METRIC_CARD_LABEL = "#94a3b8"

PARAMETER_LABELS = {
    "initial_capital": "Modal awal",
    "position_sizing_mode": "Mode ukuran posisi",
    "position_size_value": "Target entry",
    "buy_fee_pct": "Fee beli",
    "sell_fee_pct": "Fee jual",
    "slippage_pct": "Slippage",
    "stop_loss_pct": "Stop loss",
    "take_profit_pct": "Take profit",
    "trailing_stop_pct": "Trailing stop",
    "max_holding_bars": "Maksimal holding bar",
    "cooldown_bars": "Cooldown bar",
    "show_indicator_preview": "Preview indikator",
    "rsi_period": "Periode RSI",
    "oversold_level": "Level oversold",
    "overbought_level": "Level overbought",
    "exit_rsi_level": "Level exit RSI",
    "trend_filter_enabled": "Filter tren aktif",
    "trend_ma_period": "Periode MA tren",
    "entry_mode": "Mode entry",
    "exit_mode": "Mode exit",
    "macd_fast_period": "Periode cepat MACD",
    "macd_slow_period": "Periode lambat MACD",
    "macd_signal_period": "Periode signal MACD",
    "ema_period": "Periode EMA",
    "ma_period": "Periode MA",
    "breakdown_confirm_mode": "Konfirmasi breakdown",
    "psar_acceleration_pct": "Akselerasi PSAR",
    "psar_max_acceleration_pct": "Maks. akselerasi PSAR",
    "ema_fast_period": "EMA cepat",
    "ema_medium_period": "EMA sedang",
    "ema_slow_period": "EMA lambat",
    "ema_anchor_period": "EMA anchor",
    "ma_trend_period": "MA tren",
    "trendline_lookback": "Lookback trendline",
    "trendline_swing_window": "Sensitivitas trendline",
    "max_consolidation_range_pct": "Rentang konsolidasi maks.",
    "consolidation_bars": "Bar konsolidasi",
    "volume_ma_period": "Periode MA volume",
    "consolidation_volume_ratio_max": "Volume konsolidasi maks.",
    "breakout_volume_ratio_min": "Volume breakout min.",
    "breakout_buffer_pct": "Buffer breakout",
    "exit_after_bars": "Exit setelah bar",
}

PARAMETER_VALUE_LABELS = {
    "fixed_percent_of_equity": "Persentase ekuitas tetap",
    "fixed_nominal": "Nominal tetap",
    "cross_up_oversold": "Cross naik dari area oversold",
    "rsi_above_level": "RSI di atas level exit",
    "cross_down_overbought": "Cross turun dari area overbought",
    "fixed_tp_sl": "SL / TP / trailing + sinyal strategi",
    "ema_breakdown": "Breakdown di bawah EMA saja",
    "ma_breakdown": "Breakdown di bawah MA saja",
    "tp_sl_trailing_only": "SL / TP / trailing + sinyal strategi",
    "macd_cross_up_signal": "MACD cross naik di atas signal",
    "macd_cross_up_zero": "MACD cross naik di atas nol",
    "histogram_turn_positive": "Histogram berubah positif",
    "macd_cross_down_signal": "MACD cross turun di bawah signal",
    "macd_cross_down_zero": "MACD turun di bawah nol",
    "body_breakdown": "Body candle bearish breakdown",
    "marubozu_breakdown": "Marubozu bearish breakdown",
}


def format_decimal(value: float) -> str:
    """Format one numeric value with Indonesian separators."""
    formatted = f"{abs(float(value)):,.2f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")



def format_rupiah(value: float, show_sign: bool = False) -> str:
    """Format one currency value using the Rp prefix."""
    sign = ""
    if value < 0:
        sign = "-"
    elif show_sign and value > 0:
        sign = "+"
    return f"{sign}Rp {format_decimal(value)}"



def format_pct(value: float, show_sign: bool = False) -> str:
    """Format one percent value using Indonesian separators."""
    sign = ""
    if value < 0:
        sign = "-"
    elif show_sign and value > 0:
        sign = "+"
    return f"{sign}{format_decimal(value)}%"



def format_qty(value: float) -> str:
    """Format quantity values compactly for the trade log."""
    formatted = f"{float(value):,.4f}".rstrip("0").rstrip(".")
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")



def format_lot(value: float) -> str:
    """Format one lot value for the Indonesian stock display."""
    return f"{format_decimal(value)} lot"



def metric_tone(value: float) -> str:
    """Pick the color tone for one signed metric."""
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"



def render_metric_card(column, label: str, value: str, tone: str) -> None:
    """Render one compact summary card with custom coloring."""
    palette = SUMMARY_TONES[tone]
    column.markdown(
        f"""
        <div style="
            border-radius: 14px;
            padding: 1rem 1.05rem;
            min-height: 108px;
            margin-bottom: 0.8rem;
            background: {METRIC_CARD_BACKGROUND};
            border: 1px solid {METRIC_CARD_BORDER};
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
        ">
            <div style="
                color: {METRIC_CARD_LABEL};
                font-size: 0.82rem;
                margin-bottom: 0.6rem;
            ">{html.escape(label)}</div>
            <div style="
                color: {palette['text']};
                font-size: 1.35rem;
                font-weight: 700;
                line-height: 1.3;
            ">{html.escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def entry_target_label(result: BacktestResult) -> str:
    """Build the human-readable entry target label."""
    mode = str(result.general_params.get("position_sizing_mode", "")).strip()
    value = float(result.general_params.get("position_size_value", 0.0))
    if mode == "fixed_percent_of_equity":
        return format_pct(value)
    return format_rupiah(value)



def resolve_entry_lot(result: BacktestResult) -> float | None:
    """Estimate or average the lot size used per entry for BEI symbols."""
    if not result.uses_lot_sizing or result.lot_size <= 1:
        return None

    if not result.trade_log.empty and "qty" in result.trade_log:
        qty_values = pd.to_numeric(result.trade_log["qty"], errors="coerce").dropna()
        if not qty_values.empty:
            return float(qty_values.mean()) / float(result.lot_size)

    if str(result.general_params.get("position_sizing_mode", "")).strip() != "fixed_nominal":
        return None

    close_values = pd.to_numeric(result.chart_frame.get("close"), errors="coerce").dropna()
    if close_values.empty:
        return None

    target_budget = float(result.general_params.get("position_size_value", 0.0))
    buy_fee_rate = float(result.general_params.get("buy_fee_pct", 0.0)) / 100.0
    slippage_rate = float(result.general_params.get("slippage_pct", 0.0)) / 100.0
    reference_price = float(close_values.iloc[-1])
    cost_per_share = reference_price * (1.0 + slippage_rate) * (1.0 + buy_fee_rate)
    if cost_per_share <= 0:
        return None

    raw_qty = target_budget / cost_per_share
    return float(int(raw_qty // float(result.lot_size)))



def trade_outcome_extremes(result: BacktestResult) -> tuple[float, float]:
    """Return the largest winning trade and the largest losing trade."""
    if result.trade_log.empty or "pnl_nominal" not in result.trade_log:
        return 0.0, 0.0

    pnl_values = pd.to_numeric(result.trade_log["pnl_nominal"], errors="coerce").dropna()
    if pnl_values.empty:
        return 0.0, 0.0

    positive_trades = pnl_values[pnl_values > 0]
    negative_trades = pnl_values[pnl_values < 0]
    max_profit = float(positive_trades.max()) if not positive_trades.empty else 0.0
    max_loss = float(negative_trades.min()) if not negative_trades.empty else 0.0
    return max_profit, max_loss



def parameter_value(name: str, value: object, parameters: dict[str, object]) -> str:
    """Translate parameter values into more readable Indonesian text."""
    if isinstance(value, bool):
        return "Aktif" if value else "Nonaktif"

    if name == "initial_capital":
        return format_rupiah(float(value))

    if name == "position_size_value":
        if str(parameters.get("position_sizing_mode", "")).strip() == "fixed_percent_of_equity":
            return format_pct(float(value))
        return format_rupiah(float(value))

    if name in {"consolidation_volume_ratio_max", "breakout_volume_ratio_min"}:
        return f"{float(value):.2f}x"

    if name.endswith("_pct"):
        return format_pct(float(value))

    if name.endswith("_period") or name.endswith("_bars") or name.endswith("_level"):
        if isinstance(value, (int, float)):
            return format_decimal(float(value)) if isinstance(value, float) else str(value)
        return str(value)

    return PARAMETER_VALUE_LABELS.get(str(value), str(value))



def parameter_rows(parameters: dict[str, object], section_label: str) -> pd.DataFrame:
    """Convert one parameter section into a small translated dataframe."""
    rows = []
    for name, value in parameters.items():
        rows.append(
            {
                "Bagian": section_label,
                "Parameter": PARAMETER_LABELS.get(name, name.replace("_", " ").title()),
                "Nilai": parameter_value(name, value, parameters),
            }
        )
    return pd.DataFrame(rows)



def format_price_level(value: float) -> str:
    """Format one market price without forcing the Rp prefix."""
    numeric_value = float(value)
    absolute_value = abs(numeric_value)
    if absolute_value >= 100 and abs(numeric_value - round(numeric_value)) < 1e-9:
        formatted = f"{numeric_value:,.0f}"
    elif absolute_value >= 1:
        formatted = f"{numeric_value:,.2f}"
    else:
        formatted = f"{numeric_value:,.4f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")



def count_trailing_psar_bars(result: BacktestResult, position_label: str) -> int:
    """Count how many latest bars keep the same PSAR side."""
    if result.chart_frame.empty or "psar_position" not in result.chart_frame:
        return 0
    positions = [str(value) for value in result.chart_frame["psar_position"].fillna("").tolist()]
    count = 0
    for value in reversed(positions):
        if value == position_label:
            count += 1
        else:
            break
    return count



def build_parabolic_sar_setup_status(
    result: BacktestResult,
) -> tuple[list[tuple[str, str, str]], str]:
    """Build strategy-specific setup cards for the Parabolic SAR backtest."""
    if result.chart_frame.empty:
        return [], ""

    required_columns = {
        "close",
        "trend_ma",
        "trend_alignment",
        "psar_position",
        "psar_flip_up",
        "entry_signal",
    }
    if not required_columns.issubset(set(result.chart_frame.columns)):
        return [], ""

    latest = result.chart_frame.iloc[-1]
    ma_period = 200

    close_price = float(pd.to_numeric(pd.Series([latest["close"]]), errors="coerce").iloc[0])
    trend_ma = float(pd.to_numeric(pd.Series([latest["trend_ma"]]), errors="coerce").iloc[0])
    trend_is_up = bool(latest.get("trend_alignment", False))
    price_above_trend_ma = close_price >= trend_ma if pd.notna(trend_ma) else False
    psar_position = str(latest.get("psar_position") or "")
    psar_flip_up = bool(latest.get("psar_flip_up", False))
    entry_signal = bool(latest.get("entry_signal", False))
    psar_below_price = psar_position == "below"
    psar_bars = count_trailing_psar_bars(result, psar_position)

    trend_text = (
        f"Uptrend di atas MA {ma_period}"
        if trend_is_up
        else f"Belum uptrend di atas MA {ma_period}"
    )
    trend_tone = "positive" if trend_is_up else "negative"

    if pd.notna(trend_ma):
        price_text = (
            f"Close {format_price_level(close_price)} di atas MA {ma_period} ({format_price_level(trend_ma)})"
            if price_above_trend_ma
            else f"Close {format_price_level(close_price)} di bawah MA {ma_period} ({format_price_level(trend_ma)})"
        )
        price_tone = "positive" if price_above_trend_ma else "negative"
    else:
        price_text = f"MA {ma_period} belum siap"
        price_tone = "neutral"

    if psar_flip_up and psar_below_price:
        psar_text = "Titik pertama PSAR baru pindah ke bawah harga"
        psar_tone = "positive"
    elif psar_below_price:
        psar_text = f"PSAR masih di bawah harga ({psar_bars} bar)"
        psar_tone = "neutral"
    elif psar_position == "above":
        psar_text = f"PSAR masih di atas harga ({psar_bars} bar)"
        psar_tone = "negative"
    else:
        psar_text = "PSAR belum siap"
        psar_tone = "neutral"

    if entry_signal:
        entry_text = "Cocok untuk entry berikutnya"
        entry_tone = "positive"
        guidance_text = (
            "Sinyal titik pertama PSAR di bawah harga baru muncul dan close juga masih bertahan di atas MA 200."
        )
    elif trend_is_up and psar_below_price and price_above_trend_ma:
        entry_text = "Masih bullish, tapi sinyal pertama sudah lewat"
        entry_tone = "neutral"
        guidance_text = (
            "Trend masih sehat di atas MA 200, tapi entry idealnya saat titik pertama PSAR baru pindah ke bawah harga."
        )
    elif not trend_is_up:
        entry_text = "Belum cocok, harga belum di atas MA 200"
        entry_tone = "negative"
        guidance_text = "Tunggu harga kembali bertahan di atas MA 200 supaya filter tren PSAR kembali valid."
    else:
        entry_text = "Belum cocok, tunggu flip PSAR berikutnya"
        entry_tone = "negative"
        guidance_text = "Tunggu reversal PSAR berikutnya yang kembali muncul di bawah harga saat saham masih di atas MA 200."

    cards = [
        ("Status trend", trend_text, trend_tone),
        ("Posisi harga", price_text, price_tone),
        ("Status PSAR", psar_text, psar_tone),
        ("Kelayakan entry", entry_text, entry_tone),
    ]
    return cards, guidance_text


__all__ = [
    "SUMMARY_TONES",
    "build_parabolic_sar_setup_status",
    "entry_target_label",
    "format_decimal",
    "format_lot",
    "format_pct",
    "format_price_level",
    "format_qty",
    "format_rupiah",
    "metric_tone",
    "parameter_rows",
    "trade_outcome_extremes",
    "render_metric_card",
    "resolve_entry_lot",
]





