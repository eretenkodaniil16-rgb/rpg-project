from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass05 import (
    BLEND_CANDIDATES,
    CORRECTION_PASS,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    RECOVERY_CLEARANCE_REVISION,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


class AttackSwordDirectionalCycleV21Pass05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.diagnostic_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_left_recovery_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_recovery_diagnostic_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass05")
        self.assertEqual(
            RECOVERY_CLEARANCE_REVISION,
            "left_onehand_recovery_to_guard_blend_v21_pass05",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_onehand_left_v21")
        self.assertEqual(TARGET_GRIP_ID, "onehand_ready")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 7)
        self.assertEqual(GUARD_FRAME, 8)
        self.assertEqual(BLEND_CANDIDATES[0], 0.10)
        self.assertEqual(BLEND_CANDIDATES[-1], 1.00)
        self.assertGreater(MIN_HEAD_CLEARANCE_PIXELS, 0.0)
        self.assertGreater(MIN_CAMERA_MARGIN_PIXELS, 0.0)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30741831909)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8831682378)

    def test_diagnostic_changes_only_right_arm_pose(self) -> None:
        ast.parse(self.diagnostic_source)
        self.assertIn(
            'TARGET_BONES = ("upper_arm.R", "forearm.R", "hand.R")',
            self.diagnostic_source,
        )
        self.assertIn("_shortest_angle_delta", self.diagnostic_source)
        self.assertIn("_weapon_head_clearance", self.diagnostic_source)
        self.assertIn("_camera_margin", self.diagnostic_source)
        self.assertIn("_render_candidate", self.diagnostic_source)
        self.assertNotIn("obj.scale", self.diagnostic_source)
        self.assertNotIn("mesh.vertices", self.diagnostic_source)

    def test_workflow_targets_recovery_diagnostic(self) -> None:
        target = (
            "blender_sprite_factory_attack_sword_left_recovery_diagnostic_v21.py"
        )
        self.assertIn(target, self.workflow_source)
        self.assertIn("left one-hand recovery v21 pass05", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
