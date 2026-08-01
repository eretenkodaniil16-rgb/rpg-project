from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v18 import (
    CORRECTION_REVISION,
    ONEHAND_TRAJECTORY_REVISION,
    TWOHAND_ANTICIPATION_REVISION,
    load_attack_sword_down_keyposes_profile_v18,
)


class AttackSwordDownKeyposesV18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v18(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v18.py"
        ).read_text(encoding="utf-8")

    def test_correction_identity_and_sources(self) -> None:
        self.assertEqual(CORRECTION_REVISION, "v18")
        self.assertEqual(
            ONEHAND_TRAJECTORY_REVISION,
            "high_windup_to_low_follow_v18",
        )
        self.assertEqual(
            TWOHAND_ANTICIPATION_REVISION,
            "contained_high_guard_v18",
        )
        self.assertEqual(self.profile.appearance_revision, "v03")
        self.assertEqual(self.profile.head_revision, "v22")
        self.assertEqual(self.profile.proxy_revision, "v25")

    def test_onehand_visual_phase_order_is_high_to_low(self) -> None:
        onehand = self.profile.grips[0]
        guard, anticipation, contact, follow, recovery = onehand.poses
        self.assertEqual(
            tuple(pose.phase for pose in onehand.poses),
            ("guard", "anticipation", "contact", "follow_through", "recovery"),
        )
        self.assertLess(anticipation.hand_right_z_degrees, -50.0)
        self.assertGreater(contact.hand_right_z_degrees, anticipation.hand_right_z_degrees)
        self.assertGreater(follow.hand_right_z_degrees, 20.0)
        self.assertLess(abs(recovery.hand_right_z_degrees), 12.0)
        self.assertEqual(guard.frame, 1)
        self.assertEqual(recovery.frame, 5)

    def test_twohand_anticipation_stays_contained_and_symmetric(self) -> None:
        twohand = self.profile.grips[1]
        anticipation = twohand.poses[1]
        self.assertEqual(anticipation.upper_arm_left_x_degrees, -10.0)
        self.assertEqual(
            anticipation.upper_arm_left_x_degrees,
            anticipation.upper_arm_right_x_degrees,
        )
        self.assertEqual(
            anticipation.forearm_left_x_degrees,
            anticipation.forearm_right_x_degrees,
        )
        self.assertEqual(
            anticipation.hand_left_x_degrees,
            anticipation.hand_right_x_degrees,
        )
        self.assertGreaterEqual(anticipation.hand_left_x_degrees, -12.0)

    def test_v18_adapter_patches_only_profile_and_manifest(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "action_builder.load_attack_sword_down_keyposes_profile_v17",
            self.adapter_source,
        )
        self.assertIn(
            "previous_adapter.load_attack_sword_down_keyposes_profile_v17",
            self.adapter_source,
        )
        self.assertIn(
            "BASE_WRITE_MANIFEST_V17 = previous_adapter._write_manifest_v17",
            self.adapter_source,
        )
        self.assertIn(
            'CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v18.png"',
            self.adapter_source,
        )
        self.assertIn('"source_v17_preserved": True', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertNotIn("factory._new_action", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
