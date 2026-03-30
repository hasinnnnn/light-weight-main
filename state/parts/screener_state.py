from __future__ import annotations

import streamlit as st


APP_PAGE_CHART = "chart"
APP_PAGE_SCREENER = "screener"


def open_screener_page() -> None:
    """Switch the app shell from chart mode to the Screener page."""
    st.session_state.current_app_page = APP_PAGE_SCREENER


def close_screener_page() -> None:
    """Return from the Screener page back to the main chart view."""
    st.session_state.current_app_page = APP_PAGE_CHART


def is_screener_page_active() -> bool:
    """Return whether the app is currently showing the Screener page."""
    return str(st.session_state.get("current_app_page") or APP_PAGE_CHART).strip().lower() == APP_PAGE_SCREENER


__all__ = [
    "APP_PAGE_CHART",
    "APP_PAGE_SCREENER",
    "close_screener_page",
    "is_screener_page_active",
    "open_screener_page",
]
