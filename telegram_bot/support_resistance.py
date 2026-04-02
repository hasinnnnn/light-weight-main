from __future__ import annotations

from io import BytesIO

import pandas as pd

from charts.chart_service import describe_nearest_support_resistance, describe_strong_support_resistance
from data.market_data_service import DataServiceError, load_market_data
from data.search import sanitize_symbol
from indicators.catalog import (
    default_indicator_colors,
    default_indicator_params,
    normalize_indicator_colors,
    normalize_indicator_params,
)
from ui.market_insight_parts.formatters import format_price_change_with_percent, format_price_value
from ui.market_insight_parts.note_builders import (
    format_price_distance_percentage,
    format_support_resistance_zone,
)


DEFAULT_SR_INTERVAL_LABEL = "1 hari"
DEFAULT_SR_PERIOD_LABEL = "1y"
SRD_CHART_LOOKBACK = 120
SRK_CHART_LOOKBACK = 160


def _build_indicator_config(indicator_key: str) -> dict[str, object]:
    return {
        "key": indicator_key,
        "params": normalize_indicator_params(indicator_key, default_indicator_params(indicator_key)),
        "colors": normalize_indicator_colors(indicator_key, default_indicator_colors(indicator_key)),
        "visible": True,
    }


def _load_support_resistance_context(
    symbol: str,
    *,
    strong: bool,
    interval_label: str,
    period_label: str,
) -> dict[str, object]:
    cleaned_symbol = sanitize_symbol(symbol)
    command_name = "/srk" if strong else "/srd"
    if not cleaned_symbol:
        raise ValueError(f"Format command: `{command_name} BUMI`")

    result = load_market_data(
        symbol=cleaned_symbol,
        interval_label=interval_label,
        period_label=period_label,
    )

    indicator_key = "STRONG_SUPPORT_RESISTANCE" if strong else "NEAREST_SUPPORT_RESISTANCE"
    indicator = _build_indicator_config(indicator_key)
    if strong:
        summary = describe_strong_support_resistance(
            result.data,
            indicator,
            interval_label=result.interval_label,
        )
    else:
        summary = describe_nearest_support_resistance(result.data, indicator)

    return {
        "cleaned_symbol": cleaned_symbol,
        "command_name": command_name,
        "indicator_key": indicator_key,
        "indicator": indicator,
        "result": result,
        "summary": summary,
        "title_text": ("SR Kuat" if strong else "SR Terdekat"),
        "strong": strong,
    }


def _build_level_lines(
    label: str,
    level: dict[str, object] | None,
    current_price: float,
    *,
    strong: bool,
) -> list[str]:
    if level is None:
        return [f"{label}:", "- Belum ketemu level yang valid"]

    lines = [
        f"{label}:",
        f"- Titik: {format_price_value(float(level['price']))}",
        f"- Zona: {format_support_resistance_zone(level)}",
        f"- Jarak: {format_price_distance_percentage(current_price, float(level['price']))}",
        f"- Pantulan: {int(level['bounces'])}",
    ]
    if strong:
        lines.extend(
            [
                f"- Breakout count: {int(level['breakout_count'])}",
                f"- Reversal volume kuat: {int(level['high_volume_reversals'])}",
                f"- Rata-rata volume reversal: {float(level['average_volume_ratio']):.2f}x",
            ]
        )
    return lines


def _format_compact_axis_value(value: float) -> str:
    """Format chart-axis values compactly like 500K, 120M, or 1.2B."""
    absolute_value = abs(float(value))
    if absolute_value < 1e-9:
        return "0"

    suffixes = [
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]
    for threshold, suffix in suffixes:
        if absolute_value >= threshold:
            scaled_value = float(value) / threshold
            if abs(scaled_value) >= 100 or abs(scaled_value - round(scaled_value)) < 0.05:
                return f"{scaled_value:,.0f}{suffix}"
            if abs(scaled_value) >= 10:
                return f"{scaled_value:,.1f}{suffix}"
            return f"{scaled_value:,.2f}{suffix}"

    if abs(float(value) - round(float(value))) < 1e-9:
        return f"{float(value):,.0f}"
    return f"{float(value):,.2f}"


def _build_latest_price_text(result: object, current_price: float) -> str:
    """Build the latest-price line including daily change text when available."""
    previous_close = getattr(result, "previous_close", None)
    if previous_close is None:
        return f"Harga terakhir: {format_price_value(current_price)}"

    try:
        previous_close_value = float(previous_close)
    except (TypeError, ValueError):
        return f"Harga terakhir: {format_price_value(current_price)}"

    if previous_close_value == 0:
        return f"Harga terakhir: {format_price_value(current_price)}"

    change_value = float(current_price) - previous_close_value
    change_percent = (change_value / previous_close_value) * 100.0
    use_integer_price = bool(getattr(result, "uses_bei_price_fractions", False))
    change_text = format_price_change_with_percent(
        change_value,
        change_percent,
        use_integer_price=use_integer_price,
        include_sign=False,
    )
    return f"Harga terakhir: {format_price_value(current_price)} | {change_text}"


