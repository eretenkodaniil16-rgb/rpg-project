from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass11 import (
    SELECTED_ARM_BLEND as ANTICIPATION_ARM_BLEND,
    SELECTED_SCREEN_PROJECTION as ANTICIPATION_SCREEN_PROJECTION,
    SELECTED_WEAPON_OFFSET_DEGREES as ANTICIPATION_WEAPON_OFFSET_DEGREES,
)
from attack_sword_directional_cycle_correction_v21_pass13 import (
    CONTACT_ACTION_DATA_CHANGED,
    CONTACT_DIAGNOSTIC_ALPHA_BBOX,
    CONTACT_DIAGNOSTIC_ARTIFACT_ID,
    CONTACT_DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    CONTACT_DIAGNOSTIC_FRAME_SIZE,
    CONTACT_DIAGNOSTIC_RUN_ID,
    CONTACT_FRAME,
    CONTACT_SELECTED_ARM_BLEND,
    CONTACT_SELECTED_CAMERA_MARGIN_PIXELS,
    CONTACT_SELECTED_HEAD_CLEARANCE_PIXELS,
    CONTACT_SELECTED_SCREEN_PROJECTION,
    CONTACT_SELECTED_WEAPON_OFFSET_DEGREES,
    CONTACT_VERIFICATION_REVISION,
    CONTACT_WEAPON_TRANSFORM_REQUIRED,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_GRIP_ID,
)


class AttackSwordDirectionalCycleV21Pass13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21_pass13.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass13.py"
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

    def test_aggregate_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass13")
        self.assertEqual(
            CONTACT_VERIFICATION_REVISION,
            "twohand_left_contact_verified_unchanged_v21_pass13",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(CONTACT_FRAME, 4)
        self.assertEqual(ANTICIPATION_ARM_BLEND, 0.10)
        self.assertEqual(ANTICIPATION_SCREEN_PROJECTION, 0.82)
        self.assertEqual(ANTICIPATION_WEAPON_OFFSET_DEGREES, 64.0)
        self.assertEqual(CONTACT_SELECTED_ARM_BLEND, 0.0)
        self.assertEqual(CONTACT_SELECTED_SCREEN_PROJECTION, 0.80)
        self.assertEqual(CONTACT_SELECTED_WEAPON_OFFSET_DEGREES, 0.0)
        self.assertGreaterEqual(
            CONTACT_SELECTED_HEAD_CLEARANCE_PIXELS,
            MIN_HEAD_CLEARANCE_PIXELS,
        )
        self.assertGreaterEqual(
            CONTACT_SELECTED_CAMERA_MARGIN_PIXELS,
            MIN_CAMERA_MARGIN_PIXELS,
        )
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertFalse(CONTACT_ACTION_DATA_CHANGED)
        self.assertFalse(CONTACT_WEAPON_TRANSFORM_REQUIRED)
        self.assertEqual(CONTACT_DIAGNOSTIC_RUN_ID, 30748303279)
        self.assertEqual(CONTACT_DIAGNOSTIC_ARTIFACT_ID, 8833645959)
        self.assertEqual(CONTACT_DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(CONTACT_DIAGNOSTIC_ALPHA_BBOX, (12, 17, 77, 92))
        self.assertEqual(
            CONTACT_DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_reuses_pass11_and_does_not_change_contact_keys(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass11",
            self.builder_source,
        )
        self.assertIn("CONTACT_VERIFICATION_REVISION", self.builder_source)
        self.assertIn("CONTACT_ACTION_DATA_CHANGED", self.builder_source)
        self.assertIn("CONTACT_WEAPON_TRANSFORM_REQUIRED", self.builder_source)
        self.assertNotIn("point.co[1]", self.builder_source)
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_wraps_pass09_and_handles_only_f03(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("BASE_RENDER_FRAME_PASS09", self.adapter_source)
        self.assertIn("_is_anticipation_frame", self.adapter_source)
        self.assertIn("_target_direction_v21_pass13", self.adapter_source)
        self.assertIn("pass06_adapter._camera_axes", self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon", self.adapter_source)
        self.assertIn("_weapon_head_clearance", self.adapter_source)
        self.assertIn("_edge_alpha_counts", self.adapter_source)
        self.assertIn("contact_metrics", self.adapter_source)
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"onehand_left_pass05_changed": False', self.adapter_source)
        self.assertIn('"twohand_left_windup_pass09_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_active_entrypoints_use_full_pass13(self) -> None:
        target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass13.py"
        )
        self.assertIn(target, self.workflow_source)
        self.assertIn(target, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
