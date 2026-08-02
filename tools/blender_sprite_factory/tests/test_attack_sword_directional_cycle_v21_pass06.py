from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass06 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_CLEARANCE_REVISION,
)


class AttackSwordDirectionalCycleV21Pass06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_twohand_left_windup_diagnostic_v21.py"
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

    def test_diagnostic_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass06")
        self.assertEqual(
            TWOHAND_LEFT_CLEARANCE_REVISION,
            "twohand_left_windup_extended_rigid_arc_v21_pass06",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 2)
        self.assertEqual(ANGLE_SEARCH_LIMIT_DEGREES, 90)
        self.assertEqual(ANGLE_SEARCH_STEP_DEGREES, 2)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30743036073)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8832083387)

    def test_diagnostic_uses_rigid_weapon_only_and_export_checks(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass05",
            self.diagnostic_source,
        )
        self.assertIn("pass07_adapter._apply_world_rotation", self.diagnostic_source)
        self.assertIn("pass06_adapter._restore_weapon", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_camera_margin", self.diagnostic_source)
        self.assertIn("_edge_alpha_counts", self.diagnostic_source)
        self.assertIn("_render_candidate", self.diagnostic_source)
        self.assertNotIn("pose.bones", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_workflow_runs_diagnostic_and_launcher_keeps_full_pass05(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_twohand_left_windup_diagnostic_v21.py"
        )
        full = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass05.py"
        )
        self.assertIn(diagnostic, self.workflow_source)
        self.assertIn(full, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
