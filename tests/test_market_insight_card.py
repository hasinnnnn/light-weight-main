from __future__ import annotations

import unittest

from ui.market_insight_parts.market_card import build_price_change_state


class MarketInsightCardTests(unittest.TestCase):
    def test_build_price_change_state_formats_positive_bei_move(self) -> None:
        change_class, change_text = build_price_change_state(
            current_price=1630.0,
            previous_close=1615.0,
            use_integer_price=True,
        )
        self.assertEqual(change_class, "change-up")
        self.assertEqual(change_text, "▲ 15 (+0.93%)")

    def test_build_price_change_state_formats_negative_bei_move(self) -> None:
        change_class, change_text = build_price_change_state(
            current_price=1585.0,
            previous_close=1615.0,
            use_integer_price=True,
        )
        self.assertEqual(change_class, "change-down")
        self.assertEqual(change_text, "▼ 30 (-1.86%)")

    def test_build_price_change_state_returns_dash_when_previous_close_missing(self) -> None:
        change_class, change_text = build_price_change_state(
            current_price=1630.0,
            previous_close=None,
            use_integer_price=True,
        )
        self.assertEqual(change_class, "change-flat")
        self.assertEqual(change_text, "-")


if __name__ == "__main__":
    unittest.main()