def build_support_resistance_message_text(
    symbol: str,
    *,
    strong: bool,
    interval_label: str = DEFAULT_SR_INTERVAL_LABEL,
    period_label: str = DEFAULT_SR_PERIOD_LABEL,
) -> str:
    cleaned_symbol = sanitize_symbol(symbol)
    try:
        context = _load_support_resistance_context(
            symbol,
            strong=strong,
            interval_label=interval_label,
            period_label=period_label,
        )
    except ValueError as exc:
        return str(exc)
    except DataServiceError as exc:
        return f"Data `{sanitize_symbol(symbol)}` belum bisa diambil: {str(exc).strip()}"
    except Exception:
        return f"Data `{sanitize_symbol(symbol)}` gagal diproses sekarang. Coba lagi sebentar."

    result = context["result"]
    summary = context["summary"]
    title_text = str(context["title_text"])
    if summary is None:
        return (
            f"{title_text} {result.symbol}\n"
            f"Interval: {result.interval_label} | Periode: {result.period_label}\n"
            "Data chart belum cukup untuk menghitung level support/resistance."
        )

    current_price = float(summary["current_price"])
    lines = [
        f"{title_text} {result.symbol}",
        f"Nama: {result.company_name}",
        f"Interval: {result.interval_label} | Periode: {result.period_label}",
        _build_latest_price_text(result, current_price),
    ]
    if strong:
        lines.append(f"Timeframe analisis: {summary['analysis_timeframe']}")

    lines.extend(
        [
            "",
            *_build_level_lines("Support", summary.get("support"), current_price, strong=strong),
            "",
            *_build_level_lines("Resistance", summary.get("resistance"), current_price, strong=strong),
        ]
    )
    return "\n".join(lines)


