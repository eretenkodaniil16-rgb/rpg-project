from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass19 import (
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX_BY_FRAME,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME,
    DIAGNOSTIC_FRAME_SIZE,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME,
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
    TWOHAND_RIGHT_FULL_REVISION,
)


class AttackSwordDirectionalCycleV21Pass19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass19.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass19.py"
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

    def test_complete_right_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass19")
        self.assertEqual(
            TWOHAND_RIGHT_FULL_REVISION,
            "twohand_right_full_action_projection_v21_pass19",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_right_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "right")
        self.assertEqual(TARGET_FRAMES, (2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(
            SOURCE_FRAME_BY_TARGET,
            {2: 1, 3: 1, 4: 3, 5: 4, 6: 5, 7: 8, 8: 1},
        )
        self.assertEqual(
            SELECTED_ARM_BLEND_BY_FRAME,
            {2: 0.50, 3: 1.00, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0},
        )
        self.assertEqual(
            SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME[3],
            0.55,
        )
        self.assertAlmostEqual(
            SELECTED_APPLIED_SCREEN_PROJECTION_BY_FRAME[5],
            0.7706997905240274,
        )
        self.assertEqual(
            SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
            {2: -72.0, 3: -48.0, 4: -8.0, 5: 0.0, 6: 0.0, 7: -8.0, 8: -8.0},
        )
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME[2], 4.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME[8], 1.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX_BY_FRAME[7], (28, 3, 78, 92))
        for edge_counts in DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME.values():
            self.assertEqual(
                edge_counts,
                {"left": 0, "right": 0, "top": 0, "bottom": 0},
            )

    def test_builder_wraps_pass18_without_new_pose_changes(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass18",
            self.builder_source,
        )
        self.assertIn(
            'action["directional_twohand_right_full_revision"]',
            self.builder_source,
        )
        self.assertIn(
            'action["directional_twohand_right_action_changed_frames"] = "2,3"',
            self.builder_source,
        )
        self.assertNotIn("target_point.co[1]", self.builder_source)
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_reproduces_right_export_transforms(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_is_target_frame", self.adapter_source)
        self.assertIn("_target_direction_v21_pass19", self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon", self.adapter_source)
        self.assertIn("_weapon_head_clearance", self.adapter_source)
        self.assertIn("_camera_margin", self.adapter_source)
        self.assertIn("_edge_alpha_counts", self.adapter_source)
        self.assertIn("_render_candidate", self.adapter_source)
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"left_direction_changed": False', self.adapter_source)
        self.assertIn('"up_actions_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_active_entrypoints_use_full_pass19(self) -> None:
        active = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass19.py"
        )
        historical = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass15.py"
        )
        self.assertIn(active, self.workflow_source)
        self.assertIn(active, self.launcher_source)
        self.assertIn(historical, self.workflow_source)
        self.assertIn(historical, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
