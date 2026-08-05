from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v19_pass03 import (
    load_attack_sword_down_keyposes_profile_v19_pass03,
)
from attack_sword_down_keyposes_correction_v19_pass04 import (
    CORRECTION_PASS,
    TWOHAND_ANTICIPATION_REVISION,
    load_attack_sword_down_keyposes_profile_v19_pass04,
)


class AttackSwordDownKeyposesV19Pass04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v19_pass04(
            "human_warrior_m01"
        )
        cls.previous = load_attack_sword_down_keyposes_profile_v19_pass03(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass04.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_raised_windup(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v19_pass04")
        self.assertEqual(
            TWOHAND_ANTICIPATION_REVISION,
            "raised_outside_head_windup_v19_pass04",
        )
        anticipation = self.profile.grips[1].poses[1]
        previous = self.previous.grips[1].poses[1]
        self.assertEqual(anticipation.upper_arm_left_x_degrees, -14.0)
        self.assertEqual(anticipation.upper_arm_right_x_degrees, -14.0)
        self.assertEqual(anticipation.forearm_left_x_degrees, -12.0)
        self.assertEqual(anticipation.forearm_right_x_degrees, -12.0)
        self.assertEqual(anticipation.hand_right_z_degrees, -18.0)
        self.assertLess(
            anticipation.upper_arm_right_x_degrees,
            previous.upper_arm_right_x_degrees,
        )
        self.assertLess(anticipation.hand_right_z_degrees, -12.0)

    def test_only_twohand_anticipation_changed(self) -> None:
        self.assertEqual(self.profile.grips[0], self.previous.grips[0])
        current_twohand = self.profile.grips[1]
        previous_twohand = self.previous.grips[1]
        self.assertEqual(current_twohand.poses[0], previous_twohand.poses[0])
        self.assertNotEqual(current_twohand.poses[1], previous_twohand.poses[1])
        self.assertEqual(current_twohand.poses[2:], previous_twohand.poses[2:])

    def test_adapter_preserves_v19_clearance_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "load_attack_sword_down_keyposes_profile_v19_pass04",
            self.adapter_source,
        )
        self.assertIn("BASE_WRITE_MANIFEST_PASS03", self.adapter_source)
        self.assertIn('CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"', self.adapter_source)
        self.assertIn('"onehand_v19_pass03_unchanged": True', self.adapter_source)
        self.assertIn('"twohand_frames_01_and_03_to_05_unchanged": True', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertNotIn("factory._new_action", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
