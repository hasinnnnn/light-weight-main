from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

import pandas as pd
import streamlit as st


SCREENER_SELECTION_COLUMN = "Pilih"
SCREENER_SELECTED_SYMBOLS_STATE_KEY = "screener_selected_symbols"
SCREENER_EDITOR_VERSION_STATE_KEY = "screener_table_editor_version"
SCREENER_POSITIVE_TONE = "#4ade80"
SCREENER_NEGATIVE_TONE = "#f87171"
SCREENER_NEUTRAL_TONE = "#dbe7f5"
SCREENER_TABLE_TEXT_COLUMNS = [
    "Kode Saham",
    "Harga Sekarang",
    "Price Change",
    "Win Rate Backtest EMA",
]


def _sort_screener_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            row.get("price_change_pct") is None,
            -(float(row.get("price_change_pct") or 0.0)),
            str(row.get("symbol") or "").upper(),
        ),
    )


def build_screener_symbol_list(rows: Iterable[dict[str, Any]]) -> list[str]:
    """Collect one de-duplicated symbol list following the active table order."""
    ordered_symbols: list[str] = []
    seen_symbols: set[str] = set()
    for row in _sort_screener_rows(rows):
        symbol = str(row.get("symbol") or row.get("Kode Saham") or "").strip().upper()
        if not symbol or symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)
        ordered_symbols.append(symbol)
    return ordered_symbols


