from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass10 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    F02_REFERENCE_ARM_BLEND,
    F02_REFERENCE_SCREEN_PROJECTION,
    F02_REFERENCE_WEAPON_OFFSET_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FRAME,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_ANTICIPATION_REVISION,
)


class AttackSwordDirectionalCycleV21Pass10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_twohand_left_anticipation_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")
        cls.launcher_source = (
            cls.tool_root / "run_blender_sprite_pilot.ps1"
        ).read_text(encoding="utf-8")

    def test_anticipation_diagnostic_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass10")
        self.assertEqual(
            TWOHAND_LEFT_ANTICIPATION_REVISION,
            "twohand_left_anticipation_from_windup_projection_v21_pass10",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 3)
        self.assertEqual(SOURCE_FRAME, 2)
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(ARM_BLEND_CANDIDATES[0], 0.0)
        self.assertEqual(ARM_BLEND_CANDIDATES[-1], 0.5)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES, (0.82, 0.78, 0.74, 0.70))
        self.assertEqual(ANGLE_OFFSET_CANDIDATES[0], 44.0)
        self.assertEqual(ANGLE_OFFSET_CANDIDATES[-1], 68.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30747420266)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8833482546)
        self.assertEqual(F02_REFERENCE_ARM_BLEND, 0.10)
        self.assertEqual(F02_REFERENCE_SCREEN_PROJECTION, 0.82)
        self.assertEqual(F02_REFERENCE_WEAPON_OFFSET_DEGREES, 54.0)

    def test_diagnostic_blends_from_f03_toward_corrected_f02(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn("SOURCE_FRAME", self.diagnostic_source)
        self.assertIn("TARGET_FRAME", self.diagnostic_source)
        self.assertIn("create_attack_sword_directional_cycle_actions_v21_pass09", self.diagnostic_source)
        self.assertIn("_projection_target_direction", self.diagnostic_source)
        self.assertIn("pass06_adapter._camera_axes", self.diagnostic_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.diagnostic_source)
        self.assertIn("pass06_adapter._restore_weapon", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_edge_alpha_counts", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_pass10_is_preserved_while_pass13_is_active(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_twohand_left_anticipation_diagnostic_v21.py"
        )
        active = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass13.py"
        )
        self.assertTrue((self.tool_root / diagnostic).is_file())
        self.assertIn(active, self.workflow_source)
        self.assertIn(active, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
