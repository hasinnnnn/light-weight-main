from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from backtest.config import (
    get_default_backtest_general_params,
    normalize_general_backtest_params,
    normalize_strategy_backtest_params,
)
from backtest.engine import (
    _OpenPosition,
    _evaluate_intrabar_risk_exit,
    _evaluate_intrabar_strategy_exit,
    _evaluate_scheduled_exit_reason,
    _format_trade_timestamp,
    _prepare_ohlcv_frame,
    _prepare_strategy_frame,
)
from ui.market_insight_parts.sections.moving_averages import build_ema_note_payload
from ui.screener.data import build_break_ema_strategy_params, load_ema_screener_snapshot


SCREENING_LOOKBACK_BY_INTERVAL = {
    "5 menit": "1mo",
    "15 menit": "1mo",
    "1 jam": "3mo",
    "4 jam": "6mo",
    "1 hari": "1y",
    "1 minggu": "5y",
}


def resolve_screening_period_label(interval_label: str) -> str:
    """Resolve one internal chart period used to keep real-time screening independent from UI backtest period."""
    normalized_interval = str(interval_label or "").strip()
    return SCREENING_LOOKBACK_BY_INTERVAL.get(normalized_interval, "1y")


def _build_event_id(symbol: str, action: str, timestamp_text: str, sequence: int) -> str:
    return f"{str(symbol).strip().upper()}|{str(action).strip().upper()}|{timestamp_text}|{int(sequence)}"


