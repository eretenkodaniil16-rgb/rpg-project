from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass26 import (
    ARM_TARGET_FRAME,
    CORRECTION_PASS,
    FLIP_CAMERA_DEPTH_BRANCH,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME,
    ONEHAND_UP_FINAL_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_ARM_PROFILE,
    SELECTED_BONE_DELTAS_DEGREES,
    SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
    SOURCE_DIAGNOSTIC_ARTIFACT_ID,
    SOURCE_DIAGNOSTIC_RUN_ID,
    SOURCE_FULL_CONTEXT_ARTIFACT_ID,
    SOURCE_FULL_CONTEXT_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
)


class AttackSwordDirectionalCycleV21Pass26Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass26.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass26.py"
        ).read_text(encoding="utf-8")
        cls.launcher_source = (
            cls.tool_root / "run_blender_sprite_pilot.ps1"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_integrated_onehand_up_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass26")
        self.assertEqual(
            ONEHAND_UP_FINAL_REVISION,
            "onehand_up_f05_arm_clearance_integrated_v21_pass26",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_onehand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "onehand_ready")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAMES, (5, 6, 7, 8))
        self.assertEqual(ARM_TARGET_FRAME, 5)
        self.assertEqual(SELECTED_ARM_PROFILE["scale"], 0.5)
        self.assertEqual(SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME[5], -24.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME[5], 1.5)
        self.assertGreaterEqual(MIN_CAMERA_MARGIN_PIXELS, 12.0)
        self.assertTrue(FLIP_CAMERA_DEPTH_BRANCH)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_DIAGNOSTIC_RUN_ID, 30773183585)
        self.assertEqual(SOURCE_DIAGNOSTIC_ARTIFACT_ID, 8841230831)
        self.assertEqual(SOURCE_FULL_CONTEXT_RUN_ID, 30773644539)
        self.assertEqual(SOURCE_FULL_CONTEXT_ARTIFACT_ID, 8841651589)
        self.assertEqual(
            set(SELECTED_BONE_DELTAS_DEGREES),
            {"upper_arm.R", "forearm.R", "hand.R"},
        )

    def test_builder_changes_only_onehand_up_f05_action_data(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass19(context)",
            self.builder_source,
        )
        self.assertIn("ARM_TARGET_FRAME", self.builder_source)
        self.assertIn("SELECTED_BONE_DELTAS_DEGREES", self.builder_source)
        self.assertIn("point.co[1]", self.builder_source)
        self.assertIn("down_changed", self.builder_source)
        self.assertIn("twohand_up_changed", self.builder_source)
        self.assertNotIn("vertex.co", self.builder_source)
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("root.location", self.builder_source)

    def test_adapter_renders_full_cycle_with_depth_aware_clearance(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("BASE_RENDER_FRAME_PASS19", self.adapter_source)
        self.assertIn("_depth_aware_visible_blade_head_clearance", self.adapter_source)
        self.assertIn("target_depth_sign = -source_depth_sign", self.adapter_source)
        self.assertIn("attack_sword_directional_cycle_v21_pass26", self.adapter_source)
        self.assertIn("weapon_geometry_changed", self.adapter_source)
        self.assertIn("root_translation_used", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)

    def test_ci_and_windows_launcher_use_integrated_pass26(self) -> None:
        adapter_name = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass26.py"
        )
        self.assertIn(adapter_name, self.workflow_source)
        self.assertIn(adapter_name, self.launcher_source)
        self.assertIn("full directional cycle", self.workflow_source)
        self.assertIn("attack_sword_01_directional_cycle_v21.png", self.launcher_source)


if __name__ == "__main__":
    unittest.main()
