from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass05 import (
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    RECOVERY_CLEARANCE_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_ARM_BLEND,
    SELECTED_CAMERA_MARGIN_PIXELS,
    SELECTED_HEAD_CLEARANCE_PIXELS,
    SELECTED_WEAPON_OFFSET_DEGREES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


class AttackSwordDirectionalCycleV21Pass05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root
            / "attack_sword_directional_cycle_builder_v21_pass05.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass05.py"
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

    def test_recovery_correction_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass05")
        self.assertEqual(
            RECOVERY_CLEARANCE_REVISION,
            "left_onehand_recovery_arm_weapon_v21_pass05",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_onehand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "onehand_ready")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 7)
        self.assertEqual(GUARD_FRAME, 8)
        self.assertEqual(TARGET_BONES, ("upper_arm.R", "forearm.R", "hand.R"))
        self.assertEqual(SELECTED_ARM_BLEND, 0.10)
        self.assertEqual(SELECTED_WEAPON_OFFSET_DEGREES, -44.0)
        self.assertGreaterEqual(
            SELECTED_HEAD_CLEARANCE_PIXELS,
            MIN_HEAD_CLEARANCE_PIXELS,
        )
        self.assertGreaterEqual(
            SELECTED_CAMERA_MARGIN_PIXELS,
            MIN_CAMERA_MARGIN_PIXELS,
        )
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30741831909)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8831682378)
        self.assertEqual(DIAGNOSTIC_RUN_ID, 30742776923)
        self.assertEqual(DIAGNOSTIC_ARTIFACT_ID, 8831875225)
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX, (30, 18, 66, 92))
        self.assertEqual(
            DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_bakes_only_target_recovery_arm_blend(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass04",
            self.builder_source,
        )
        self.assertIn("TARGET_BONES", self.builder_source)
        self.assertIn("TARGET_FRAME", self.builder_source)
        self.assertIn("GUARD_FRAME", self.builder_source)
        self.assertIn("_shortest_angle_delta", self.builder_source)
        self.assertIn("directional_recovery_arm_blend", self.builder_source)
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_applies_rigid_weapon_offset_and_export_checks(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon", self.adapter_source)
        self.assertIn("SELECTED_WEAPON_OFFSET_DEGREES", self.adapter_source)
        self.assertIn("_weapon_head_clearance", self.adapter_source)
        self.assertIn("_camera_margin", self.adapter_source)
        self.assertIn("_edge_alpha_counts", self.adapter_source)
        self.assertIn("_render_candidate", self.adapter_source)
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"mirroring_used": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_pass05_remains_full_source_under_pass06_diagnostic(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_twohand_left_windup_diagnostic_v21.py"
        )
        full = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass05.py"
        )
        self.assertTrue((self.tool_root / full).is_file())
        self.assertIn(diagnostic, self.workflow_source)
        self.assertIn(full, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
