from __future__ import annotations

import ast
import unittest
from pathlib import Path


class WalkAnimationBuilderV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "walk_animation_builder_v03.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_walk_down_v03.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_locks_approved_appearance_and_reuses_channel_mapping(self) -> None:
        self.assertIn('("v22", "v25")', self.builder_source)
        self.assertIn('_APPROVED_APPEARANCE_REVISION = "v03"', self.builder_source)
        self.assertIn("previous_builder._create_idle_action", self.builder_source)
        self.assertIn("previous_builder._create_walk_action", self.builder_source)
        self.assertIn("load_walk_down_profile_v02", self.builder_source)
        self.assertIn("create_walk_down_actions_v03", self.builder_source)

    def test_builder_changes_only_action_data(self) -> None:
        self.assertIn('walk_action["geometry_changed"] = False', self.builder_source)
        self.assertIn('walk_action["material_changed"] = False', self.builder_source)
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("bpy.data.meshes.new", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_reuses_appearance_v03_and_patches_manifest_profile_paths(self) -> None:
        self.assertIn("appearance_adapter_v03._build_armor_appearance_v03", self.adapter_source)
        self.assertIn("factory._create_actions = create_walk_down_actions_v03", self.adapter_source)
        self.assertIn(
            "factory._write_run_manifest = _write_run_manifest_walk_down_v03",
            self.adapter_source,
        )
        self.assertIn(
            "walk_manifest_adapter.load_walk_down_profile_v01 = load_walk_down_profile_v02",
            self.adapter_source,
        )
        self.assertIn("walk_manifest_adapter.WALK_PROFILE_PATH = WALK_PROFILE_PATH", self.adapter_source)
        self.assertIn("walk_manifest_adapter.WALK_BUILDER_PATH = WALK_BUILDER_PATH", self.adapter_source)

    def test_manifest_records_motion_refinement_and_locked_appearance(self) -> None:
        self.assertIn('"vertical_amplitude_reduced": True', self.adapter_source)
        self.assertIn('"support_foot_contact_refined": True', self.adapter_source)
        self.assertIn('"approved_appearance_v03_locked": True', self.adapter_source)
        self.assertIn('"geometry_changed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertIn('"hair_changed": False', self.adapter_source)
        self.assertIn('"scarf_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
