from __future__ import annotations

from typing import Any

import streamlit as st

from backtest.config import (
    build_backtest_preview_indicator_config,
    get_default_backtest_general_params,
    get_default_break_ema_params,
    get_default_parabolic_sar_params,
    get_default_volume_breakout_params,
    get_default_macd_params,
    get_default_rsi_params,
    normalize_general_backtest_params,
)
from backtest.engine import BacktestError, run_backtest
from indicators.catalog import (
    INDICATOR_CATALOG_BY_KEY,
    normalize_indicator_colors,
    normalize_indicator_params,
)
from ui.backtest_parameter_dialog import clear_backtest_parameter_draft

def sync_indicator_counter(indicator_id: str) -> None:
    """Keep the generated indicator id counter ahead of restored session ids."""
    if not indicator_id.startswith("indicator-"):
        return
    try:
        indicator_number = int(indicator_id.removeprefix("indicator-"))
    except ValueError:
        return
    st.session_state.indicator_id_counter = max(
        int(st.session_state.indicator_id_counter),
        indicator_number,
    )


def next_indicator_id() -> str:
    """Return a stable unique id for a new indicator instance."""
    indicator_number = int(st.session_state.indicator_id_counter) + 1
    st.session_state.indicator_id_counter = indicator_number
    return f"indicator-{indicator_number}"


def create_indicator_instance(indicator_key: str) -> dict[str, Any]:
    """Create one indicator config entry for session state."""
    return {
        "id": next_indicator_id(),
        "key": indicator_key,
        "params": normalize_indicator_params(indicator_key),
        "colors": normalize_indicator_colors(indicator_key),
        "visible": True,
    }


