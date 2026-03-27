from __future__ import annotations

from typing import Any

import streamlit as st

from indicators.catalog import (
    INDICATOR_CATALOG_BY_KEY,
    normalize_indicator_colors,
    normalize_indicator_params,
)


def _normalize_indicator_key(raw_value: Any) -> str:
    return str(raw_value or "").strip().upper().replace("PARABOLLIC_SAR", "PARABOLIC_SAR")


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

    indicator_key = _normalize_indicator_key(raw_indicator.get("key"))
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
            indicator_key = _normalize_indicator_key(raw_indicator)
            if indicator_key not in INDICATOR_CATALOG_BY_KEY or indicator_key in seen_keys:
                continue
            migrated_indicators.append(create_indicator_instance(indicator_key))
            seen_keys.add(indicator_key)

    return migrated_indicators



def _ensure_default_single_ema_visible(indicators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the single default EMA visible so the first-load chart is never blank of overlays."""
    if len(indicators) != 1:
        return indicators
    indicator = indicators[0]
    if indicator.get("key") != "EMA":
        return indicators

    updated_indicator = dict(indicator)
    updated_indicator["visible"] = True
    return [updated_indicator]



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
        st.session_state.active_indicators = _ensure_default_single_ema_visible(normalized_indicators)
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

    st.session_state.active_indicators = _ensure_default_single_ema_visible(normalized_indicators)
    st.session_state.indicator_state_initialized = True



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
        widget_key = indicator_param_widget_key(indicator_id, field_name)
        if widget_key in st.session_state:
            del st.session_state[widget_key]

    normalized_colors = normalize_indicator_colors(indicator["key"], indicator.get("colors"))
    for field_name in normalized_colors:
        widget_key = indicator_color_widget_key(indicator_id, field_name)
        if widget_key in st.session_state:
            del st.session_state[widget_key]

    for field in indicator_definition.get("fields", []):
        if field.get("input_type") == "select":
            widget_key = indicator_param_widget_key(indicator_id, field["name"])
            if widget_key in st.session_state:
                del st.session_state[widget_key]


def select_indicator_color(widget_key: str, color_value: str) -> None:
    """Store one normalized indicator color selection from the editor swatches."""
    st.session_state[widget_key] = str(color_value).strip().lower()

__all__ = [
    "add_indicator",
    "clear_indicator_editor_draft",
    "close_indicator_editor",
    "create_indicator_instance",
    "delete_indicator",
    "find_indicator",
    "indicator_color_widget_key",
    "indicator_param_widget_key",
    "initialize_indicator_state",
    "is_indicator_active",
    "migrate_legacy_indicator_state",
    "next_indicator_id",
    "normalize_indicator_instance",
    "open_indicator_editor",
    "select_indicator_color",
    "sync_indicator_counter",
    "toggle_indicator_visibility",
    "update_indicator_settings",
]

