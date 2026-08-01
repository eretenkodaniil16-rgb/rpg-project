from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v19_pass02 import (
    CORRECTION_PASS,
    ONEHAND_CONTACT_REVISION,
    ONEHAND_FOLLOW_REVISION,
    load_attack_sword_down_keyposes_profile_v19_pass02,
)


class AttackSwordDownKeyposesV19Pass02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v19_pass02(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass02.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_onehand_low_arc(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v19_pass02")
        self.assertEqual(
            ONEHAND_CONTACT_REVISION,
            "diagonal_down_contact_v19_pass02",
        )
        self.assertEqual(
            ONEHAND_FOLLOW_REVISION,
            "low_follow_without_torso_reversal_v19_pass02",
        )
        onehand = self.profile.grips[0]
        _guard, anticipation, contact, follow, recovery = onehand.poses
        self.assertLess(anticipation.hand_right_z_degrees, contact.hand_right_z_degrees)
        self.assertLess(contact.hand_right_z_degrees, follow.hand_right_z_degrees)
        self.assertLess(contact.upper_arm_right_x_degrees, 0.0)
        self.assertLess(follow.upper_arm_right_x_degrees, contact.upper_arm_right_x_degrees)
        self.assertLess(contact.chest_yaw_z_degrees, 0.0)
        self.assertLess(follow.chest_yaw_z_degrees, 0.0)
        self.assertLessEqual(abs(recovery.hand_right_z_degrees), 8.0)

    def test_twohand_profile_is_unchanged_from_v19(self) -> None:
        from attack_sword_down_keyposes_correction_v19 import (
            load_attack_sword_down_keyposes_profile_v19,
        )

        source = load_attack_sword_down_keyposes_profile_v19(
            "human_warrior_m01"
        )
        self.assertEqual(self.profile.grips[1], source.grips[1])

    def test_adapter_delegates_to_v19_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "load_attack_sword_down_keyposes_profile_v19_pass02",
            self.adapter_source,
        )
        self.assertIn("BASE_WRITE_MANIFEST_V19", self.adapter_source)
        self.assertIn('CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"', self.adapter_source)
        self.assertIn('"twohand_v19_trajectory_unchanged": True', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertNotIn("factory._new_action", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
