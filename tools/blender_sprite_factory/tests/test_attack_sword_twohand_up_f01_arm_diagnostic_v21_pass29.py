from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass29 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    DEPTH_BRANCH_CANDIDATES,
    MIN_VISIBLE_BLADE_SAMPLES,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FRAME_CANDIDATES,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_ARM_DIAGNOSTIC_REVISION,
)


class AttackSwordTwohandUpF01ArmDiagnosticV21Pass29Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f01_arm_diagnostic_v21_pass29.py"
        )
        cls.adapter_source = (
            cls.tool_root / cls.adapter_name
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_coordinated_arm_search_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass29")
        self.assertEqual(
            TWOHAND_UP_F01_ARM_DIAGNOSTIC_REVISION,
            "twohand_up_f01_coordinated_arm_depth_search_v21_pass29",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAME, 1)
        self.assertEqual(
            TARGET_BONES,
            (
                "upper_arm.L",
                "forearm.L",
                "hand.L",
                "upper_arm.R",
                "forearm.R",
                "hand.R",
            ),
        )
        self.assertEqual(SOURCE_FRAME_CANDIDATES[0], 2)
        self.assertEqual(min(ARM_BLEND_CANDIDATES), 0.10)
        self.assertEqual(max(ARM_BLEND_CANDIDATES), 1.00)
        self.assertLessEqual(min(SCREEN_PROJECTION_CANDIDATES), 0.25)
        self.assertGreaterEqual(max(abs(v) for v in ANGLE_OFFSET_CANDIDATES), 96)
        self.assertEqual(DEPTH_BRANCH_CANDIDATES, ("source", "flipped"))
        self.assertEqual(MIN_VISIBLE_BLADE_SAMPLES, 4)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30850308797)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8870383301)

    def test_diagnostic_changes_only_temporary_arm_pose(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass26",
            self.adapter_source,
        )
        self.assertIn("_set_arm_blend", self.adapter_source)
        self.assertIn("_restore_arm", self.adapter_source)
        self.assertIn("TARGET_BONES", self.adapter_source)
        self.assertIn(
            "_depth_search_visible_blade_head_clearance",
            self.adapter_source,
        )
        self.assertIn("visible_blade_samples", self.adapter_source)
        self.assertIn("diagnostic_only", self.adapter_source)
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass29_diagnostic_and_keeps_full_entrypoint(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("twohand up f01 arm", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
