from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_profile_v17 import (
    ATTACK_KEYPOSE_FRAME_ORDER,
    ATTACK_KEYPOSE_PHASE_ORDER,
    load_attack_sword_down_keyposes_profile_v17,
)


class AttackSwordDownKeyposesV17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v17(
            "human_warrior_m01"
        )
        cls.builder_source = (
            cls.tool_root / "attack_sword_down_keyposes_builder_v17.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v17.py"
        ).read_text(encoding="utf-8")

    def test_profile_identity_and_review_scope(self) -> None:
        self.assertEqual(self.profile.revision, "v17")
        self.assertEqual(self.profile.direction, "down")
        self.assertEqual(self.profile.frame_order, ATTACK_KEYPOSE_FRAME_ORDER)
        self.assertEqual(self.profile.phase_order, ATTACK_KEYPOSE_PHASE_ORDER)
        self.assertEqual(self.profile.fps, 6)
        self.assertFalse(self.profile.loop)
        self.assertEqual(
            tuple(item.grip_id for item in self.profile.grips),
            ("onehand_ready", "twohand_center_high"),
        )
        self.assertEqual(self.profile.appearance_revision, "v03")
        self.assertEqual(self.profile.head_revision, "v22")
        self.assertEqual(self.profile.proxy_revision, "v25")

    def test_guard_pose_is_exact_source_and_trajectories_are_distinct(self) -> None:
        for grip in self.profile.grips:
            guard = grip.poses[0]
            self.assertEqual(guard.phase, "guard")
            self.assertEqual(guard.pelvis_x, 0.0)
            self.assertEqual(guard.pelvis_z, 0.0)
            self.assertTrue(all(value == 0.0 for value in guard.rotation_deltas()))
        onehand, twohand = self.profile.grips
        self.assertEqual(
            onehand.trajectory_id,
            "physical_right_high_to_left_low_diagonal",
        )
        self.assertEqual(
            twohand.trajectory_id,
            "center_high_to_center_low_heavy_descending",
        )
        self.assertNotEqual(onehand.trajectory_id, twohand.trajectory_id)

    def test_onehand_has_clear_windup_contact_and_follow_through(self) -> None:
        onehand = self.profile.grips[0]
        anticipation = onehand.poses[1]
        contact = onehand.poses[2]
        follow = onehand.poses[3]
        self.assertGreater(anticipation.hand_right_z_degrees, 20.0)
        self.assertLess(contact.hand_right_z_degrees, -50.0)
        self.assertLess(follow.hand_right_z_degrees, contact.hand_right_z_degrees)
        self.assertGreater(anticipation.upper_arm_left_z_degrees, 0.0)
        self.assertLess(contact.chest_yaw_z_degrees, -20.0)

    def test_twohand_preserves_paired_arm_timing(self) -> None:
        twohand = self.profile.grips[1]
        for pose in twohand.poses:
            self.assertAlmostEqual(
                pose.upper_arm_left_x_degrees,
                pose.upper_arm_right_x_degrees,
            )
            self.assertAlmostEqual(
                pose.forearm_left_x_degrees,
                pose.forearm_right_x_degrees,
            )
        self.assertLess(twohand.poses[1].upper_arm_right_x_degrees, 0.0)
        self.assertGreater(twohand.poses[2].upper_arm_right_x_degrees, 30.0)
        self.assertGreater(twohand.poses[3].hand_right_x_degrees, 30.0)

    def test_builder_parses_and_reuses_approved_sources(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_combat_idle_directional_cycles_v14(context)",
            self.builder_source,
        )
        self.assertIn(
            "load_weapon_stance_profile_v09",
            self.builder_source,
        )
        self.assertIn('action["root_translation_used"] = False', self.builder_source)
        self.assertIn('action["mirroring_used"] = False', self.builder_source)
        self.assertIn('action["geometry_changed"] = False', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_renders_only_ten_down_keyposes(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "create_attack_sword_down_keypose_actions_v17",
            self.adapter_source,
        )
        self.assertIn("rendered_count != 10", self.adapter_source)
        self.assertIn('weapon_adapter._set_v12_weapon(grip.weapon_cycle_id, "down")', self.adapter_source)
        self.assertIn('CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v17.png"', self.adapter_source)
        self.assertIn('"manual_keypose_review_required": True', self.adapter_source)
        self.assertIn('"full_attack_cycle_not_yet_approved": True', self.adapter_source)
        self.assertNotIn("walk_directional_weapon_render_v16", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
