from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass17 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FRAME_CANDIDATES,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_RIGHT_ANTICIPATION_DIAGNOSTIC_REVISION,
    TWOHAND_RIGHT_WINDUP_REVISION,
    WINDUP_FRAME,
    WINDUP_SELECTED_ARM_BLEND,
    WINDUP_SELECTED_WEAPON_OFFSET_DEGREES,
    WINDUP_SOURCE_FRAME,
)


class AttackSwordDirectionalCycleV21Pass17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass17.py"
        ).read_text(encoding="utf-8")
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_twohand_right_anticipation_diagnostic_v21.py"
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

    def test_windup_and_anticipation_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass17")
        self.assertEqual(
            TWOHAND_RIGHT_WINDUP_REVISION,
            "twohand_right_windup_arm_rotation_v21_pass17",
        )
        self.assertEqual(
            TWOHAND_RIGHT_ANTICIPATION_DIAGNOSTIC_REVISION,
            "twohand_right_f03_deep_projection_source_search_v21_pass17",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_right_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "right")
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(WINDUP_FRAME, 2)
        self.assertEqual(WINDUP_SOURCE_FRAME, 1)
        self.assertEqual(WINDUP_SELECTED_ARM_BLEND, 0.50)
        self.assertEqual(WINDUP_SELECTED_WEAPON_OFFSET_DEGREES, -72.0)
        self.assertEqual(TARGET_FRAME, 3)
        self.assertEqual(SOURCE_FRAME_CANDIDATES, (2, 4, 1, 5))
        self.assertEqual(ARM_BLEND_CANDIDATES[0], 0.0)
        self.assertEqual(ARM_BLEND_CANDIDATES[-1], 1.0)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES[0], 0.55)
        self.assertEqual(SCREEN_PROJECTION_CANDIDATES[-1], 0.20)
        self.assertLess(max(SCREEN_PROJECTION_CANDIDATES), 0.5767)
        self.assertIn(-88.0, ANGLE_OFFSET_CANDIDATES)
        self.assertIn(88.0, ANGLE_OFFSET_CANDIDATES)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(DIAGNOSTIC_RUN_ID, 30751212090)
        self.assertEqual(DIAGNOSTIC_ARTIFACT_ID, 8834533057)
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX, (32, 19, 74, 92))
        self.assertEqual(
            DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_bakes_only_right_f02_arm_blend(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass15",
            self.builder_source,
        )
        self.assertIn("WINDUP_FRAME", self.builder_source)
        self.assertIn("WINDUP_SOURCE_FRAME", self.builder_source)
        self.assertIn("WINDUP_SELECTED_ARM_BLEND", self.builder_source)
        self.assertIn("target_point.co[1]", self.builder_source)
        self.assertIn(
            'action["directional_twohand_right_windup_revision"]',
            self.builder_source,
        )
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_diagnostic_uses_real_deep_projection_and_multiple_sources(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass17",
            self.diagnostic_source,
        )
        self.assertIn("for source_frame in SOURCE_FRAME_CANDIDATES", self.diagnostic_source)
        self.assertIn("for requested_projection in SCREEN_PROJECTION_CANDIDATES", self.diagnostic_source)
        self.assertIn("_projection_target_direction", self.diagnostic_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.diagnostic_source)
        self.assertIn("pass06_adapter._restore_weapon", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_camera_margin", self.diagnostic_source)
        self.assertIn("_edge_alpha_counts", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_workflow_runs_pass17_and_preserves_full_pass15_history(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_"
            "twohand_right_anticipation_diagnostic_v21.py"
        )
        full = "blender_sprite_factory_attack_sword_directional_cycle_v21_pass15.py"
        self.assertIn(diagnostic, self.workflow_source)
        self.assertIn(full, self.workflow_source)
        self.assertIn(full, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
