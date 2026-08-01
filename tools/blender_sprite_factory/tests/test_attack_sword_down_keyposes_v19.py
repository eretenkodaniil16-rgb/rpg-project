from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v19 import (
    CORRECTION_REVISION,
    MIN_TWOHAND_HEAD_CLEARANCE_PIXELS,
    ONEHAND_TRAJECTORY_REVISION,
    TWOHAND_TRAJECTORY_REVISION,
    load_attack_sword_down_keyposes_profile_v19,
)


class AttackSwordDownKeyposesV19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v19(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_locked_sources(self) -> None:
        self.assertEqual(CORRECTION_REVISION, "v19")
        self.assertEqual(
            ONEHAND_TRAJECTORY_REVISION,
            "continuous_diagonal_cut_v19",
        )
        self.assertEqual(
            TWOHAND_TRAJECTORY_REVISION,
            "outside_head_descending_arc_v19",
        )
        self.assertEqual(MIN_TWOHAND_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertEqual(self.profile.appearance_revision, "v03")
        self.assertEqual(self.profile.head_revision, "v22")
        self.assertEqual(self.profile.proxy_revision, "v25")
        self.assertEqual(self.profile.direction, "down")
        self.assertEqual(self.profile.frame_order, (1, 2, 3, 4, 5))

    def test_guard_frames_remain_exactly_approved(self) -> None:
        for grip in self.profile.grips:
            guard = grip.poses[0]
            self.assertEqual(guard.phase, "guard")
            self.assertEqual(guard.pelvis_x, 0.0)
            self.assertEqual(guard.pelvis_z, 0.0)
            self.assertTrue(all(value == 0.0 for value in guard.rotation_deltas()))

    def test_onehand_arc_is_continuous_and_torso_does_not_reverse(self) -> None:
        onehand = self.profile.grips[0]
        _guard, anticipation, contact, follow, recovery = onehand.poses
        self.assertLess(
            anticipation.hand_right_z_degrees,
            contact.hand_right_z_degrees,
        )
        self.assertLess(
            contact.hand_right_z_degrees,
            follow.hand_right_z_degrees,
        )
        self.assertLess(anticipation.hand_right_z_degrees, -35.0)
        self.assertGreater(follow.hand_right_z_degrees, 25.0)
        self.assertLess(contact.chest_yaw_z_degrees, 0.0)
        self.assertLess(follow.chest_yaw_z_degrees, 0.0)
        self.assertLessEqual(abs(recovery.hand_right_z_degrees), 8.0)

    def test_twohand_arc_stays_outside_head_until_contact(self) -> None:
        twohand = self.profile.grips[1]
        _guard, anticipation, contact, follow, _recovery = twohand.poses
        self.assertLess(anticipation.hand_right_z_degrees, -12.0)
        self.assertLessEqual(contact.hand_right_z_degrees, 4.0)
        self.assertGreater(
            follow.hand_right_z_degrees,
            contact.hand_right_z_degrees,
        )
        self.assertLess(anticipation.chest_yaw_z_degrees * anticipation.head_yaw_z_degrees, 0.0)
        self.assertEqual(anticipation.upper_arm_left_x_degrees, anticipation.upper_arm_right_x_degrees)
        self.assertEqual(contact.upper_arm_left_x_degrees, contact.upper_arm_right_x_degrees)

    def test_adapter_adds_projected_head_clearance_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("world_to_camera_view", self.adapter_source)
        self.assertIn("_twohand_head_clearance_pixels", self.adapter_source)
        self.assertIn("CLEARANCE_FRAMES = (2, 3)", self.adapter_source)
        self.assertIn("MIN_TWOHAND_HEAD_CLEARANCE_PIXELS", self.adapter_source)
        self.assertIn("combat_twohand_high_v06_blade", self.adapter_source)
        self.assertIn('CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("negative_scale", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