def build_support_resistance_chart_image_bytes(
    symbol: str,
    *,
    strong: bool,
    interval_label: str = DEFAULT_SR_INTERVAL_LABEL,
    period_label: str = DEFAULT_SR_PERIOD_LABEL,
) -> bytes | None:
    try:
        import matplotlib.pyplot as plt
        import mplfinance as mpf
        from PIL import Image
        from matplotlib.lines import Line2D
        from matplotlib.transforms import blended_transform_factory
        from matplotlib.ticker import FuncFormatter
    except ModuleNotFoundError:
        return None

    try:
        context = _load_support_resistance_context(
            symbol,
            strong=strong,
            interval_label=interval_label,
            period_label=period_label,
        )
    except Exception:
        return None

    result = context["result"]
    summary = context["summary"]
    if summary is None:
        return None

    chart_data = result.data.copy()
    chart_data["time"] = pd.to_datetime(chart_data["time"], errors="coerce")
    chart_data = chart_data.dropna(subset=["time"]).copy()
    if chart_data.empty:
        return None

    lookback = SRK_CHART_LOOKBACK if bool(context["strong"]) else SRD_CHART_LOOKBACK
    chart_data = chart_data.tail(min(len(chart_data), lookback)).copy()
    chart_frame = chart_data.set_index("time")[["open", "high", "low", "close", "volume"]].copy()
    chart_frame.columns = ["Open", "High", "Low", "Close", "Volume"]
    chart_frame.index.name = "Date"
    chart_frame["Volume MA20"] = chart_frame["Volume"].rolling(20, min_periods=1).mean()
    volume_overlays = [
        mpf.make_addplot(
            chart_frame["Volume MA20"],
            panel=1,
            color="#f59e0b",
            width=1.8,
            secondary_y=False,
        )
    ]

    market_colors = mpf.make_marketcolors(
        up="#22c55e",
        down="#ef4444",
        wick={"up": "#94f4b2", "down": "#fca5a5"},
        edge={"up": "#22c55e", "down": "#ef4444"},
        volume={"up": "#22c55e", "down": "#ef4444"},
    )
    style = mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        marketcolors=market_colors,
        facecolor="#0b1220",
        figcolor="#0b1220",
        gridcolor="#334155",
        gridstyle="-",
        rc={
            "axes.labelcolor": "#d6deeb",
            "axes.edgecolor": "#0b1220",
            "xtick.color": "#cbd5e1",
            "ytick.color": "#cbd5e1",
            "text.color": "#e2e8f0",
        },
    )

    fig, axes = mpf.plot(
        chart_frame,
        type="candle",
        style=style,
        volume=True,
        addplot=volume_overlays,
        returnfig=True,
        figsize=(13.5, 8.2),
        tight_layout=True,
        panel_ratios=(3, 1),
        title=f"{context['title_text']} {result.symbol} | {result.interval_label} | {result.period_label}",
        ylabel="Price",
        ylabel_lower="Volume",
        xrotation=0,
        datetime_format="%d-%b-%Y",
    )
    fig.subplots_adjust(left=0.095, right=0.965, top=0.92, bottom=0.09, hspace=0.03)

    price_axis = axes[0]
    volume_axis = axes[2]
    label_x = chart_frame.index[-1]
    price_marker_transform = blended_transform_factory(price_axis.transAxes, price_axis.transData)

    price_axis.yaxis.set_label_position("left")
    price_axis.yaxis.tick_left()
    price_axis.tick_params(
        axis="y",
        which="both",
        left=True,
        labelleft=True,
        right=False,
        labelright=False,
        pad=2,
        labelsize=8.5,
    )
    price_axis.set_ylabel("Price", rotation=90, labelpad=14)
    price_axis.yaxis.set_label_coords(-0.055, 0.5)
    price_axis.spines["left"].set_visible(True)
    price_axis.spines["left"].set_color("#334155")
    price_axis.spines["right"].set_visible(False)

    volume_axis.set_ylim(
        bottom=0,
        top=max(
            float(chart_frame["Volume"].max() or 0.0),
            float(chart_frame["Volume MA20"].max() or 0.0),
        )
        * 1.18,
    )
    volume_axis.yaxis.set_label_position("left")
    volume_axis.yaxis.tick_left()
    volume_axis.tick_params(
        axis="y",
        which="both",
        left=True,
        labelleft=True,
        right=False,
        labelright=False,
        pad=2,
        labelsize=8.5,
    )
    volume_axis.set_ylabel("Volume", rotation=90, labelpad=14)
    volume_axis.yaxis.set_label_coords(-0.055, 0.5)
    volume_axis.spines["left"].set_visible(True)
    volume_axis.spines["left"].set_color("#334155")
    volume_axis.spines["right"].set_visible(False)
    volume_axis.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: _format_compact_axis_value(float(value)))
    )
    volume_axis.yaxis.offsetText.set_visible(False)
    volume_axis.legend(
        handles=[Line2D([0], [0], color="#f59e0b", linewidth=1.8, label="Volume MA20")],
        loc="upper left",
        fontsize=8,
        frameon=False,
        labelcolor="#f8fafc",
    )

    support = summary.get("support")
    resistance = summary.get("resistance")
    if support is not None:
        price_axis.axhspan(
            float(support["zone_bottom"]),
            float(support["zone_top"]),
            color="#ef4444",
            alpha=0.10,
        )
        price_axis.axhline(float(support["price"]), color="#ef4444", linestyle="--", linewidth=1.15)
        price_axis.annotate(
            f"Support {format_price_value(float(support['price']))}",
            xy=(label_x, float(support["price"])),
            xytext=(-8, 4),
            textcoords="offset points",
            color="#fecaca",
            fontsize=8,
            va="bottom",
            ha="right",
            bbox={"facecolor": "#7f1d1d", "alpha": 0.40, "edgecolor": "none", "pad": 2},
        )
    if resistance is not None:
        price_axis.axhspan(
            float(resistance["zone_bottom"]),
            float(resistance["zone_top"]),
            color="#22c55e",
            alpha=0.10,
        )
        price_axis.axhline(float(resistance["price"]), color="#22c55e", linestyle="--", linewidth=1.15)
        price_axis.annotate(
            f"Resistance {format_price_value(float(resistance['price']))}",
            xy=(label_x, float(resistance["price"])),
            xytext=(-8, 4),
            textcoords="offset points",
            color="#bbf7d0",
            fontsize=8,
            va="bottom",
            ha="right",
            bbox={"facecolor": "#14532d", "alpha": 0.40, "edgecolor": "none", "pad": 2},
        )

    close_price = float(chart_frame["Close"].iloc[-1])
    price_axis.axhline(close_price, color="#38bdf8", linestyle=":", linewidth=1.1, alpha=0.95, zorder=3)
    price_axis.text(
        0.985,
        close_price,
        f" {format_price_value(close_price)} ",
        transform=price_marker_transform,
        color="#e0f2fe",
        fontsize=8.5,
        va="center",
        ha="right",
        clip_on=True,
        zorder=7,
        bbox={"facecolor": "#0c4a6e", "alpha": 0.90, "edgecolor": "#38bdf8", "pad": 2},
    )

    output = BytesIO()
    fig.savefig(output, format="png", dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    output.seek(0)
    image_bytes = output.getvalue()

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            if width <= 2500 and height <= 1600:
                return image_bytes

            resized_image = image.copy()
            resized_image.thumbnail((2500, 1600))
            normalized_output = BytesIO()
            resized_image.save(normalized_output, format="PNG", optimize=True)
            normalized_output.seek(0)
            return normalized_output.getvalue()
    except Exception:
        return image_bytes


__all__ = [
    "DEFAULT_SR_INTERVAL_LABEL",
    "DEFAULT_SR_PERIOD_LABEL",
    "build_support_resistance_chart_image_bytes",
    "build_support_resistance_message_text",
]
