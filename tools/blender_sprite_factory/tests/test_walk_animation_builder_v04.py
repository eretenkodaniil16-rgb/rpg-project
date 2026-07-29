from __future__ import annotations

import ast
import unittest
from pathlib import Path


class WalkAnimationBuilderV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "walk_animation_builder_v04.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_walk_down_v04.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_loads_v04_profile_and_locks_appearance(self) -> None:
        self.assertIn("load_walk_down_profile_v03", self.builder_source)
        self.assertIn("previous_builder._assert_approved_appearance", self.builder_source)
        self.assertIn('walk_action["appearance_locked"] = True', self.builder_source)
        self.assertIn('walk_action["phase_height_balanced"] = True', self.builder_source)
        self.assertIn('walk_action["geometry_changed"] = False', self.builder_source)
        self.assertIn('walk_action["material_changed"] = False', self.builder_source)

    def test_builder_changes_actions_only(self) -> None:
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("bpy.data.meshes.new", self.builder_source)
        self.assertNotIn('pose.bones["root"].location', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_reuses_approved_appearance_pipeline(self) -> None:
        self.assertIn("import blender_sprite_factory_walk_down_v03 as previous_adapter", self.adapter_source)
        self.assertIn("create_walk_down_actions_v04", self.adapter_source)
        self.assertIn("_write_run_manifest_walk_down_v04", self.adapter_source)
        self.assertIn("_patch_manifest_chain_for_walk_v04", self.adapter_source)
        self.assertIn('"approved_appearance_v03_locked": True', self.adapter_source)
        self.assertIn('"hair_changed": False', self.adapter_source)
        self.assertIn('"scarf_changed": False', self.adapter_source)
        self.assertIn('"equipment_sides_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
