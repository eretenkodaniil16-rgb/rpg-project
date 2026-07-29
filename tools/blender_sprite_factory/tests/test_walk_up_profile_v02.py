from __future__ import annotations

import ast
import unittest
from pathlib import Path

from walk_up_profile_v01 import load_walk_up_profile_v01
from walk_up_profile_v02 import load_walk_up_profile_v02


class WalkUpProfileV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v01 = load_walk_up_profile_v01("human_warrior_m01")
        cls.v02 = load_walk_up_profile_v02("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "walk_up_animation_builder_v02.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_walk_up_v02.py"
        ).read_text(encoding="utf-8")

    def test_revision_and_contract(self) -> None:
        self.assertEqual(self.v02.revision, "v02")
        self.assertEqual(self.v02.animation_revision, "v02")
        self.assertEqual(self.v02.animation_id, "walk_up")
        self.assertEqual(self.v02.direction, "up")
        self.v02.assert_valid()

    def test_only_right_passing_pose_changes(self) -> None:
        self.assertEqual(self.v02.poses[:5], self.v01.poses[:5])
        self.assertNotEqual(self.v02.poses[5], self.v01.poses[5])
        self.assertEqual(self.v02.poses[5].phase, "physical_right_passing")

    def test_corrected_leg_keys_and_loop_budget(self) -> None:
        pose = self.v02.poses[5]
        self.assertEqual(
            (
                pose.thigh_left_x_degrees,
                pose.thigh_right_x_degrees,
                pose.shin_left_x_degrees,
                pose.shin_right_x_degrees,
                pose.foot_left_x_degrees,
                pose.foot_right_x_degrees,
            ),
            (10.0, -4.0, 6.0, -4.0, 0.0, 5.0),
        )
        first = self.v02.poses[0].numeric_channels()
        last = pose.numeric_channels()
        self.assertLessEqual(max(abs(end - start) for start, end in zip(first, last)), 10.0)

    def test_builder_and_adapter_are_action_only(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)
        self.assertIn("create_walk_right_actions_v01", self.builder_source)
        self.assertIn('action["rear_passing_silhouette_correction"] = True', self.builder_source)
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("bpy.data.meshes.new", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertIn('"physical_right_passing_leg_keys_only"', self.adapter_source)
        self.assertIn('"walk_up_v01_rejected": True', self.adapter_source)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_up v02 profile"):
            load_walk_up_profile_v02("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
