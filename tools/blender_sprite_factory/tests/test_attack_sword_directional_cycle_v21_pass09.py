from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass09 import (
    APPROVED_DOWN_PROJECTION_REFERENCE,
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_ARM_BLEND,
    SELECTED_CAMERA_MARGIN_PIXELS,
    SELECTED_HEAD_CLEARANCE_PIXELS,
    SELECTED_SCREEN_PROJECTION,
    SELECTED_WEAPON_OFFSET_DEGREES,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_WINDUP_REVISION,
)


class AttackSwordDirectionalCycleV21Pass09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass09.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
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

    def test_selected_projection_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass09")
        self.assertEqual(
            TWOHAND_LEFT_WINDUP_REVISION,
            "twohand_left_windup_arm_projection_v21_pass09",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 2)
        self.assertEqual(GUARD_FRAME, 1)
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(SELECTED_ARM_BLEND, 0.10)
        self.assertEqual(SELECTED_SCREEN_PROJECTION, 0.82)
        self.assertEqual(SELECTED_WEAPON_OFFSET_DEGREES, 54.0)
        self.assertGreaterEqual(
            SELECTED_HEAD_CLEARANCE_PIXELS,
            MIN_HEAD_CLEARANCE_PIXELS,
        )
        self.assertGreaterEqual(
            SELECTED_CAMERA_MARGIN_PIXELS,
            MIN_CAMERA_MARGIN_PIXELS,
        )
        self.assertEqual(APPROVED_DOWN_PROJECTION_REFERENCE, 0.74)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(DIAGNOSTIC_RUN_ID, 30747037081)
        self.assertEqual(DIAGNOSTIC_ARTIFACT_ID, 8833238034)
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX, (4, 2, 64, 92))
        self.assertEqual(
            DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_bakes_only_twohand_left_f02_arm_blend(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass05",
            self.builder_source,
        )
        self.assertIn("TARGET_BONES", self.builder_source)
        self.assertIn("TARGET_FRAME", self.builder_source)
        self.assertIn("GUARD_FRAME", self.builder_source)
        self.assertIn("_shortest_angle_delta", self.builder_source)
        self.assertIn("directional_twohand_left_windup_arm_blend", self.builder_source)
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_uses_rigid_projection_and_export_checks(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_target_direction_v21_pass09", self.adapter_source)
        self.assertIn("pass06_adapter._camera_axes", self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon", self.adapter_source)
        self.assertIn("SELECTED_SCREEN_PROJECTION", self.adapter_source)
        self.assertIn("_weapon_head_clearance", self.adapter_source)
        self.assertIn("_camera_margin", self.adapter_source)
        self.assertIn("_edge_alpha_counts", self.adapter_source)
        self.assertIn("_render_candidate", self.adapter_source)
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"onehand_left_pass05_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_active_entrypoints_use_full_pass09(self) -> None:
        target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
        )
        self.assertIn(target, self.workflow_source)
        self.assertIn(target, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
