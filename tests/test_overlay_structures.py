from __future__ import annotations

import unittest

from charts.renderers_parts.overlay_structures import _build_support_resistance_axis_label


class OverlayStructureTests(unittest.TestCase):
    def test_nearest_support_label_is_compact(self) -> None:
        self.assertEqual(_build_support_resistance_axis_label("nearest", "support", 3), "SD x3")

    def test_nearest_resistance_label_is_compact(self) -> None:
        self.assertEqual(_build_support_resistance_axis_label("nearest", "resistance", 1), "RD x1")

    def test_strong_support_label_is_compact(self) -> None:
        self.assertEqual(_build_support_resistance_axis_label("strong", "support", 4), "SK x4")

    def test_strong_resistance_label_is_compact(self) -> None:
        self.assertEqual(_build_support_resistance_axis_label("strong", "resistance", 2), "RK x2")


if __name__ == "__main__":
    unittest.main()
