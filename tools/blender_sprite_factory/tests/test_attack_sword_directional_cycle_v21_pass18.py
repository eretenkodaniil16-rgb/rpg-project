from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass18 import (
    ANGLE_OFFSET_CANDIDATES,
    ANTICIPATION_DIAGNOSTIC_ALPHA_BBOX,
    ANTICIPATION_DIAGNOSTIC_ARTIFACT_ID,
    ANTICIPATION_DIAGNOSTIC_FRAME_SIZE,
    ANTICIPATION_DIAGNOSTIC_RUN_ID,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    EARLY_SELECTED_ARM_BLEND_BY_FRAME,
    EARLY_SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME,
    EARLY_SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
    EARLY_SOURCE_FRAME_BY_TARGET,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_RIGHT_EARLY_REVISION,
    TWOHAND_RIGHT_TAIL_DIAGNOSTIC_REVISION,
    WINDUP_DIAGNOSTIC_ALPHA_BBOX,
    WINDUP_DIAGNOSTIC_ARTIFACT_ID,
    WINDUP_DIAGNOSTIC_FRAME_SIZE,
    WINDUP_DIAGNOSTIC_RUN_ID,
)


class AttackSwordDirectionalCycleV21Pass18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass18.py"
        ).read_text(encoding="utf-8")
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_twohand_right_tail_diagnostic_v21.py"
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

    def test_early_pose_and_tail_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass18")
        self.assertEqual(
            TWOHAND_RIGHT_EARLY_REVISION,
            "twohand_right_f02_f03_action_projection_v21_pass18",
        )
        self.assertEqual(
            TWOHAND_RIGHT_TAIL_DIAGNOSTIC_REVISION,
            "twohand_right_f04_f08_sequential_projection_v21_pass18",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_right_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "right")
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(EARLY_SOURCE_FRAME_BY_TARGET, {2: 1, 3: 1})
        self.assertEqual(EARLY_SELECTED_ARM_BLEND_BY_FRAME, {2: 0.50, 3: 1.00})
        self.assertEqual(
            EARLY_SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME,
            {2: 0.95, 3: 0.55},
        )
        self.assertEqual(
            EARLY_SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
            {2: -72.0, 3: -48.0},
        )
        self.assertEqual(TARGET_FRAMES, (4, 5, 6, 7, 8))
        self.assertEqual(
            SOURCE_FRAME_BY_TARGET,
            {4: 3, 5: 4, 6: 5, 7: 8, 8: 1},
        )
        self.assertEqual(ARM_BLEND_CANDIDATES[0], 0.0)
        self.assertEqual(ARM_BLEND_CANDIDATES[-1], 1.0)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES[0], 0.95)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES[-1], 0.18)
        self.assertIn(-88.0, ANGLE_OFFSET_CANDIDATES)
        self.assertIn(88.0, ANGLE_OFFSET_CANDIDATES)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME[4], 4.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME[8], 1.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)

    def test_source_diagnostics_are_locked(self) -> None:
        self.assertEqual(WINDUP_DIAGNOSTIC_RUN_ID, 30751212090)
        self.assertEqual(WINDUP_DIAGNOSTIC_ARTIFACT_ID, 8834533057)
        self.assertEqual(WINDUP_DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(WINDUP_DIAGNOSTIC_ALPHA_BBOX, (32, 19, 74, 92))
        self.assertEqual(ANTICIPATION_DIAGNOSTIC_RUN_ID, 30751575069)
        self.assertEqual(ANTICIPATION_DIAGNOSTIC_ARTIFACT_ID, 8834650938)
        self.assertEqual(ANTICIPATION_DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(ANTICIPATION_DIAGNOSTIC_ALPHA_BBOX, (31, 21, 73, 92))
        self.assertEqual(
            DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_bakes_only_right_f02_f03_arm_poses(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass15",
            self.builder_source,
        )
        self.assertIn("EARLY_SOURCE_FRAME_BY_TARGET.items()", self.builder_source)
        self.assertIn("EARLY_SELECTED_ARM_BLEND_BY_FRAME", self.builder_source)
        self.assertIn("target_point.co[1]", self.builder_source)
        self.assertIn(
            'action["directional_twohand_right_early_revision"]',
            self.builder_source,
        )
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_tail_diagnostic_uses_sequential_selected_poses(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass18",
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
        self.assertIn("_write_five_frame_sheet", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_workflow_runs_tail_diagnostic_and_preserves_full_pass15(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_"
            "twohand_right_tail_diagnostic_v21.py"
        )
        full = "blender_sprite_factory_attack_sword_directional_cycle_v21_pass15.py"
        self.assertIn(diagnostic, self.workflow_source)
        self.assertIn(full, self.workflow_source)
        self.assertIn(full, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
