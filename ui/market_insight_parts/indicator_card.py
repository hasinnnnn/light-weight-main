from __future__ import annotations

import streamlit as st

from indicators.catalog import normalize_indicator_colors, normalize_indicator_params

from .sections import SECTION_BUILDERS


def render_indicator_explanation_card(indicator_configs: list[dict[str, object]] | None = None) -> None:
    """Render a descriptive card below the main chart for active indicators that need context."""
    result = st.session_state.loaded_result
    if result is None:
        return

    section_html: list[str] = []
    active_indicators = indicator_configs if indicator_configs is not None else (st.session_state.active_indicators or [])

    for indicator in active_indicators:
        if not bool(indicator.get("visible", True)):
            continue

        indicator_key = str(indicator.get("key") or "").strip().upper()
        builder = SECTION_BUILDERS.get(indicator_key)
        if builder is None:
            continue

        params = normalize_indicator_params(indicator_key, indicator.get("params"))
        colors = normalize_indicator_colors(indicator_key, indicator.get("colors"))
        section = builder(result=result, params=params, colors=colors)
        if section:
            section_html.append(section)

    if not section_html:
        return

    st.markdown(
        (
            '<div class="indicator-note-card">'
            '<div class="indicator-note-card-title">Keterangan</div>'
            f'{"".join(section_html)}'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


__all__ = ["render_indicator_explanation_card"]
