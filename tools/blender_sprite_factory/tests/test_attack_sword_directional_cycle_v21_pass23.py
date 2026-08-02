from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass23 import (
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    FULLY_OCCLUDED_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_TECHNICAL_ARTIFACT_ID,
    SOURCE_TECHNICAL_RUN_ID,
)


class AttackSwordDirectionalCycleV21Pass23Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_onehand_up_depth_search_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_depth_search_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass23")
        self.assertEqual(
            ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION,
            "onehand_up_f05_f08_depth_aware_search_v21_pass23",
        )
        self.assertEqual(MIN_VISIBLE_BLADE_SAMPLES, 4)
        self.assertEqual(FULLY_OCCLUDED_CLEARANCE_PIXELS, 0.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_TECHNICAL_RUN_ID, 30758465362)
        self.assertEqual(SOURCE_TECHNICAL_ARTIFACT_ID, 8836705798)
        self.assertIn("depth_aware_search", DIAGNOSTIC_SCENE_KEY)
        self.assertIn("depth_aware_search", CONTACT_SHEET_NAME)

    def test_adapter_rejects_hidden_blade_without_terminating_search(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("except RuntimeError as error", self.adapter_source)
        self.assertIn("FULLY_OCCLUDED_CLEARANCE_PIXELS", self.adapter_source)
        self.assertIn("visible_samples < MIN_VISIBLE_BLADE_SAMPLES", self.adapter_source)
        self.assertIn("return float(FULLY_OCCLUDED_CLEARANCE_PIXELS)", self.adapter_source)
        self.assertIn("_depth_search_visible_blade_head_clearance", self.adapter_source)
        self.assertIn("weapon_geometry_changed", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)
        self.assertNotIn("obj.scale =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)

    def test_workflow_preserves_pass22_and_runs_pass23(self) -> None:
        pass22 = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_depth_aware_diagnostic_v21.py"
        )
        pass23 = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_depth_search_diagnostic_v21.py"
        )
        self.assertIn(pass22, self.workflow_source)
        self.assertIn(pass23, self.workflow_source)


if __name__ == "__main__":
    unittest.main()
