from __future__ import annotations

import unittest

from ui.screener import (
    SCREENER_DEFAULT_INTERVAL_LABEL,
    SCREENER_EMA_SYMBOLS,
    build_selected_symbols_summary_html,
    build_screener_editor_widget_key,
    build_screener_symbol_list,
    build_screener_table_layout_css,
    build_screener_table_dataframe,
    build_screener_table_styler,
    resolve_selected_symbols_from_editor_state,
)


class ScreenerPageTests(unittest.TestCase):
    def test_screener_symbol_list_contains_expected_entries(self) -> None:
        self.assertIn("BUMI", SCREENER_EMA_SYMBOLS)
        self.assertIn("WIFI", SCREENER_EMA_SYMBOLS)
        self.assertGreaterEqual(len(SCREENER_EMA_SYMBOLS), 15)
        self.assertEqual(SCREENER_DEFAULT_INTERVAL_LABEL, "1 hari")

    def test_screener_table_dataframe_sorts_by_price_change_descending(self) -> None:
        sample_rows = [
            {
                "no": 1,
                "company_name": "Bumi Resources Tbk.",
                "symbol": "BUMI",
                "current_price_text": "132",
                "price_change_pct": 5.61,
                "price_change_text": "8 (+5.61%)",
                "win_rate_pct": 58.25,
                "win_rate_text": "58.25%",
                "error": "",
            },
            {
                "no": 2,
                "company_name": "PT Medco Energi Internasional Tbk.",
                "symbol": "MEDC",
                "current_price_text": "1,930",
                "price_change_pct": 1.35,
                "price_change_text": "26 (+1.35%)",
                "win_rate_pct": 58.25,
                "win_rate_text": "58.25%",
                "error": "",
            },
            {
                "no": 3,
                "company_name": "PT Darma Henwa Tbk.",
                "symbol": "DEWA",
                "current_price_text": "456",
                "price_change_pct": -2.10,
                "price_change_text": "10 (-2.10%)",
                "win_rate_pct": 41.10,
                "win_rate_text": "41.10%",
                "error": "",
            },
        ]
        frame = build_screener_table_dataframe(sample_rows, selected_symbols=["MEDC"])
        self.assertEqual(
            frame.columns.tolist(),
            ["Pilih", "Kode Saham", "Harga Sekarang", "Price Change", "Win Rate Backtest EMA"],
        )
        self.assertEqual(frame.iloc[0]["Kode Saham"], "BUMI")
        self.assertEqual(frame.iloc[1]["Kode Saham"], "MEDC")
        self.assertEqual(frame.iloc[2]["Kode Saham"], "DEWA")
        self.assertEqual(frame.iloc[0]["Price Change"], "8 (+5.61%)")
        self.assertTrue(bool(frame.iloc[1]["Pilih"]))
        self.assertFalse(bool(frame.iloc[0]["Pilih"]))
        self.assertEqual(build_screener_symbol_list(sample_rows), ["BUMI", "MEDC", "DEWA"])

    def test_screener_table_styler_colors_price_change_and_win_rate(self) -> None:
        frame = build_screener_table_dataframe(
            [
                {
                    "symbol": "BUMI",
                    "current_price_text": "132",
                    "price_change_pct": 5.61,
                    "price_change_text": "8 (+5.61%)",
                    "win_rate_pct": 58.25,
                    "win_rate_text": "58.25%",
                },
                {
                    "symbol": "DEWA",
                    "current_price_text": "456",
                    "price_change_pct": -2.10,
                    "price_change_text": "10 (-2.10%)",
                    "win_rate_pct": 41.10,
                    "win_rate_text": "41.10%",
                },
            ]
        )
        html = build_screener_table_styler(frame).to_html()
        self.assertIn("color: #4ade80", html)
        self.assertIn("color: #f87171", html)
        self.assertIn("text-align: center", html)
        self.assertIn("padding-left: 0.45rem", html)

    def test_selected_symbols_summary_html_is_centered_and_wrapping(self) -> None:
        html = build_selected_symbols_summary_html(["BUMI", "MEDC", "DEWA", "ELSA"])
        self.assertIn("text-align:center", html)
        self.assertIn("overflow-wrap:anywhere", html)
        self.assertIn("BUMI, MEDC, DEWA, ELSA", html)

    def test_screener_table_layout_css_centers_fit_content_editor(self) -> None:
        css = build_screener_table_layout_css()
        self.assertIn("width: fit-content !important", css)
        self.assertIn('div[data-testid="stDataEditor"]', css)
        self.assertIn("display: table", css)
        self.assertIn("margin-left: auto !important", css)

    def test_build_screener_editor_widget_key_appends_refresh_version(self) -> None:
        widget_key = build_screener_editor_widget_key("screener_table_editor_1 hari_YTD_10", 3)
        self.assertEqual(widget_key, "screener_table_editor_1 hari_YTD_10__v3")

    def test_resolve_selected_symbols_from_editor_state_applies_checkbox_changes(self) -> None:
        rows = [
            {
                "symbol": "BUMI",
                "current_price_text": "132",
                "price_change_text": "8 (+5.61%)",
                "win_rate_text": "58.25%",
                "price_change_pct": 5.61,
            },
            {
                "symbol": "MEDC",
                "current_price_text": "1,930",
                "price_change_text": "26 (+1.35%)",
                "win_rate_text": "66.67%",
                "price_change_pct": 1.35,
            },
        ]
        resolved_symbols = resolve_selected_symbols_from_editor_state(
            rows,
            previous_selected_symbols=["MEDC"],
            editor_state={"edited_rows": {0: {"Pilih": True}, 1: {"Pilih": False}}},
        )
        self.assertEqual(resolved_symbols, ["BUMI"])


if __name__ == "__main__":
    unittest.main()