def _simulate_break_ema_execution_events(
    data: pd.DataFrame,
    *,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> tuple[list[dict[str, Any]], pd.Timestamp | None]:
    """Simulate live BREAK_EMA execution bars with the same engine flow used by backtest."""
    source_frame = _prepare_ohlcv_frame(data)
    strategy_params = normalize_strategy_backtest_params(
        "BREAK_EMA",
        build_break_ema_strategy_params(
            ema_period=ema_period,
            breakdown_confirm_mode=breakdown_confirm_mode,
            exit_mode=exit_mode,
        ),
    )
    general_params = normalize_general_backtest_params(get_default_backtest_general_params())
    prepared_strategy = _prepare_strategy_frame(
        frame=source_frame,
        strategy_key="BREAK_EMA",
        strategy_params=strategy_params,
    )
    strategy_frame = prepared_strategy.frame.reset_index(drop=True)
    if strategy_frame.empty:
        return [], None

    risk_management_enabled = bool(prepared_strategy.risk_management_enabled)
    strategy_exit_price_column = prepared_strategy.strategy_exit_price_column
    events: list[dict[str, Any]] = []
    position: _OpenPosition | None = None
    pending_action: dict[str, Any] | None = None
    cooldown_remaining = 0
    event_sequence = 0

    for index in range(len(strategy_frame)):
        row = strategy_frame.iloc[index]
        current_time = pd.Timestamp(row["time"])
        current_open = float(row["open"])
        current_close = float(row["close"])

        if pending_action is not None:
            if pending_action["action"] == "entry" and position is None:
                position = _OpenPosition(
                    qty=1.0,
                    entry_time=current_time,
                    entry_price=current_open,
                    entry_cost=current_open,
                    buy_fee=0.0,
                    highest_close=current_open,
                )
                timestamp_text = _format_trade_timestamp(current_time)
                events.append(
                    {
                        "event_id": _build_event_id("BREAK_EMA", "BUY", timestamp_text, event_sequence),
                        "action": "BUY",
                        "time": current_time,
                        "time_text": timestamp_text,
                        "reason": "entry",
                    }
                )
                event_sequence += 1
            elif pending_action["action"] == "exit" and position is not None:
                timestamp_text = _format_trade_timestamp(current_time)
                events.append(
                    {
                        "event_id": _build_event_id("BREAK_EMA", "SELL", timestamp_text, event_sequence),
                        "action": "SELL",
                        "time": current_time,
                        "time_text": timestamp_text,
                        "reason": str(pending_action["reason"]),
                    }
                )
                event_sequence += 1
                position = None
                cooldown_remaining = int(general_params["cooldown_bars"])
            pending_action = None

        is_last_bar = index == len(strategy_frame) - 1
        if position is not None:
            position.bars_held += 1
            intrabar_exit = (
                _evaluate_intrabar_risk_exit(row, position, general_params)
                if risk_management_enabled
                else None
            )
            strategy_exit_price = (
                _evaluate_intrabar_strategy_exit(row, strategy_exit_price_column)
                if bool(row.get("exit_signal", False))
                else None
            )
            if intrabar_exit is not None:
                exit_reason, _ = intrabar_exit
                timestamp_text = _format_trade_timestamp(current_time)
                events.append(
                    {
                        "event_id": _build_event_id("BREAK_EMA", "SELL", timestamp_text, event_sequence),
                        "action": "SELL",
                        "time": current_time,
                        "time_text": timestamp_text,
                        "reason": str(exit_reason),
                    }
                )
                event_sequence += 1
                position = None
                cooldown_remaining = int(general_params["cooldown_bars"])
            elif strategy_exit_price is not None:
                timestamp_text = _format_trade_timestamp(current_time)
                events.append(
                    {
                        "event_id": _build_event_id("BREAK_EMA", "SELL", timestamp_text, event_sequence),
                        "action": "SELL",
                        "time": current_time,
                        "time_text": timestamp_text,
                        "reason": "strategy_exit",
                    }
                )
                event_sequence += 1
                position = None
                cooldown_remaining = int(general_params["cooldown_bars"])
            else:
                position.highest_close = max(position.highest_close, current_close)
                if not is_last_bar:
                    exit_reason = _evaluate_scheduled_exit_reason(row, position, general_params)
                    if exit_reason is not None:
                        pending_action = {
                            "action": "exit",
                            "reason": exit_reason,
                        }
        elif not is_last_bar:
            can_enter = (
                index >= int(prepared_strategy.warmup_bars)
                and bool(row.get("indicator_ready", False))
                and bool(row.get("entry_signal", False))
                and cooldown_remaining <= 0
            )
            if can_enter:
                pending_action = {"action": "entry"}

        if position is None and cooldown_remaining > 0:
            cooldown_remaining -= 1

    return events, pd.Timestamp(strategy_frame.iloc[-1]["time"])


def build_break_ema_signal_snapshot(
    symbol: str,
    *,
    interval_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> dict[str, Any]:
    """Build one selected symbol snapshot for live screener alerts and Telegram notes."""
    screening_period_label = resolve_screening_period_label(interval_label)
    screener_snapshot = load_ema_screener_snapshot(
        symbol=symbol,
        interval_label=interval_label,
        period_label=screening_period_label,
        ema_period=ema_period,
        breakdown_confirm_mode=breakdown_confirm_mode,
        exit_mode=exit_mode,
    )
    row = dict(screener_snapshot["row"])
    market_result = screener_snapshot.get("market_result")
    note_payload = (
        build_ema_note_payload(
            market_result,
            {"length": int(ema_period)},
            {"line": "#38bdf8"},
        )
        if market_result is not None
        else None
    )

    events: list[dict[str, Any]] = []
    latest_bar_time: pd.Timestamp | None = None
    simulation_error = ""
    if market_result is not None:
        try:
            events, latest_bar_time = _simulate_break_ema_execution_events(
                market_result.data,
                ema_period=ema_period,
                breakdown_confirm_mode=breakdown_confirm_mode,
                exit_mode=exit_mode,
            )
        except Exception as exc:
            simulation_error = str(exc)

    symbol_key = str(row.get("symbol") or symbol).strip().upper()
    normalized_events: list[dict[str, Any]] = []
    for sequence, event in enumerate(events):
        normalized_events.append(
            {
                **event,
                "symbol": symbol_key,
                "company_name": row.get("company_name") or symbol_key,
                "event_id": _build_event_id(symbol_key, str(event["action"]), str(event["time_text"]), sequence),
            }
        )

    fresh_events = [
        event
        for event in normalized_events
        if latest_bar_time is not None and pd.Timestamp(event["time"]) == latest_bar_time
    ]
    return {
        "symbol": symbol_key,
        "company_name": row.get("company_name") or symbol_key,
        "row": row,
        "note_payload": note_payload,
        "events": normalized_events,
        "fresh_events": fresh_events,
        "latest_bar_time": latest_bar_time,
        "screening_period_label": screening_period_label,
        "error": row.get("error") or simulation_error,
    }


def build_break_ema_signal_snapshots(
    symbols: Iterable[str],
    *,
    interval_label: str,
    ema_period: int,
    breakdown_confirm_mode: str,
    exit_mode: str,
) -> list[dict[str, Any]]:
    """Build live screener snapshots for the selected symbols only."""
    return [
        build_break_ema_signal_snapshot(
            str(symbol).strip().upper(),
            interval_label=interval_label,
            ema_period=ema_period,
            breakdown_confirm_mode=breakdown_confirm_mode,
            exit_mode=exit_mode,
        )
        for symbol in symbols
        if str(symbol).strip()
    ]


__all__ = [
    "SCREENING_LOOKBACK_BY_INTERVAL",
    "build_break_ema_signal_snapshot",
    "build_break_ema_signal_snapshots",
    "resolve_screening_period_label",
]
