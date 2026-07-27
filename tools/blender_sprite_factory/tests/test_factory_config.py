from __future__ import annotations

import unittest
from pathlib import Path

from factory_config import (
    CONTACT_SHEET_BACKGROUND_HEX,
    load_factory_config,
    validate_required_files,
)


class FactoryConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]
        cls.manifest = (
            cls.repo_root
            / "tools/blender_sprite_factory/configs/human_warrior_m01.json"
        )
        cls.config = load_factory_config(cls.manifest, cls.repo_root)

    def test_contract_reuses_approved_sprite_dimensions(self) -> None:
        config = self.config
        self.assertEqual(config.character_id, "human_warrior_m01")
        self.assertEqual(config.technical.canvas_width, 96)
        self.assertEqual(config.technical.canvas_height, 96)
        self.assertEqual(config.technical.pilot_sprite_height, 78)
        self.assertEqual(config.technical.baseline_y, 91)
        self.assertEqual(config.camera["elevation_degrees"], 47.0)
        self.assertEqual(config.camera["projection"], "ORTHOGRAPHIC")

    def test_directions_are_real_rotations_not_mirrors(self) -> None:
        self.assertEqual(
            self.config.directions,
            {
                "down": 0.0,
                "left": -90.0,
                "right": 90.0,
                "up": 180.0,
            },
        )

    def test_canonical_physical_sides_are_locked(self) -> None:
        self.assertEqual(
            self.config.physical_sides,
            {
                "large_silver_pauldron": "left",
                "small_dark_pauldron": "right",
                "sword_scabbard": "left",
                "pouch": "right",
            },
        )

    def test_pilot_has_required_vertical_slice(self) -> None:
        self.assertEqual(self.config.animations["idle"]["frames"], (1,))
        self.assertEqual(
            self.config.animations["walk_down"]["frames"],
            (1, 2, 3, 4, 5, 6),
        )
        self.assertGreaterEqual(len(self.config.required_bones), 20)
        self.assertEqual(len(self.config.required_modules), 14)

    def test_reference_pack_and_texture_slots_exist(self) -> None:
        self.assertEqual(validate_required_files(self.config), [])

    def test_contact_sheet_background_cannot_hide_palette_pixels(self) -> None:
        self.assertNotIn(
            CONTACT_SHEET_BACKGROUND_HEX.upper(),
            {color.upper() for color in self.config.quantization_palette},
        )

    def test_skin_palette_is_pale_cool_and_has_quantized_tones(self) -> None:
        skin = self.config.material_slots["skin"]
        self.assertEqual(skin.base_color.upper(), "#D2BABB")
        palette = {color.upper() for color in self.config.quantization_palette}
        self.assertTrue(
            {"#978687", "#B09B9D", "#D2BABB", "#DDC9C6"}.issubset(palette)
        )
        red = int(skin.base_color[1:3], 16)
        green = int(skin.base_color[3:5], 16)
        blue = int(skin.base_color[5:7], 16)
        self.assertGreaterEqual(blue, green)
        self.assertLessEqual(blue - green, 2)
        self.assertGreater(red, blue)
        self.assertGreaterEqual(red, 0xD0)

    def test_blender_support_window_is_explicit(self) -> None:
        self.assertEqual(self.config.recommended_blender_lts, (5, 2))
        self.assertEqual(self.config.minimum_blender, (4, 5))
        self.config.assert_blender_version((5, 2, 0))
        with self.assertRaisesRegex(RuntimeError, "не поддерживается"):
            self.config.assert_blender_version((4, 4, 9))


if __name__ == "__main__":
    unittest.main()
