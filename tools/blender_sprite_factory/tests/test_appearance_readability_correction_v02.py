from __future__ import annotations

import ast
import unittest
from pathlib import Path

from appearance_readability_correction_v02 import (
    CORRECTION_REVISION,
    load_appearance_readability_corrected_v02,
)


class AppearanceReadabilityCorrectionV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_appearance_readability_corrected_v02("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_appearance_v02.py"
        ).read_text(encoding="utf-8")

    def test_corrected_profile_remains_valid(self) -> None:
        self.assertEqual(CORRECTION_REVISION, "v02")
        self.profile.assert_valid()
        self.assertEqual(self.profile.material_override_map()["scarf"], "#8A1F2D")
        self.assertEqual(self.profile.scarf_highlight_hex, "#C33A4C")

    def test_temple_coverage_is_stronger_than_v01(self) -> None:
        side_transforms = [item for item in self.profile.hair_transforms if item.zone == "side"]
        self.assertEqual(len(side_transforms), 2)
        for item in side_transforms:
            self.assertGreaterEqual(item.scale_multiplier[0], 1.12)
            self.assertGreaterEqual(item.scale_multiplier[2], 1.12)
            self.assertLessEqual(item.world_offset[1], -0.020)
        for item in self.profile.temple_fills:
            self.assertGreaterEqual(item.scale[0], 0.132)
            self.assertGreaterEqual(item.scale[2], 0.196)

    def test_adapter_patches_linear_color_conversion_without_new_geometry_system(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("appearance_builder._rgb = factory._hex_to_linear_rgb", self.adapter_source)
        self.assertIn("appearance_builder._PROFILE = corrected_profile", self.adapter_source)
        self.assertIn("create_walk_down_actions_v02", self.adapter_source)
        self.assertNotIn("mesh.from_pydata", self.adapter_source)
        self.assertNotIn("bpy.data.meshes.new", self.adapter_source)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No appearance readability correction v02"):
            load_appearance_readability_corrected_v02("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
