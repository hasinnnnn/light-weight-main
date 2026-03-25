from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from backtest.config import (
    filter_frame_to_chart_period,
    get_strategy_label,
    normalize_general_backtest_params,
    normalize_strategy_backtest_params,
)
from backtest.metrics import build_trade_log, calculate_backtest_metrics
from backtest.models import BacktestResult, Trade
from strategies.base_strategy import StrategyPreparation
from strategies.macd_strategy import prepare_macd_strategy
from strategies.rsi_strategy import prepare_rsi_strategy


class BacktestError(Exception):
    """Raised when the requested backtest cannot be executed safely."""


@dataclass
class _OpenPosition:
    qty: float
    entry_time: pd.Timestamp
    entry_price: float
    entry_cost: float
    buy_fee: float
    bars_held: int = 0
    highest_close: float = 0.0


PREPARERS = {
    "RSI": prepare_rsi_strategy,
    "MACD": prepare_macd_strategy,
}


def _prepare_ohlcv_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize one chart dataframe for strategy simulation."""
    if data is None or data.empty:
        raise BacktestError("Load chart dulu sebelum menjalankan backtest.")

    required_columns = ["time", "open", "high", "low", "close", "volume"]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise BacktestError(
            f"Data chart tidak lengkap untuk backtest. Kolom hilang: {', '.join(missing_columns)}."
        )

    prepared = data[required_columns].copy()
    prepared["time"] = pd.to_datetime(prepared["time"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared["volume"] = prepared["volume"].fillna(0.0)
    prepared = prepared.dropna(subset=["time", "open", "high", "low", "close"])
    prepared = prepared.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    prepared = prepared.reset_index(drop=True)

    if len(prepared) < 3:
        raise BacktestError("Data chart belum cukup untuk menghitung sinyal dan eksekusi backtest.")
    return prepared


def _percent_to_rate(value: Any) -> float:
    """Convert one percentage input into a decimal rate."""
    return max(float(value), 0.0) / 100.0


def _determine_budget(cash: float, general_params: dict[str, Any]) -> float:
    """Return the order budget for the next entry."""
    if general_params["position_sizing_mode"] == "fixed_nominal":
        return min(float(general_params["position_size_value"]), cash)
    return cash * (float(general_params["position_size_value"]) / 100.0)


def _normalize_entry_qty(raw_qty: float, use_lot_sizing: bool, lot_size: int) -> float:
    """Convert one raw share quantity into the tradable quantity."""
    normalized_qty = max(float(raw_qty), 0.0)
    if not use_lot_sizing or lot_size <= 1:
        return normalized_qty
    return float(math.floor(normalized_qty / float(lot_size)) * lot_size)


def _format_trade_timestamp(timestamp: pd.Timestamp) -> str:
    """Format one trade timestamp for the UI."""
    if timestamp.hour == 0 and timestamp.minute == 0 and timestamp.second == 0:
        return timestamp.strftime("%Y-%m-%d")
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def _evaluate_exit_reason(
    row: pd.Series,
    position: _OpenPosition,
    general_params: dict[str, Any],
) -> str | None:
    """Check whether the open position should exit based on the current close."""
    close_price = float(row["close"])
    stop_loss_pct = float(general_params["stop_loss_pct"])
    take_profit_pct = float(general_params["take_profit_pct"])
    trailing_stop_pct = float(general_params["trailing_stop_pct"])
    max_holding_bars = int(general_params["max_holding_bars"])

    if stop_loss_pct > 0:
        stop_loss_level = position.entry_price * (1.0 - (stop_loss_pct / 100.0))
        if close_price <= stop_loss_level:
            return "stop_loss"

    if take_profit_pct > 0:
        take_profit_level = position.entry_price * (1.0 + (take_profit_pct / 100.0))
        if close_price >= take_profit_level:
            return "take_profit"

    if trailing_stop_pct > 0 and position.highest_close > 0:
        trailing_stop_level = position.highest_close * (1.0 - (trailing_stop_pct / 100.0))
        if close_price <= trailing_stop_level:
            return "trailing_stop"

    if bool(row.get("exit_signal", False)):
        return "strategy_exit"

    if max_holding_bars > 0 and position.bars_held >= max_holding_bars:
        return "max_holding_bars"

    return None


def _close_position(
    position: _OpenPosition,
    exit_time: pd.Timestamp,
    raw_exit_price: float,
    sell_fee_rate: float,
    slippage_rate: float,
    exit_reason: str,
) -> tuple[float, Trade]:
    """Close one open position and return the released cash plus trade log row."""
    executed_exit_price = raw_exit_price * (1.0 - slippage_rate)
    gross_proceeds = position.qty * executed_exit_price
    sell_fee = gross_proceeds * sell_fee_rate
    net_proceeds = gross_proceeds - sell_fee
    pnl_nominal = net_proceeds - position.entry_cost
    pnl_pct = (pnl_nominal / position.entry_cost * 100.0) if position.entry_cost > 0 else 0.0

    trade = Trade(
        entry_datetime=_format_trade_timestamp(position.entry_time),
        entry_price=position.entry_price,
        exit_datetime=_format_trade_timestamp(exit_time),
        exit_price=executed_exit_price,
        qty=position.qty,
        pnl_nominal=pnl_nominal,
        pnl_pct=pnl_pct,
        exit_reason=exit_reason,
        bars_held=position.bars_held,
        buy_fee=position.buy_fee,
        sell_fee=sell_fee,
    )
    return net_proceeds, trade


def _build_equity_row(
    timestamp: pd.Timestamp,
    cash: float,
    position: _OpenPosition | None,
    mark_price: float,
    sell_fee_rate: float,
) -> dict[str, float | pd.Timestamp]:
    """Build one mark-to-market equity point for the equity curve."""
    position_value = 0.0
    if position is not None:
        position_value = position.qty * mark_price * (1.0 - sell_fee_rate)
    return {
        "time": timestamp,
        "cash": cash,
        "position_value": position_value,
        "equity": cash + position_value,
    }


def _prepare_strategy_frame(
    frame: pd.DataFrame,
    strategy_key: str,
    strategy_params: dict[str, Any],
) -> StrategyPreparation:
    """Prepare indicator columns and signals for one strategy."""
    normalized_key = str(strategy_key or "").strip().upper()
    try:
        preparer = PREPARERS[normalized_key]
    except KeyError as exc:
        raise BacktestError(f"Strategi backtest `{strategy_key}` belum didukung.") from exc
    return preparer(frame, strategy_params)


def run_backtest(
    data: pd.DataFrame,
    strategy_key: str,
    general_params: dict[str, Any] | None,
    strategy_params: dict[str, Any] | None,
    symbol: str,
    interval_label: str,
    period_label: str,
    use_lot_sizing: bool = False,
) -> BacktestResult:
    """Run one long-only backtest without look-ahead bias."""
    normalized_key = str(strategy_key or "").strip().upper()
    if not normalized_key:
        raise BacktestError("Pilih strategi backtest dulu sebelum klik Jalankan Backtest.")

    normalized_general_params = normalize_general_backtest_params(general_params)
    normalized_strategy_params = normalize_strategy_backtest_params(
        normalized_key,
        strategy_params,
    )
    source_frame = _prepare_ohlcv_frame(data)
    source_frame = filter_frame_to_chart_period(source_frame, period_label)
    if len(source_frame) < 3:
        raise BacktestError("Periode chart aktif terlalu pendek untuk backtest yang aman.")

    prepared_strategy = _prepare_strategy_frame(
        frame=source_frame,
        strategy_key=normalized_key,
        strategy_params=normalized_strategy_params,
    )
    strategy_frame = prepared_strategy.frame.reset_index(drop=True)
    if len(strategy_frame) < 3:
        raise BacktestError("Data yang tersisa belum cukup setelah indikator dihitung.")

    initial_capital = float(normalized_general_params["initial_capital"])
    buy_fee_rate = _percent_to_rate(normalized_general_params["buy_fee_pct"])
    sell_fee_rate = _percent_to_rate(normalized_general_params["sell_fee_pct"])
    slippage_rate = _percent_to_rate(normalized_general_params["slippage_pct"])
    resolved_lot_size = 100 if use_lot_sizing else 1

    cash = initial_capital
    position: _OpenPosition | None = None
    trades: list[Trade] = []
    equity_rows: list[dict[str, float | pd.Timestamp]] = []
    pending_action: dict[str, Any] | None = None
    cooldown_remaining = 0

    for index in range(len(strategy_frame)):
        row = strategy_frame.iloc[index]
        current_time = pd.Timestamp(row["time"])
        current_open = float(row["open"])
        current_close = float(row["close"])

        if pending_action is not None:
            if pending_action["action"] == "entry" and position is None:
                order_budget = _determine_budget(cash, normalized_general_params)
                executed_entry_price = current_open * (1.0 + slippage_rate)
                qty = _normalize_entry_qty(
                    order_budget / (executed_entry_price * (1.0 + buy_fee_rate)),
                    use_lot_sizing=use_lot_sizing,
                    lot_size=resolved_lot_size,
                )
                gross_cost = qty * executed_entry_price
                buy_fee = gross_cost * buy_fee_rate
                total_cost = gross_cost + buy_fee
                if total_cost > cash and executed_entry_price > 0:
                    qty = _normalize_entry_qty(
                        cash / (executed_entry_price * (1.0 + buy_fee_rate)),
                        use_lot_sizing=use_lot_sizing,
                        lot_size=resolved_lot_size,
                    )
                    gross_cost = qty * executed_entry_price
                    buy_fee = gross_cost * buy_fee_rate
                    total_cost = gross_cost + buy_fee
                if qty > 0 and total_cost > 0 and total_cost <= cash + 1e-9:
                    cash -= total_cost
                    position = _OpenPosition(
                        qty=qty,
                        entry_time=current_time,
                        entry_price=executed_entry_price,
                        entry_cost=total_cost,
                        buy_fee=buy_fee,
                        highest_close=current_close,
                    )
            elif pending_action["action"] == "exit" and position is not None:
                released_cash, closed_trade = _close_position(
                    position=position,
                    exit_time=current_time,
                    raw_exit_price=current_open,
                    sell_fee_rate=sell_fee_rate,
                    slippage_rate=slippage_rate,
                    exit_reason=str(pending_action["reason"]),
                )
                cash += released_cash
                trades.append(closed_trade)
                position = None
                cooldown_remaining = int(normalized_general_params["cooldown_bars"])
            pending_action = None

        if position is not None:
            position.bars_held += 1
            position.highest_close = max(position.highest_close, current_close)

        is_last_bar = index == len(strategy_frame) - 1
        if position is not None and not is_last_bar:
            exit_reason = _evaluate_exit_reason(row, position, normalized_general_params)
            if exit_reason is not None:
                pending_action = {
                    "action": "exit",
                    "reason": exit_reason,
                }
        elif position is None and not is_last_bar:
            can_enter = (
                index >= int(prepared_strategy.warmup_bars)
                and bool(row.get("indicator_ready", False))
                and bool(row.get("entry_signal", False))
                and cooldown_remaining <= 0
            )
            if can_enter:
                pending_action = {"action": "entry"}

        equity_rows.append(
            _build_equity_row(
                timestamp=current_time,
                cash=cash,
                position=position,
                mark_price=current_close,
                sell_fee_rate=sell_fee_rate,
            )
        )

        if position is None and cooldown_remaining > 0:
            cooldown_remaining -= 1

        if is_last_bar and position is not None:
            released_cash, closed_trade = _close_position(
                position=position,
                exit_time=current_time,
                raw_exit_price=current_close,
                sell_fee_rate=sell_fee_rate,
                slippage_rate=slippage_rate,
                exit_reason="end_of_data",
            )
            cash += released_cash
            trades.append(closed_trade)
            position = None
            equity_rows[-1] = _build_equity_row(
                timestamp=current_time,
                cash=cash,
                position=None,
                mark_price=current_close,
                sell_fee_rate=sell_fee_rate,
            )

    equity_curve = pd.DataFrame(equity_rows)
    if equity_curve.empty:
        raise BacktestError("Backtest tidak menghasilkan equity curve yang valid.")

    metrics = calculate_backtest_metrics(
        equity_curve=equity_curve,
        trades=trades,
        initial_capital=initial_capital,
    )
    trade_log = build_trade_log(trades)

    return BacktestResult(
        strategy_key=normalized_key,
        strategy_label=get_strategy_label(normalized_key),
        symbol=symbol,
        interval_label=interval_label,
        period_label=period_label,
        uses_lot_sizing=bool(use_lot_sizing),
        lot_size=resolved_lot_size,
        general_params=normalized_general_params,
        strategy_params=normalized_strategy_params,
        metrics=metrics,
        trade_log=trade_log,
        equity_curve=equity_curve,
        chart_frame=strategy_frame,
        entry_rule_summary=prepared_strategy.entry_rule_summary,
        exit_rule_summary=prepared_strategy.exit_rule_summary,
        initial_capital=initial_capital,
        final_equity=float(equity_curve["equity"].iloc[-1]),
    )