def normalize_indicator_instance(raw_indicator: Any) -> dict[str, Any] | None:
    """Normalize one raw indicator state entry into the current structure."""
    if not isinstance(raw_indicator, dict):
        return None

    indicator_key = str(raw_indicator.get("key") or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if indicator_key not in INDICATOR_CATALOG_BY_KEY:
        return None

    indicator_id = str(raw_indicator.get("id") or "").strip() or next_indicator_id()
    sync_indicator_counter(indicator_id)

    return {
        "id": indicator_id,
        "key": indicator_key,
        "params": normalize_indicator_params(indicator_key, raw_indicator.get("params")),
        "colors": normalize_indicator_colors(indicator_key, raw_indicator.get("colors")),
        "visible": bool(raw_indicator.get("visible", True)),
    }


def migrate_legacy_indicator_state(raw_indicators: Any) -> list[dict[str, Any]]:
    """Convert the old string-based indicator list into the new object structure."""
    migrated_indicators = [create_indicator_instance("EMA")]
    seen_keys = {"EMA"}

    if isinstance(raw_indicators, list):
        for raw_indicator in raw_indicators:
            indicator_key = str(raw_indicator or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
            if indicator_key not in INDICATOR_CATALOG_BY_KEY or indicator_key in seen_keys:
                continue
            migrated_indicators.append(create_indicator_instance(indicator_key))
            seen_keys.add(indicator_key)

    return migrated_indicators


def initialize_indicator_state() -> None:
    """Prepare indicator state, including migration from older app versions."""
    if st.session_state.indicator_state_initialized:
        normalized_indicators: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for raw_indicator in st.session_state.active_indicators or []:
            normalized_indicator = normalize_indicator_instance(raw_indicator)
            if normalized_indicator is None or normalized_indicator["id"] in seen_ids:
                continue
            normalized_indicators.append(normalized_indicator)
            seen_ids.add(normalized_indicator["id"])
        st.session_state.active_indicators = normalized_indicators
        return

    raw_indicators = st.session_state.active_indicators
    if isinstance(raw_indicators, list) and raw_indicators and isinstance(raw_indicators[0], dict):
        normalized_indicators = []
        for raw_indicator in raw_indicators:
            normalized_indicator = normalize_indicator_instance(raw_indicator)
            if normalized_indicator is not None:
                normalized_indicators.append(normalized_indicator)
    else:
        normalized_indicators = migrate_legacy_indicator_state(raw_indicators)

    if not normalized_indicators:
        normalized_indicators = [create_indicator_instance("EMA")]

    st.session_state.active_indicators = normalized_indicators
    st.session_state.indicator_state_initialized = True


def initialize_session_state() -> None:
    """Set app defaults so selections and the last result survive reruns."""
    defaults = {
        "symbol_input": "BUMI",
        "interval_option": "1 hari",
        "period_option": "YTD",
        "loaded_result": None,
        "last_error": "",
        "selected_company_name": "",
        "active_indicators": [],
        "indicator_id_counter": 0,
        "indicator_state_initialized": False,
        "indicator_editor_id": "",
        "pending_load": True,
        "selected_backtest_strategy": "",
        "backtest_search_query": "",
        "backtest_params_general": get_default_backtest_general_params(),
        "backtest_params_rsi": get_default_rsi_params(),
        "backtest_params_macd": get_default_macd_params(),
        "backtest_params_break_ema": get_default_break_ema_params(),
        "backtest_params_parabolic_sar": get_default_parabolic_sar_params(),
        "backtest_params_volume_breakout": get_default_volume_breakout_params(),
        "backtest_result": None,
        "backtest_period_label": "YTD",
        "backtest_enabled": False,
        "backtest_refresh_requested": False,
        "show_indicator_preview": True,
        "backtest_parameter_modal_open": False,
        "backtest_last_error": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    st.session_state.backtest_params_general = normalize_general_backtest_params(
        st.session_state.backtest_params_general
    )
    params_version = int(st.session_state.get("backtest_general_params_version", 0))
    if params_version < 2:
        if (
            st.session_state.backtest_params_general["position_sizing_mode"] == "fixed_percent_of_equity"
            and abs(float(st.session_state.backtest_params_general["position_size_value"]) - 100.0) < 1e-9
        ):
            st.session_state.backtest_params_general["position_sizing_mode"] = "fixed_nominal"
            st.session_state.backtest_params_general["position_size_value"] = 1_000_000.0
        st.session_state.backtest_general_params_version = 2

    if params_version < 3:
        if abs(float(st.session_state.backtest_params_general["initial_capital"]) - 100_000_000.0) < 1e-9:
            st.session_state.backtest_params_general["initial_capital"] = 10_000_000.0
        st.session_state.backtest_general_params_version = 3

    selection_version = int(st.session_state.get("backtest_strategy_selection_version", 0))
    if selection_version < 1:
        if (
            str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR") == "RSI"
            and not st.session_state.backtest_enabled
            and st.session_state.backtest_result is None
        ):
            st.session_state.selected_backtest_strategy = ""
        st.session_state.backtest_strategy_selection_version = 1

    st.session_state.backtest_period_label = st.session_state.period_option
    st.session_state.show_indicator_preview = bool(
        st.session_state.backtest_params_general.get("show_indicator_preview", True)
    )
    initialize_indicator_state()


def request_data_reload() -> None:
    """Flag the app to fetch fresh data on the next rerun."""
    st.session_state.pending_load = True
    st.session_state.backtest_last_error = ""
    st.session_state.backtest_period_label = st.session_state.period_option


def selected_backtest_strategy_params() -> dict[str, Any]:
    """Return the parameter dictionary for the selected backtest strategy."""
    selected_strategy = str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if selected_strategy == "VOLUME_BREAKOUT":
        return st.session_state.backtest_params_volume_breakout
    if selected_strategy == "PARABOLIC_SAR":
        return st.session_state.backtest_params_parabolic_sar
    if selected_strategy == "BREAK_EMA":
        return st.session_state.backtest_params_break_ema
    if selected_strategy == "MACD":
        return st.session_state.backtest_params_macd
    if selected_strategy == "RSI":
        return st.session_state.backtest_params_rsi
    return {}


def open_backtest_parameter_editor() -> None:
    """Open the parameter editor view inside the indicator dialog."""
    clear_backtest_parameter_draft()
    st.session_state.backtest_parameter_modal_open = True


def close_backtest_parameter_editor() -> None:
    """Close the parameter editor view inside the indicator dialog."""
    clear_backtest_parameter_draft()
    st.session_state.backtest_parameter_modal_open = False


def remove_backtest_indicator() -> None:
    """Remove the active backtest selection and disable its chart output."""
    close_backtest_parameter_editor()
    st.session_state.backtest_enabled = False
    st.session_state.backtest_refresh_requested = False
    st.session_state.backtest_result = None
    st.session_state.backtest_last_error = ""
    st.session_state.selected_backtest_strategy = ""


def build_effective_indicator_configs() -> list[dict[str, Any]]:
    """Add temporary backtest preview indicators when needed."""
    indicator_configs = list(st.session_state.active_indicators)
    selected_strategy = str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    if selected_strategy not in {"RSI", "MACD", "BREAK_EMA", "PARABOLIC_SAR", "VOLUME_BREAKOUT"}:
        return indicator_configs

    should_render_backtest_indicator = (
        bool(st.session_state.backtest_enabled)
        or st.session_state.backtest_result is not None
        or bool(st.session_state.show_indicator_preview)
    )
    if not should_render_backtest_indicator:
        return indicator_configs

    try:
        preview_indicator = build_backtest_preview_indicator_config(
            selected_strategy,
            selected_backtest_strategy_params(),
        )
    except ValueError:
        return indicator_configs

    if isinstance(preview_indicator, list):
        return [*indicator_configs, *preview_indicator]
    return [*indicator_configs, preview_indicator]


def is_backtest_indicator_config(indicator: dict[str, Any]) -> bool:
    """Return whether one indicator row belongs to the backtest flow."""
    return str(indicator.get("source") or "").strip().lower() == "backtest"


def run_selected_backtest(show_spinner: bool = True) -> None:
    """Run the currently selected strategy against the active chart data."""
    result = st.session_state.loaded_result
    if result is None:
        st.session_state.backtest_result = None
        st.session_state.backtest_last_error = "Load chart dulu sebelum menjalankan backtest."
        st.session_state.backtest_refresh_requested = False
        return

    selected_strategy = str(st.session_state.selected_backtest_strategy or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")
    st.session_state.backtest_period_label = st.session_state.period_option
    st.session_state.show_indicator_preview = bool(
        st.session_state.backtest_params_general.get("show_indicator_preview", True)
    )

    try:
        if show_spinner:
            with st.spinner("Menjalankan backtest..."):
                st.session_state.backtest_result = run_backtest(
                    data=result.data,
                    strategy_key=selected_strategy,
                    general_params=st.session_state.backtest_params_general,
                    strategy_params=selected_backtest_strategy_params(),
                    symbol=result.symbol,
                    interval_label=result.interval_label,
                    period_label=st.session_state.backtest_period_label,
                    use_lot_sizing=result.uses_bei_price_fractions,
                )
        else:
            st.session_state.backtest_result = run_backtest(
                data=result.data,
                strategy_key=selected_strategy,
                general_params=st.session_state.backtest_params_general,
                strategy_params=selected_backtest_strategy_params(),
                symbol=result.symbol,
                interval_label=result.interval_label,
                period_label=st.session_state.backtest_period_label,
                use_lot_sizing=result.uses_bei_price_fractions,
            )
    except BacktestError as exc:
        st.session_state.backtest_result = None
        st.session_state.backtest_last_error = str(exc)
    else:
        st.session_state.backtest_last_error = ""
    finally:
        st.session_state.backtest_refresh_requested = False


def is_indicator_active(indicator_key: str) -> bool:
    """Check whether one indicator type is already active."""
    return any(
        indicator["key"] == indicator_key
        for indicator in st.session_state.active_indicators
    )


def find_indicator(indicator_id: str) -> dict[str, Any] | None:
    """Return one active indicator by id."""
    for indicator in st.session_state.active_indicators:
        if indicator["id"] == indicator_id:
            return indicator
    return None


def add_indicator(indicator_key: str) -> None:
    """Append one indicator to the active list if it is not active yet."""
    if indicator_key not in INDICATOR_CATALOG_BY_KEY or is_indicator_active(indicator_key):
        return
    st.session_state.active_indicators = [
        *st.session_state.active_indicators,
        create_indicator_instance(indicator_key),
    ]


def toggle_indicator_visibility(indicator_id: str) -> None:
    """Toggle whether an indicator is rendered on the chart."""
    updated_indicators: list[dict[str, Any]] = []
    for indicator in st.session_state.active_indicators:
        if indicator["id"] == indicator_id:
            updated_indicator = dict(indicator)
            updated_indicator["visible"] = not bool(indicator.get("visible", True))
            updated_indicators.append(updated_indicator)
        else:
            updated_indicators.append(indicator)
    st.session_state.active_indicators = updated_indicators


def delete_indicator(indicator_id: str) -> None:
    """Remove one indicator from the active list."""
    st.session_state.active_indicators = [
        indicator
        for indicator in st.session_state.active_indicators
        if indicator["id"] != indicator_id
    ]
    if st.session_state.indicator_editor_id == indicator_id:
        close_indicator_editor()


def update_indicator_settings(
    indicator_id: str,
    params: dict[str, Any],
    colors: dict[str, Any],
) -> None:
    """Store a normalized parameter and color update for one indicator."""
    updated_indicators: list[dict[str, Any]] = []
    for indicator in st.session_state.active_indicators:
        if indicator["id"] == indicator_id:
            updated_indicator = dict(indicator)
            updated_indicator["params"] = normalize_indicator_params(
                indicator["key"],
                params,
            )
            updated_indicator["colors"] = normalize_indicator_colors(
                indicator["key"],
                colors,
            )
            updated_indicators.append(updated_indicator)
        else:
            updated_indicators.append(indicator)
    st.session_state.active_indicators = updated_indicators


def open_indicator_editor(indicator_id: str) -> None:
    """Open the in-modal editor for one indicator."""
    clear_indicator_editor_draft(indicator_id)
    st.session_state.indicator_editor_id = indicator_id


def close_indicator_editor() -> None:
    """Close the in-modal indicator editor view."""
    current_indicator_id = st.session_state.indicator_editor_id
    if current_indicator_id:
        clear_indicator_editor_draft(current_indicator_id)
    st.session_state.indicator_editor_id = ""



def indicator_param_widget_key(indicator_id: str, field_name: str) -> str:
    """Build the widget key for one indicator parameter input."""
    return f"indicator_edit_{indicator_id}_{field_name}"


def indicator_color_widget_key(indicator_id: str, field_name: str) -> str:
    """Build the widget key for one indicator color input."""
    return f"indicator_color_{indicator_id}_{field_name}"


def clear_indicator_editor_draft(indicator_id: str) -> None:
    """Clear draft widgets for one indicator editor."""
    indicator = find_indicator(indicator_id)
    if indicator is None:
        return

    indicator_definition = INDICATOR_CATALOG_BY_KEY[indicator["key"]]
    normalized_params = normalize_indicator_params(indicator["key"], indicator.get("params"))
    for field_name in normalized_params:
        st.session_state.pop(indicator_param_widget_key(indicator_id, str(field_name)), None)
    for color_field in indicator_definition.get("color_fields", []):
        st.session_state.pop(indicator_color_widget_key(indicator_id, color_field["name"]), None)


def select_indicator_color(widget_key: str, color_value: str) -> None:
    """Store a preset color selection for the current indicator editor."""
    st.session_state[widget_key] = color_value.lower()












