from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass15 import (
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX_BY_FRAME,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_APPLIED_SCREEN_PROJECTION_BY_FRAME,
    SELECTED_ARM_BLEND_BY_FRAME,
    SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME,
    SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
    SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_TAIL_REVISION,
)


class AttackSwordDirectionalCycleV21Pass15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass15.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass15.py"
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

    def test_selected_tail_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass15")
        self.assertEqual(
            TWOHAND_LEFT_TAIL_REVISION,
            "twohand_left_tail_action_projection_v21_pass15",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAMES, (5, 6, 7, 8))
        self.assertEqual(
            SOURCE_FRAME_BY_TARGET,
            {5: 4, 6: 5, 7: 8, 8: 1},
        )
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(
            SELECTED_ARM_BLEND_BY_FRAME,
            {5: 0.40, 6: 0.0, 7: 0.0, 8: 0.0},
        )
        self.assertEqual(
            SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME,
            {5: 0.95, 6: 0.95, 7: 0.95, 8: 0.95},
        )
        self.assertAlmostEqual(
            SELECTED_APPLIED_SCREEN_PROJECTION_BY_FRAME[5],
            0.95,
        )
        self.assertEqual(
            SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
            {5: -16.0, 6: 0.0, 7: 0.0, 8: 8.0},
        )
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 1.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(DIAGNOSTIC_RUN_ID, 30749917970)
        self.assertEqual(DIAGNOSTIC_ARTIFACT_ID, 8834141095)
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX_BY_FRAME[5], (14, 20, 88, 92))
        for edge_counts in DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME.values():
            self.assertEqual(
                edge_counts,
                {"left": 0, "right": 0, "top": 0, "bottom": 0},
            )

    def test_builder_bakes_only_f05_arm_blend(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass13",
            self.builder_source,
        )
        self.assertIn("for target_frame in TARGET_FRAMES", self.builder_source)
        self.assertIn("math.isclose(blend, 0.0", self.builder_source)
        self.assertIn("target_point.co[1]", self.builder_source)
        self.assertIn(
            'action["directional_twohand_left_tail_revision"]',
            self.builder_source,
        )
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_reproduces_four_rigid_weapon_transforms(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_is_tail_frame", self.adapter_source)
        self.assertIn("_target_direction_v21_pass15", self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon", self.adapter_source)
        self.assertIn("_weapon_head_clearance", self.adapter_source)
        self.assertIn("_camera_margin", self.adapter_source)
        self.assertIn("_edge_alpha_counts", self.adapter_source)
        self.assertIn("_render_candidate", self.adapter_source)
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"right_up_actions_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_active_entrypoints_use_full_pass15(self) -> None:
        active = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass15.py"
        )
        historical = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass13.py"
        )
        self.assertIn(active, self.workflow_source)
        self.assertIn(active, self.launcher_source)
        self.assertIn(historical, self.workflow_source)
        self.assertIn(historical, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
