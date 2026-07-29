from __future__ import annotations

import ast
import unittest
from pathlib import Path


class WalkUpAnimationBuilderV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "walk_up_animation_builder_v01.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_walk_up_v01.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_preserves_all_approved_cycles_and_appearance(self) -> None:
        self.assertIn("create_walk_right_actions_v01", self.builder_source)
        self.assertIn('action["approved_walk_down_revision"] = "v04"', self.builder_source)
        self.assertIn('action["approved_walk_left_revision"] = "v01"', self.builder_source)
        self.assertIn('action["approved_walk_right_revision"] = "v01"', self.builder_source)
        self.assertIn('action["appearance_locked"] = True', self.builder_source)
        self.assertIn('action["geometry_changed"] = False', self.builder_source)
        self.assertIn('action["material_changed"] = False', self.builder_source)

    def test_action_contains_full_body_and_cloth_channels(self) -> None:
        for channel in (
            'pose.bones["pelvis"].location',
            'pose.bones["spine"].rotation_euler',
            'pose.bones["chest"].rotation_euler',
            'pose.bones["head"].rotation_euler',
            'pose.bones["forearm.L"].rotation_euler',
            'pose.bones["forearm.R"].rotation_euler',
            'pose.bones["foot.L"].rotation_euler',
            'pose.bones["foot.R"].rotation_euler',
            'pose.bones["cloth.L"].rotation_euler',
            'pose.bones["cloth.C"].rotation_euler',
            'pose.bones["cloth.R"].rotation_euler',
        ):
            self.assertIn(channel, self.builder_source)

    def test_builder_does_not_change_geometry_translate_root_or_mirror(self) -> None:
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("bpy.data.meshes.new", self.builder_source)
        self.assertNotIn('pose.bones["root"].location', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)
        self.assertIn('action["mirroring_used"] = False', self.builder_source)

    def test_rear_view_preserves_screen_side_equipment_contract(self) -> None:
        self.assertIn('action["rear_view"] = True', self.builder_source)
        self.assertIn('action["screen_left_physical_side"] = "left"', self.builder_source)
        self.assertIn('action["large_pauldron_screen_left"] = True', self.builder_source)
        self.assertIn('action["scabbard_screen_left"] = True', self.builder_source)
        self.assertIn('action["small_pauldron_screen_right"] = True', self.builder_source)
        self.assertIn('action["pouch_screen_right"] = True', self.builder_source)
        self.assertIn('action["face_visible"] = False', self.builder_source)

    def test_adapter_renders_real_up_rotation_and_six_row_sheet(self) -> None:
        self.assertIn('config.directions[profile.direction]', self.adapter_source)
        self.assertIn('direction=direction', self.adapter_source)
        self.assertIn('rows = 6', self.adapter_source)
        self.assertIn('animation_paths("walk_up")', self.adapter_source)
        self.assertIn('"proxy_walk_up"', self.adapter_source)
        self.assertIn('"walk_up_real_rotation_without_mirroring": True', self.adapter_source)
        self.assertIn('"equipment_sides_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
