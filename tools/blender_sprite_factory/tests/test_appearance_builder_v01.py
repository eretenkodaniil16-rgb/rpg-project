from __future__ import annotations

import ast
import unittest
from pathlib import Path


class AppearanceBuilderV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "appearance_builder_v01.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_appearance_v01.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_hair_fill_preserves_crown_and_adds_two_temples(self) -> None:
        self.assertIn("_EXPECTED_PREVIOUS_HAIR_COUNT = 10", self.builder_source)
        self.assertIn("_EXPECTED_FINAL_HAIR_COUNT = 12", self.builder_source)
        self.assertIn("_create_temple_fills", self.builder_source)
        self.assertIn("must not modify crown vertex coordinates", self.builder_source)
        self.assertIn("reduced hair volume", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_material_override_uses_explicit_constant_color(self) -> None:
        self.assertIn("appearance_texture_link_disabled", self.builder_source)
        self.assertIn("material.node_tree.links.remove", self.builder_source)
        self.assertIn("MAT_scarf_highlight_v01", self.builder_source)
        self.assertIn("_assign_scarf_highlight", self.builder_source)

    def test_clothing_changes_stay_in_existing_modules(self) -> None:
        self.assertIn("_build_clothing_details", self.builder_source)
        self.assertIn("factory._register(context, detail, spec.module_id, spec.bone_name)", self.builder_source)
        self.assertNotIn("factory._create_rig", self.builder_source)
        self.assertNotIn("mesh.from_pydata", self.builder_source)

    def test_adapter_preserves_walk_and_overrides_only_appearance_builders(self) -> None:
        self.assertIn("factory._create_actions = create_walk_down_actions_v02", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v22", self.adapter_source)
        self.assertIn("factory._build_head_and_hair = build_head_and_hair_appearance_v01", self.adapter_source)
        self.assertIn("factory._build_armor = build_armor_appearance_v01", self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)
        self.assertIn('"equipment_sides_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
