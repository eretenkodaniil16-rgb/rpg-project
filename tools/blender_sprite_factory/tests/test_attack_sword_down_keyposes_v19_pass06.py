from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v19_pass06 import (
    CORRECTION_PASS,
    TWOHAND_ANTICIPATION_REVISION,
    WEAPON_SCREEN_PROJECTION_MAGNITUDE,
)


class AttackSwordDownKeyposesV19Pass06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass06.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_projection_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v19_pass06")
        self.assertEqual(
            TWOHAND_ANTICIPATION_REVISION,
            "rigid_weapon_depth_projection_v19_pass06",
        )
        self.assertEqual(WEAPON_SCREEN_PROJECTION_MAGNITUDE, 0.82)
        self.assertGreater(WEAPON_SCREEN_PROJECTION_MAGNITUDE, 0.78)
        self.assertLess(WEAPON_SCREEN_PROJECTION_MAGNITUDE, 0.86)

    def test_adapter_rotates_complete_weapon_as_rigid_group(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("TWO_HAND_HIGH_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn("combat_twohand_high_v06_grip", self.adapter_source)
        self.assertIn("Matrix.Translation(pivot)", self.adapter_source)
        self.assertIn("rotation.to_matrix().to_4x4()", self.adapter_source)
        self.assertIn("transform @ obj.matrix_world", self.adapter_source)
        self.assertIn("obj.matrix_basis = matrix_basis", self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)

    def test_adapter_preserves_screen_direction_and_checks_actual_clearance(self) -> None:
        self.assertIn("screen_direction * WEAPON_SCREEN_PROJECTION_MAGNITUDE", self.adapter_source)
        self.assertIn("camera_forward * depth_magnitude", self.adapter_source)
        self.assertIn("_validate_twohand_head_clearance_pass06", self.adapter_source)
        self.assertIn("_apply_rigid_weapon_depth_projection()", self.adapter_source)
        self.assertIn("v19_base._twohand_head_clearance_pixels(context)", self.adapter_source)
        self.assertIn("v19_base.MIN_TWOHAND_HEAD_CLEARANCE_PIXELS", self.adapter_source)
        self.assertIn("CLEARANCE_FRAMES", self.adapter_source)

    def test_adapter_only_targets_twohand_anticipation(self) -> None:
        self.assertIn(
            'TARGET_ANIMATION_ID = "attack_sword_01_twohand_down_keyposes_v17"',
            self.adapter_source,
        )
        self.assertIn("TARGET_FRAME = 2", self.adapter_source)
        self.assertIn('"onehand_v19_pass03_unchanged": True', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
