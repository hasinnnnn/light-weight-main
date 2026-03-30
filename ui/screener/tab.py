from __future__ import annotations

import streamlit as st


def render_screener_tab() -> dict[str, bool]:
    """Render the Screener launcher tab inside the indicator dialog."""
    actions = {"open_page": False}

    st.text_input(
        "Cari screener",
        key="screener_search_query",
        placeholder="Cari screener...",
    )
    search_query = str(st.session_state.get("screener_search_query") or "").strip().lower()

    screeners = [
        {
            "key": "EMA",
            "label": "EMA",
            "description": "Starter screener untuk workflow EMA. Page tujuan masih kosong untuk tahap awal.",
        }
    ]
    filtered_screeners = [
        screener
        for screener in screeners
        if not search_query or search_query in str(screener["label"]).lower()
    ]

    if not filtered_screeners:
        st.info("Belum ada screener yang cocok dengan pencarian itu.")
        return actions

    for screener in filtered_screeners:
        with st.container(border=True):
            info_col, action_col = st.columns([6.0, 1.25])
            with info_col:
                st.markdown(f"**{screener['label']}**")
                st.caption(str(screener["description"]))
            with action_col:
                if st.button(
                    "Buka",
                    key=f"screener_open_{screener['key']}",
                    use_container_width=True,
                ):
                    actions["open_page"] = True

    return actions


__all__ = ["render_screener_tab"]
