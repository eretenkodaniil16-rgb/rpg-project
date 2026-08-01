from __future__ import annotations

import ast
import unittest
from dataclasses import fields
from pathlib import Path

from attack_sword_down_keyposes_correction_v19_pass03 import (
    load_attack_sword_down_keyposes_profile_v19_pass03,
)
from attack_sword_down_keyposes_correction_v19_pass05 import (
    AttackSwordDownPoseDeltaV19,
    CORRECTION_PASS,
    DEPTH_ROTATION_DEGREES,
    TWOHAND_ANTICIPATION_REVISION,
    load_attack_sword_down_keyposes_profile_v19_pass05,
)
from attack_sword_down_keyposes_profile_v17 import AttackSwordDownPoseDeltaV17


class AttackSwordDownKeyposesV19Pass05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_keyposes_profile_v19_pass05(
            "human_warrior_m01"
        )
        cls.previous = load_attack_sword_down_keyposes_profile_v19_pass03(
            "human_warrior_m01"
        )
        cls.builder_source = (
            cls.tool_root / "attack_sword_down_keyposes_builder_v17.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass05.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_depth_pose(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v19_pass05")
        self.assertEqual(
            TWOHAND_ANTICIPATION_REVISION,
            "foreshortened_depth_windup_v19_pass05",
        )
        self.assertEqual(DEPTH_ROTATION_DEGREES, 46.0)
        anticipation = self.profile.grips[1].poses[1]
        self.assertIsInstance(anticipation, AttackSwordDownPoseDeltaV19)
        self.assertEqual(anticipation.upper_arm_left_y_degrees, 6.0)
        self.assertEqual(anticipation.upper_arm_right_y_degrees, 6.0)
        self.assertEqual(anticipation.forearm_left_y_degrees, 14.0)
        self.assertEqual(anticipation.forearm_right_y_degrees, 14.0)
        self.assertEqual(anticipation.hand_left_y_degrees, DEPTH_ROTATION_DEGREES)
        self.assertEqual(anticipation.hand_right_y_degrees, DEPTH_ROTATION_DEGREES)

    def test_only_depth_fields_changed_from_pass03(self) -> None:
        current = self.profile.grips[1].poses[1]
        previous = self.previous.grips[1].poses[1]
        for field in fields(AttackSwordDownPoseDeltaV17):
            self.assertEqual(
                getattr(current, field.name),
                getattr(previous, field.name),
                field.name,
            )
        self.assertEqual(self.profile.grips[0], self.previous.grips[0])
        self.assertEqual(self.profile.grips[1].poses[0], self.previous.grips[1].poses[0])
        self.assertEqual(self.profile.grips[1].poses[2:], self.previous.grips[1].poses[2:])

    def test_builder_supports_optional_y_rotation_without_changing_old_poses(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn('getattr(pose, attribute, 0.0)', self.builder_source)
        for attribute in (
            "upper_arm_left_y_degrees",
            "forearm_left_y_degrees",
            "hand_left_y_degrees",
            "upper_arm_right_y_degrees",
            "forearm_right_y_degrees",
            "hand_right_y_degrees",
        ):
            self.assertIn(f'"{attribute}"', self.builder_source)
        self.assertGreaterEqual(self.builder_source.count("1: _degree_pairs("), 6)

    def test_adapter_preserves_clearance_and_locked_contracts(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "load_attack_sword_down_keyposes_profile_v19_pass05",
            self.adapter_source,
        )
        self.assertIn("BASE_WRITE_MANIFEST_PASS03", self.adapter_source)
        self.assertIn('CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"', self.adapter_source)
        self.assertIn('"onehand_v19_pass03_unchanged": True', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertNotIn("factory._new_action", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
