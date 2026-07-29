from __future__ import annotations

import ast
import unittest
from pathlib import Path

from appearance_readability_correction_v03 import (
    CORRECTION_REVISION,
    load_appearance_readability_corrected_v03,
)


class AppearanceReadabilityCorrectionV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_appearance_readability_corrected_v03("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_appearance_v03.py"
        ).read_text(encoding="utf-8")

    def test_v03_restores_original_non_scarf_materials(self) -> None:
        self.assertEqual(CORRECTION_REVISION, "v03")
        self.assertEqual(self.profile.material_override_map(), {"scarf": "#8A1F2D"})
        self.assertEqual(set(self.profile.quantization_additions), {"#8A1F2D", "#C33A4C"})

    def test_v03_hair_coverage_is_stronger_without_new_object_family(self) -> None:
        self.assertEqual(len(self.profile.hair_transforms), 5)
        self.assertEqual(len(self.profile.temple_fills), 2)
        for item in self.profile.temple_fills:
            self.assertGreaterEqual(item.scale[0], 0.152)
            self.assertGreaterEqual(item.scale[2], 0.218)
            self.assertLessEqual(item.location[1], -0.238)
        for item in self.profile.hair_transforms:
            self.assertTrue(all(value >= 1.0 for value in item.scale_multiplier))

    def test_adapter_forces_full_scarf_material_assignment(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_force_full_scarf_palette", self.adapter_source)
        self.assertIn("obj.data.materials.clear()", self.adapter_source)
        self.assertIn("polygon.material_index = 0", self.adapter_source)
        self.assertIn("MAT_scarf_base_v03", self.adapter_source)
        self.assertIn("MAT_scarf_highlight_v03", self.adapter_source)
        self.assertIn("original_non_scarf_materials_restored", self.adapter_source)

    def test_adapter_reuses_existing_geometry_and_walk(self) -> None:
        self.assertIn("appearance_builder.build_head_and_hair_appearance_v01", self.adapter_source)
        self.assertIn("create_walk_down_actions_v02", self.adapter_source)
        self.assertNotIn("mesh.from_pydata", self.adapter_source)
        self.assertNotIn("bpy.data.meshes.new", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No appearance readability correction v03"):
            load_appearance_readability_corrected_v03("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
