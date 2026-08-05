from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass24 import (
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    FLIP_CAMERA_DEPTH_BRANCH,
    ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
)


class AttackSwordDirectionalCycleV21Pass24Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_onehand_up_front_depth_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_front_depth_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass24")
        self.assertEqual(
            ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION,
            "onehand_up_f05_f08_front_depth_branch_v21_pass24",
        )
        self.assertTrue(FLIP_CAMERA_DEPTH_BRANCH)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30758735419)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8836789913)
        self.assertIn("front_depth", DIAGNOSTIC_SCENE_KEY)
        self.assertIn("front_depth", CONTACT_SHEET_NAME)

    def test_adapter_flips_only_weapon_depth_direction(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("target_depth_sign = -source_depth_sign", self.adapter_source)
        self.assertIn("_projection_target_direction", self.adapter_source)
        self.assertIn("weapon_geometry_changed", self.adapter_source)
        self.assertIn("root_translation_used", self.adapter_source)
        self.assertNotIn("obj.scale =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_retains_pass23_and_runs_pass24(self) -> None:
        self.assertIn(
            "blender_sprite_factory_attack_sword_onehand_up_depth_search_diagnostic_v21.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_onehand_up_front_depth_diagnostic_v21.py",
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
