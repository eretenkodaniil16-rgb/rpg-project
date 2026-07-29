from __future__ import annotations

import ast
import unittest
from pathlib import Path


class WalkAnimationBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "walk_animation_builder.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_walk_down_v02.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_uses_structured_profile_and_compatible_geometry_states(self) -> None:
        self.assertIn("load_walk_down_profile_v01", self.builder_source)
        self.assertIn("_ALLOWED_GEOMETRY_STATES", self.builder_source)
        self.assertIn('(\"v21\", \"v24\")', self.builder_source)
        self.assertIn('(\"v22\", \"v25\")', self.builder_source)
        self.assertIn("create_walk_down_actions_v02", self.builder_source)
        self.assertNotIn("left_thigh = (", self.builder_source)
        self.assertNotIn("right_thigh = tuple", self.builder_source)

    def test_walk_action_contains_full_body_channels(self) -> None:
        for channel in (
            'pose.bones["pelvis"].location',
            'pose.bones["pelvis"].rotation_euler',
            'pose.bones["spine"].rotation_euler',
            'pose.bones["chest"].rotation_euler',
            'pose.bones["head"].rotation_euler',
            'pose.bones["foot.L"].rotation_euler',
            'pose.bones["foot.R"].rotation_euler',
            'pose.bones["cloth.L"].rotation_euler',
            'pose.bones["cloth.C"].rotation_euler',
            'pose.bones["cloth.R"].rotation_euler',
        ):
            self.assertIn(channel, self.builder_source)

    def test_builder_does_not_translate_root_or_change_geometry(self) -> None:
        self.assertNotIn('pose.bones["root"].location', self.builder_source)
        self.assertIn('walk_action["root_translation_used"] = False', self.builder_source)
        self.assertIn('walk_action["geometry_changed"] = False', self.builder_source)
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("bpy.data.meshes.new", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_reuses_head_v21_and_overrides_only_actions_and_manifest(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v21", self.adapter_source)
        self.assertIn("factory._create_actions = create_walk_down_actions_v02", self.adapter_source)
        self.assertIn(
            "factory._write_run_manifest = _write_run_manifest_walk_down_v02",
            self.adapter_source,
        )
        self.assertIn('"geometry_changed": False', self.adapter_source)
        self.assertIn('"hair_geometry_changed": False', self.adapter_source)
        self.assertIn('"equipment_sides_changed": False', self.adapter_source)
        self.assertIn('"rig_bone_count_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
