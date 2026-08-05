from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass20 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_UP_TAIL_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
)


class AttackSwordDirectionalCycleV21Pass20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_onehand_up_tail_diagnostic_v21.py"
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

    def test_onehand_up_tail_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass20")
        self.assertEqual(
            ONEHAND_UP_TAIL_DIAGNOSTIC_REVISION,
            "onehand_up_f05_f08_sequential_projection_v21_pass20",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_onehand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "onehand_ready")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAMES, (5, 6, 7, 8))
        self.assertEqual(SOURCE_FRAME_BY_TARGET, {5: 4, 6: 5, 7: 8, 8: 1})
        self.assertEqual(
            TARGET_BONES,
            ("upper_arm.R", "forearm.R", "hand.R"),
        )
        self.assertEqual(ARM_BLEND_CANDIDATES[0], 0.0)
        self.assertEqual(ARM_BLEND_CANDIDATES[-1], 1.0)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES[0], 0.95)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES[-1], 0.18)
        self.assertIn(-90.0, ANGLE_OFFSET_CANDIDATES)
        self.assertIn(90.0, ANGLE_OFFSET_CANDIDATES)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 1.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30752258967)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8835097632)

    def test_diagnostic_uses_sequential_selected_onehand_poses(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass19",
            self.diagnostic_source,
        )
        self.assertIn("selected_pose_by_frame", self.diagnostic_source)
        self.assertIn("for target_frame in TARGET_FRAMES", self.diagnostic_source)
        self.assertIn("_projection_target_direction", self.diagnostic_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.diagnostic_source)
        self.assertIn("pass06_adapter._restore_weapon", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_camera_margin", self.diagnostic_source)
        self.assertIn("_edge_alpha_counts", self.diagnostic_source)
        self.assertIn("_write_four_frame_sheet", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_workflow_runs_pass20_and_preserves_full_pass19(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_tail_diagnostic_v21.py"
        )
        full = "blender_sprite_factory_attack_sword_directional_cycle_v21_pass19.py"
        self.assertIn(diagnostic, self.workflow_source)
        self.assertIn(full, self.workflow_source)
        self.assertIn(full, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