def build_screener_table_dataframe(
    rows: list[dict[str, Any]],
    selected_symbols: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Build one display dataframe for the Screener table."""
    normalized_selection = {
        str(symbol or "").strip().upper()
        for symbol in (selected_symbols or [])
        if str(symbol or "").strip()
    }

    prepared_rows: list[dict[str, Any]] = []
    for row in _sort_screener_rows(rows):
        symbol = str(row.get("symbol") or "").strip().upper()
        prepared_rows.append(
            {
                SCREENER_SELECTION_COLUMN: symbol in normalized_selection,
                "Kode Saham": symbol or "-",
                "Harga Sekarang": row.get("current_price_text") or "-",
                "Price Change": row.get("price_change_text") or "-",
                "Win Rate Backtest EMA": row.get("win_rate_text") or "-",
            }
        )

    return pd.DataFrame(prepared_rows)


def _parse_percent_text(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text or text in {"-", "—"}:
        return None

    percent_matches = re.findall(r"([-+]?\d+(?:,\d+)*(?:\.\d+)?)\s*%", text)
    if percent_matches:
        try:
            return float(percent_matches[-1].replace(",", ""))
        except ValueError:
            return None

    sanitized_text = text.replace("%", "").replace(",", "")
    try:
        return float(sanitized_text)
    except ValueError:
        return None


def _style_price_change_cell(value: Any) -> str:
    parsed_value = _parse_percent_text(value)
    if parsed_value is None:
        return f"color: {SCREENER_NEUTRAL_TONE}; font-weight: 700;"
    if parsed_value > 0:
        return f"color: {SCREENER_POSITIVE_TONE}; font-weight: 700;"
    if parsed_value < 0:
        return f"color: {SCREENER_NEGATIVE_TONE}; font-weight: 700;"
    return f"color: {SCREENER_NEUTRAL_TONE}; font-weight: 700;"


def _style_win_rate_cell(value: Any) -> str:
    parsed_value = _parse_percent_text(value)
    if parsed_value is None:
        return f"color: {SCREENER_NEUTRAL_TONE}; font-weight: 700;"
    if parsed_value >= 50.0:
        return f"color: {SCREENER_POSITIVE_TONE}; font-weight: 700;"
    return f"color: {SCREENER_NEGATIVE_TONE}; font-weight: 700;"


def build_screener_table_styler(table_frame: pd.DataFrame) -> Any:
    """Build the table styler for non-editable colored columns."""
    return (
        table_frame.style
        .set_properties(
            subset=SCREENER_TABLE_TEXT_COLUMNS,
            **{
                "text-align": "center",
                "padding-left": "0.45rem",
                "padding-right": "0.45rem",
                "padding-top": "0.2rem",
                "padding-bottom": "0.2rem",
            },
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("text-align", "center"),
                        ("padding-left", "0.45rem"),
                        ("padding-right", "0.45rem"),
                        ("padding-top", "0.2rem"),
                        ("padding-bottom", "0.2rem"),
                    ],
                }
            ],
            overwrite=False,
        )
        .map(_style_price_change_cell, subset=["Price Change"])
        .map(_style_win_rate_cell, subset=["Win Rate Backtest EMA"])
    )


def resolve_selected_symbols_from_editor_state(
    rows: list[dict[str, Any]],
    previous_selected_symbols: Iterable[str] | None,
    editor_state: Mapping[str, Any] | None,
) -> list[str]:
    """Resolve checkbox selection from one editor-state diff payload."""
    table_frame = build_screener_table_dataframe(rows, selected_symbols=previous_selected_symbols)
    edited_rows = dict(editor_state.get("edited_rows", {})) if isinstance(editor_state, Mapping) else {}

    for row_index, row_changes in edited_rows.items():
        try:
            normalized_row_index = int(row_index)
        except (TypeError, ValueError):
            continue
        if not 0 <= normalized_row_index < len(table_frame):
            continue
        if not isinstance(row_changes, Mapping) or SCREENER_SELECTION_COLUMN not in row_changes:
            continue
        table_frame.at[normalized_row_index, SCREENER_SELECTION_COLUMN] = bool(
            row_changes[SCREENER_SELECTION_COLUMN]
        )

    return [
        str(symbol).strip().upper()
        for symbol in table_frame.loc[table_frame[SCREENER_SELECTION_COLUMN].fillna(False), "Kode Saham"].tolist()
        if str(symbol).strip()
    ]


def build_screener_editor_widget_key(editor_key: str, refresh_version: int) -> str:
    """Build one versioned widget key so the editor can be safely recreated."""
    return f"{editor_key}__v{int(refresh_version)}"


def _sync_selected_symbols_from_editor_change(
    rows: list[dict[str, Any]],
    editor_key: str,
) -> None:
    previous_selected_symbols = st.session_state.get(SCREENER_SELECTED_SYMBOLS_STATE_KEY, [])
    editor_state = st.session_state.get(editor_key)
    st.session_state[SCREENER_SELECTED_SYMBOLS_STATE_KEY] = resolve_selected_symbols_from_editor_state(
        rows,
        previous_selected_symbols,
        editor_state if isinstance(editor_state, Mapping) else None,
    )


def build_selected_symbols_summary_html(selected_symbols: Iterable[str]) -> str:
    """Build one centered summary block that wraps cleanly on narrow layouts."""
    normalized_symbols = [
        str(symbol).strip().upper()
        for symbol in selected_symbols
        if str(symbol).strip()
    ]
    details_text = f" ({', '.join(normalized_symbols)})" if normalized_symbols else ""
    return (
        "<div style=\""
        "width:100%;"
        "text-align:center;"
        "margin-top:0.35rem;"
        "color:#9fb0c8;"
        "font-size:0.9rem;"
        "line-height:1.65;"
        "overflow-wrap:anywhere;"
        "word-break:break-word;"
        "padding:0.1rem 0.75rem 0 0.75rem;"
        "\">"
        f"Terpilih: {len(normalized_symbols)} saham{details_text}"
        "</div>"
    )


def build_screener_table_layout_css() -> str:
    """Build layout CSS so the Screener data editor sits in the visual center."""
    return """
        <style>
        div[data-testid="stDataFrame"],
        div[data-testid="stDataEditor"] {
            width: fit-content !important;
            max-width: 100%;
            display: table;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        div[data-testid="stDataFrame"] > div,
        div[data-testid="stDataEditor"] > div,
        div[data-testid="stDataEditor"] [role="grid"] {
            width: fit-content !important;
            max-width: 100%;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        </style>
    """


def render_screener_table_layout_styles() -> None:
    """Inject lightweight layout overrides for centering the Screener table block."""
    st.markdown(build_screener_table_layout_css(), unsafe_allow_html=True)


def render_screener_table(
    rows: list[dict[str, Any]],
    *,
    editor_key: str,
) -> None:
    """Render the native Streamlit Screener table with selectable rows."""
    editor_refresh_version = int(st.session_state.get(SCREENER_EDITOR_VERSION_STATE_KEY, 0))
    active_editor_key = build_screener_editor_widget_key(editor_key, editor_refresh_version)
    available_symbols = build_screener_symbol_list(rows)
    selected_symbols = st.session_state.get(SCREENER_SELECTED_SYMBOLS_STATE_KEY, [])
    table_frame = build_screener_table_dataframe(rows, selected_symbols=selected_symbols)

    if table_frame.empty:
        st.info("Belum ada data screener.")
        st.session_state[SCREENER_SELECTED_SYMBOLS_STATE_KEY] = []
        return

    render_screener_table_layout_styles()
    outer_left, center_col, outer_right = st.columns([0.8, 8.4, 0.8])
    with center_col:
        table_left, table_center, table_right = st.columns([1.6, 4.6, 1.6])
        with table_center:
            table_styler = build_screener_table_styler(table_frame)
            st.data_editor(
                table_styler,
                key=active_editor_key,
                width="content",
                row_height=34,
                hide_index=True,
                num_rows="fixed",
                on_change=_sync_selected_symbols_from_editor_change,
                args=(rows, active_editor_key),
                column_order=[
                    SCREENER_SELECTION_COLUMN,
                    "Kode Saham",
                    "Harga Sekarang",
                    "Price Change",
                    "Win Rate Backtest EMA",
                ],
                disabled=[
                    "Kode Saham",
                    "Harga Sekarang",
                    "Price Change",
                    "Win Rate Backtest EMA",
                ],
                column_config={
                    SCREENER_SELECTION_COLUMN: st.column_config.CheckboxColumn(
                        "Pilih",
                        help="Centang saham yang nanti mau dipakai saat fitur Screen diaktifkan.",
                        width="small",
                    ),
                    "Kode Saham": st.column_config.TextColumn("Kode Saham", width="small"),
                    "Harga Sekarang": st.column_config.TextColumn("Harga Sekarang", width="small"),
                    "Price Change": st.column_config.TextColumn("Price Change", width="medium"),
                    "Win Rate Backtest EMA": st.column_config.TextColumn("Win Rate Backtest EMA", width="medium"),
                },
            )

        selected_symbols = list(st.session_state.get(SCREENER_SELECTED_SYMBOLS_STATE_KEY, []))
        with table_center:
            spacer_left, bulk_check_col, bulk_uncheck_col, spacer_right = st.columns([1.1, 1.0, 1.0, 1.1])
            with bulk_check_col:
                if st.button(
                    "Check All",
                    key=f"{editor_key}_check_all",
                    use_container_width=True,
                    disabled=not available_symbols or len(selected_symbols) == len(available_symbols),
                ):
                    st.session_state[SCREENER_SELECTED_SYMBOLS_STATE_KEY] = list(available_symbols)
                    st.session_state[SCREENER_EDITOR_VERSION_STATE_KEY] = editor_refresh_version + 1
                    st.rerun()
            with bulk_uncheck_col:
                if st.button(
                    "Uncheck All",
                    key=f"{editor_key}_uncheck_all",
                    use_container_width=True,
                    disabled=not selected_symbols,
                ):
                    st.session_state[SCREENER_SELECTED_SYMBOLS_STATE_KEY] = []
                    st.session_state[SCREENER_EDITOR_VERSION_STATE_KEY] = editor_refresh_version + 1
                    st.rerun()

            st.markdown(build_selected_symbols_summary_html(selected_symbols), unsafe_allow_html=True)


__all__ = [
    "SCREENER_EDITOR_VERSION_STATE_KEY",
    "SCREENER_SELECTED_SYMBOLS_STATE_KEY",
    "SCREENER_SELECTION_COLUMN",
    "build_screener_editor_widget_key",
    "build_screener_table_layout_css",
    "build_screener_symbol_list",
    "build_selected_symbols_summary_html",
    "build_screener_table_dataframe",
    "build_screener_table_styler",
    "render_screener_table_layout_styles",
    "resolve_selected_symbols_from_editor_state",
    "render_screener_table",
]
