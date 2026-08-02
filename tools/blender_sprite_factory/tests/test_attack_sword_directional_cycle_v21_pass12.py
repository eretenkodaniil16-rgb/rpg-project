from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass12 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    F03_REFERENCE_ARM_BLEND,
    F03_REFERENCE_SCREEN_PROJECTION,
    F03_REFERENCE_WEAPON_OFFSET_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FRAME,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_CONTACT_REVISION,
)


class AttackSwordDirectionalCycleV21Pass12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_twohand_left_contact_diagnostic_v21.py"
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

    def test_contact_diagnostic_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass12")
        self.assertEqual(
            TWOHAND_LEFT_CONTACT_REVISION,
            "twohand_left_contact_from_anticipation_projection_v21_pass12",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 4)
        self.assertEqual(SOURCE_FRAME, 3)
        self.assertEqual(len(TARGET_BONES), 6)
        self.assertEqual(ARM_BLEND_CANDIDATES, (0.0, 0.1, 0.2, 0.3, 0.4))
        self.assertEqual(
            SCREEN_PROJECTION_CANDIDATES,
            (0.90, 0.86, 0.82, 0.78, 0.74, 0.70),
        )
        self.assertEqual(ANGLE_OFFSET_CANDIDATES[0], 0.0)
        self.assertEqual(ANGLE_OFFSET_CANDIDATES[-1], -64.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30747420266)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8833482546)
        self.assertEqual(F03_REFERENCE_ARM_BLEND, 0.10)
        self.assertEqual(F03_REFERENCE_SCREEN_PROJECTION, 0.82)
        self.assertEqual(F03_REFERENCE_WEAPON_OFFSET_DEGREES, 64.0)

    def test_diagnostic_blends_f04_toward_corrected_f03(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn("SOURCE_FRAME", self.diagnostic_source)
        self.assertIn("TARGET_FRAME", self.diagnostic_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass11",
            self.diagnostic_source,
        )
        self.assertIn("_projection_target_direction", self.diagnostic_source)
        self.assertIn("pass06_adapter._camera_axes", self.diagnostic_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.diagnostic_source)
        self.assertIn("pass06_adapter._restore_weapon", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_camera_margin", self.diagnostic_source)
        self.assertIn("_edge_alpha_counts", self.diagnostic_source)
        self.assertIn("_render_candidate", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_workflow_runs_pass12_and_launcher_keeps_full_pass09(self) -> None:
        diagnostic = (
            "blender_sprite_factory_attack_sword_twohand_left_contact_diagnostic_v21.py"
        )
        full = "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
        self.assertIn(diagnostic, self.workflow_source)
        self.assertIn(full, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
