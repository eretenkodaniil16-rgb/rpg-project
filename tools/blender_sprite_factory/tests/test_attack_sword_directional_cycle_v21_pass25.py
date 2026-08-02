from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass25 import (
    ARM_PROFILE_CANDIDATES,
    BASE_BONE_DELTAS_DEGREES,
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    ONEHAND_UP_F05_ARM_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SEARCH_ANGLE_OFFSETS,
    SEARCH_PROJECTIONS,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_FRAMES,
)


class AttackSwordDirectionalCycleV21Pass25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_onehand_up_f05_arm_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_f05_arm_search_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass25")
        self.assertEqual(
            ONEHAND_UP_F05_ARM_DIAGNOSTIC_REVISION,
            "onehand_up_f05_right_arm_lateral_clearance_v21_pass25",
        )
        self.assertEqual(TARGET_FRAMES, (5,))
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30758959479)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8836881277)
        self.assertGreaterEqual(len(ARM_PROFILE_CANDIDATES), 10)
        self.assertGreaterEqual(len(SEARCH_PROJECTIONS), 6)
        self.assertGreaterEqual(len(SEARCH_ANGLE_OFFSETS), 15)
        self.assertEqual(
            set(BASE_BONE_DELTAS_DEGREES),
            {"upper_arm.R", "forearm.R", "hand.R"},
        )
        self.assertIn("f05_arm", DIAGNOSTIC_SCENE_KEY)
        self.assertIn("f05_arm", CONTACT_SHEET_NAME)

    def test_adapter_applies_only_local_right_arm_pose_search(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_diagnose_f05_with_arm_search", self.adapter_source)
        self.assertIn("_apply_arm_profile", self.adapter_source)
        self.assertIn("BASE_BONE_DELTAS_DEGREES", self.adapter_source)
        self.assertIn("pass24_adapter.main()", self.adapter_source)
        self.assertIn("target_frame) not in TARGET_FRAMES", self.adapter_source)
        self.assertIn("weapon_geometry_changed", self.adapter_source)
        self.assertIn("root_translation_used", self.adapter_source)
        self.assertNotIn("obj.scale =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)

    def test_workflow_retains_pass24_and_runs_pass25(self) -> None:
        self.assertIn(
            "blender_sprite_factory_attack_sword_onehand_up_front_depth_diagnostic_v21.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_onehand_up_f05_arm_diagnostic_v21.py",
            self.workflow_source,
        )
        self.assertIn("one-hand up f05 arm-clearance", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
