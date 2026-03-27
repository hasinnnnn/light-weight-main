from __future__ import annotations

from typing import Any

import streamlit as st

from state.app_state import close_indicator_editor, find_indicator, indicator_param_widget_key, update_indicator_settings
from indicators.candle_patterns import ALL_CANDLE_PATTERN_KEYS, CANDLE_PATTERN_DEFINITIONS
from indicators.chart_patterns import ALL_CHART_PATTERN_KEYS, CHART_PATTERN_DEFINITIONS
from indicators.catalog import INDICATOR_CATALOG_BY_KEY, normalize_indicator_colors, normalize_indicator_params
from .helpers import (
    render_indicator_color_controls,
    render_nearest_support_resistance_info,
    render_pattern_toggle_section,
    render_strong_support_resistance_info,
)
def render_indicator_editor_view(indicator_id: str) -> None:
    """Show the edit form inside the indicator modal."""
    indicator = find_indicator(indicator_id)
    if indicator is None:
        st.info("Indikator yang dipilih sudah tidak ada.")
        if st.button("Tutup", use_container_width=True):
            close_indicator_editor()
            st.rerun(scope="fragment")
        return

    indicator_definition = INDICATOR_CATALOG_BY_KEY[indicator["key"]]
    normalized_params = normalize_indicator_params(indicator["key"], indicator.get("params"))
    normalized_colors = normalize_indicator_colors(indicator["key"], indicator.get("colors"))

    st.markdown(f"**{indicator_definition['modal_label']}**")
    if indicator_definition["fields"] or indicator_definition.get("color_fields"):
        st.caption("Ubah parameter dan warna indikator, lalu klik OK untuk menerapkan ke chart.")
    else:
        st.caption("Indikator ini tidak punya parameter yang perlu diubah.")

    input_values: dict[str, Any] = {}
    for field in indicator_definition["fields"]:
        widget_key = indicator_param_widget_key(indicator_id, field["name"])
        is_select_field = str(field.get("input_type", "")).strip().lower() == "select" or bool(field.get("options"))
        is_float_field = (
            str(field.get("value_type", "")).strip().lower() == "float"
            or isinstance(field.get("default"), float)
        )
        if widget_key not in st.session_state:
            if is_select_field:
                st.session_state[widget_key] = str(normalized_params[field["name"]])
            else:
                st.session_state[widget_key] = (
                    float(normalized_params[field["name"]])
                    if is_float_field
                    else int(normalized_params[field["name"]])
                )
        if is_select_field:
            options = field.get("options", [])
            option_values = [str(option.get("value") if isinstance(option, dict) else option) for option in options]
            option_labels = {
                str(option.get("value")): str(option.get("label"))
                for option in options
                if isinstance(option, dict)
            }
            current_value = str(st.session_state[widget_key])
            if current_value not in option_values and option_values:
                current_value = option_values[0]
                st.session_state[widget_key] = current_value
            input_values[field["name"]] = st.selectbox(
                field["label"],
                options=option_values,
                index=(option_values.index(current_value) if current_value in option_values else 0),
                format_func=lambda value: option_labels.get(str(value), str(value)),
                key=widget_key,
            )
        elif is_float_field:
            input_values[field["name"]] = float(
                st.number_input(
                    field["label"],
                    min_value=float(field["min_value"]),
                    step=float(field.get("step", 0.1)),
                    value=float(st.session_state[widget_key]),
                    format=str(field.get("format", "%.2f")),
                    key=widget_key,
                )
            )
        else:
            input_values[field["name"]] = int(
                st.number_input(
                    field["label"],
                    min_value=int(field["min_value"]),
                    step=1,
                    value=int(st.session_state[widget_key]),
                    format="%d",
                    key=widget_key,
                )
            )
    if indicator["key"] == "CANDLE_PATTERN":
        st.markdown("**Pattern Candle yang Tampil**")
        st.caption("Pilih pola candle yang ingin diberi label di chart utama.")
        input_values.update(
            render_pattern_toggle_section(
                indicator_id=indicator_id,
                pattern_keys=ALL_CANDLE_PATTERN_KEYS,
                pattern_definitions=CANDLE_PATTERN_DEFINITIONS,
                normalized_params=normalized_params,
            )
        )
    elif indicator["key"] == "CHART_PATTERN":
        st.markdown("**Pattern Chart yang Tampil**")
        st.caption("Pilih pola chart yang ingin digambar atau diberi label di chart utama.")
        input_values.update(
            render_pattern_toggle_section(
                indicator_id=indicator_id,
                pattern_keys=ALL_CHART_PATTERN_KEYS,
                pattern_definitions=CHART_PATTERN_DEFINITIONS,
                normalized_params=normalized_params,
            )
        )

    color_values = render_indicator_color_controls(
        indicator_id=indicator_id,
        indicator_definition=indicator_definition,
        normalized_colors=normalized_colors,
    )

    if indicator["key"] == "NEAREST_SUPPORT_RESISTANCE":
        render_nearest_support_resistance_info(
            params=normalize_indicator_params(indicator["key"], input_values),
            colors=normalize_indicator_colors(indicator["key"], color_values),
        )
    elif indicator["key"] == "STRONG_SUPPORT_RESISTANCE":
        render_strong_support_resistance_info(
            params=normalize_indicator_params(indicator["key"], input_values),
            colors=normalize_indicator_colors(indicator["key"], color_values),
        )

    cancel_col, ok_col = st.columns(2)
    cancel_clicked = cancel_col.button("Batal", use_container_width=True)
    save_clicked = ok_col.button(
        "OK" if indicator_definition["fields"] or indicator_definition.get("color_fields") else "Tutup",
        use_container_width=True,
    )

    if cancel_clicked:
        close_indicator_editor()
        st.rerun(scope="fragment")

    if save_clicked:
        update_indicator_settings(indicator_id, input_values, color_values)
        close_indicator_editor()
        st.rerun()



