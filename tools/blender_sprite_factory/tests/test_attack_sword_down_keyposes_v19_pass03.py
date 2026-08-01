from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v19_pass02 import (
    load_attack_sword_down_keyposes_profile_v19_pass02,
)
from attack_sword_down_keyposes_correction_v19_pass03 import (
    CORRECTION_PASS,
    ONEHAND_FOLLOW_CONTAINMENT_REVISION,
    load_attack_sword_down_keyposes_profile_v19_pass03,
)


class AttackSwordDownKeyposesV19Pass03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v19_pass03(
            "human_warrior_m01"
        )
        cls.previous = load_attack_sword_down_keyposes_profile_v19_pass02(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass03.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_cross_body_follow(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v19_pass03")
        self.assertEqual(
            ONEHAND_FOLLOW_CONTAINMENT_REVISION,
            "cross_body_low_follow_v19_pass03",
        )
        onehand = self.profile.grips[0]
        follow = onehand.poses[3]
        previous_follow = self.previous.grips[0].poses[3]
        self.assertEqual(follow.pelvis_x, 0.02)
        self.assertEqual(follow.chest_yaw_z_degrees, 20.0)
        self.assertEqual(follow.hand_right_z_degrees, 28.0)
        self.assertEqual(follow.hand_right_x_degrees, -16.0)
        self.assertNotEqual(follow, previous_follow)
        self.assertGreater(follow.chest_yaw_z_degrees, 0.0)
        self.assertLess(follow.upper_arm_right_x_degrees, 0.0)

    def test_only_onehand_follow_changed_from_pass02(self) -> None:
        current_onehand = self.profile.grips[0]
        previous_onehand = self.previous.grips[0]
        self.assertEqual(current_onehand.poses[:3], previous_onehand.poses[:3])
        self.assertNotEqual(current_onehand.poses[3], previous_onehand.poses[3])
        self.assertEqual(current_onehand.poses[4], previous_onehand.poses[4])
        self.assertEqual(self.profile.grips[1], self.previous.grips[1])

    def test_arc_and_locked_contracts_remain_valid(self) -> None:
        onehand = self.profile.grips[0]
        guard, anticipation, contact, follow, recovery = onehand.poses
        self.assertTrue(all(value == 0.0 for value in guard.rotation_deltas()))
        self.assertLess(anticipation.hand_right_z_degrees, contact.hand_right_z_degrees)
        self.assertLess(contact.hand_right_z_degrees, follow.hand_right_z_degrees)
        self.assertLess(contact.chest_yaw_z_degrees, 0.0)
        self.assertGreater(follow.chest_yaw_z_degrees, 0.0)
        self.assertLessEqual(abs(recovery.hand_right_z_degrees), 8.0)

    def test_adapter_delegates_to_pass02_and_preserves_twohand(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "load_attack_sword_down_keyposes_profile_v19_pass03",
            self.adapter_source,
        )
        self.assertIn("BASE_WRITE_MANIFEST_PASS02", self.adapter_source)
        self.assertIn('CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"', self.adapter_source)
        self.assertIn('"onehand_frames_01_to_03_unchanged_from_pass02": True', self.adapter_source)
        self.assertIn('"twohand_v19_trajectory_unchanged": True', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertNotIn("factory._new_action", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
