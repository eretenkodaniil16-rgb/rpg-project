from __future__ import annotations

import unittest

from hair_palette_v10 import load_hair_palette_v10


class HairPaletteV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.palette = load_hair_palette_v10()

    def test_palette_matches_head_v10_proxy_v13(self) -> None:
        self.assertEqual(self.palette.revision, "v10")
        self.assertEqual(self.palette.proxy_revision, "v13")
        self.palette.assert_valid()

    def test_palette_is_dark_quantization_compatible_reference_ramp(self) -> None:
        self.assertEqual(
            self.palette.facet_colors,
            ("#0B0602", "#1A120A", "#26180B", "#3C2411"),
        )
        self.assertEqual(self.palette.separator, "#060102")
        self.assertNotIn("#978687", self.palette.all_colors)
        self.assertNotIn("#B09B9D", self.palette.all_colors)
        self.assertNotIn("#D2BABB", self.palette.all_colors)
        self.assertNotIn("#DDC9C6", self.palette.all_colors)

    def test_highlight_remains_below_pale_skin_value(self) -> None:
        highlight_rgb = tuple(
            int(self.palette.highlight[index : index + 2], 16)
            for index in (1, 3, 5)
        )
        skin_base_rgb = (0xD2, 0xBA, 0xBB)
        self.assertLess(max(highlight_rgb), min(skin_base_rgb))


if __name__ == "__main__":
    unittest.main()
