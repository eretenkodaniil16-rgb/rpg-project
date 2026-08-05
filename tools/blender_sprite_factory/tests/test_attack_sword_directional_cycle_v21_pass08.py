from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass08 import (
    ANGLE_OFFSET_CANDIDATES,
    APPROVED_DOWN_PROJECTION_REFERENCE,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_PROJECTION_REVISION,
)


class AttackSwordDirectionalCycleV21Pass08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_twohand_left_projection_diagnostic_v21.py"
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

    def test_projection_diagnostic_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass08")
        self.assertEqual(
            TWOHAND_LEFT_PROJECTION_REVISION,
            "twohand_left_windup_projection_planner_v21_pass08",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 2)
        self.assertEqual(GUARD_FRAME, 1)
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(ARM_BLEND_CANDIDATES[0], 0.10)
        self.assertEqual(
            SCREEN_PROJECTION_CANDIDATES,
            (0.82, 0.78, 0.74, 0.70, 0.68),
        )
        self.assertEqual(
            ANGLE_OFFSET_CANDIDATES,
            (46.0, 50.0, 54.0, 58.0, 62.0),
        )
        self.assertEqual(APPROVED_DOWN_PROJECTION_REFERENCE, 0.74)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30744357391)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8832432523)

    def test_diagnostic_uses_rigid_projection_without_geometry_changes(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn("_projection_target_direction", self.diagnostic_source)
        self.assertIn("pass06_adapter._camera_axes", self.diagnostic_source)
        self.assertIn("SCREEN_PROJECTION_CANDIDATES", self.diagnostic_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.diagnostic_source)
        self.assertIn("pass06_adapter._restore_weapon", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_edge_alpha_counts", self.diagnostic_source)
        self.assertIn("_render_candidate", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_pass08_is_preserved_while_pass13_is_active(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_twohand_left_projection_diagnostic_v21.py"
        )
        active = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass13.py"
        )
        self.assertTrue((self.tool_root / diagnostic).is_file())
        self.assertIn(active, self.workflow_source)
        self.assertIn(active, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
