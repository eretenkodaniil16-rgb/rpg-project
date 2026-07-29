from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_profile_v01 import load_combat_idle_down_profile_v01


class CombatIdleDownProfileV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_down_profile_v01("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_animation_builder_v01.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_combat_idle_down_v01.py"
        ).read_text(encoding="utf-8")

    def test_revision_and_static_pose_contract(self) -> None:
        self.assertEqual(self.profile.revision, "v01")
        self.assertEqual(self.profile.pose_revision, "v01")
        self.assertEqual(self.profile.animation_id, "combat_idle")
        self.assertEqual(self.profile.direction, "down")
        self.assertEqual(self.profile.fps, 1)
        self.assertFalse(self.profile.loop)
        self.profile.assert_valid()

    def test_sword_and_stance_use_physical_sides(self) -> None:
        self.assertEqual(self.profile.weapon_id, "sword_01")
        self.assertEqual(self.profile.weapon_hand, "right")
        self.assertGreater(self.profile.pose.thigh_left_z_degrees, 0.0)
        self.assertLess(self.profile.pose.thigh_right_z_degrees, 0.0)
        self.assertLess(self.profile.pose.pelvis_z, 0.0)

    def test_pose_keeps_large_left_pauldron_motion_restrained(self) -> None:
        self.assertLessEqual(abs(self.profile.pose.upper_arm_left_x_degrees), 18.0)
        self.assertGreater(
            abs(self.profile.pose.upper_arm_right_x_degrees),
            abs(self.profile.pose.upper_arm_left_x_degrees),
        )
        self.assertLess(self.profile.pose.forearm_right_x_degrees, -20.0)

    def test_builder_adds_drawn_sword_without_replacing_walk_actions(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "approved_walk_builder.create_walk_up_actions_v02(context)",
            self.builder_source,
        )
        self.assertIn('"combat_weapon"', self.builder_source)
        self.assertIn('"hand.R"', self.builder_source)
        self.assertIn('"combat_sword_blade"', self.builder_source)
        self.assertIn('action["weapon_hand"] = profile.weapon_hand', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_preserves_sheathed_scabbard_and_toggles_only_hilt(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("render_pilot_combat_idle_down_v01", self.adapter_source)
        self.assertIn("_set_combat_weapon_state(False)", self.adapter_source)
        self.assertIn("_set_combat_weapon_state(True)", self.adapter_source)
        self.assertIn("SHEATHED_HILT_OBJECT_NAMES", self.adapter_source)
        self.assertIn(
            '"scabbard_remains_physical_left": True',
            self.adapter_source,
        )
        self.assertIn(
            '"technical_candidate_requires_manual_static_pose_review"',
            self.adapter_source,
        )
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat_idle_down v01 profile"):
            load_combat_idle_down_profile_v01("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
