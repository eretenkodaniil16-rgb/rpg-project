from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass22 import (
    ALLOW_BLADE_OCCLUSION_BEHIND_HEAD,
    BLADE_CLEARANCE_PART_IDS,
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DEPTH_EPSILON_WORLD,
    DEPTH_MAP_SUPERSAMPLE,
    DIAGNOSTIC_SCENE_KEY,
    HEAD_MODULE_IDS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    WEAPON_EDGE_SAMPLE_STEP_PIXELS,
)


class AttackSwordDirectionalCycleV21Pass22Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_onehand_up_depth_aware_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_depth_aware_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass22")
        self.assertEqual(
            ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION,
            "onehand_up_f05_f08_depth_aware_clearance_v21_pass22",
        )
        self.assertEqual(HEAD_MODULE_IDS, ("head", "hair"))
        self.assertEqual(BLADE_CLEARANCE_PART_IDS, ("blade", "highlight", "tip"))
        self.assertEqual(MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS, 1.0)
        self.assertEqual(DEPTH_MAP_SUPERSAMPLE, 4)
        self.assertEqual(WEAPON_EDGE_SAMPLE_STEP_PIXELS, 0.25)
        self.assertEqual(DEPTH_EPSILON_WORLD, 0.01)
        self.assertTrue(ALLOW_BLADE_OCCLUSION_BEHIND_HEAD)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30754861863)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8835658875)
        self.assertIn("depth_aware", DIAGNOSTIC_SCENE_KEY)
        self.assertIn("depth_aware", CONTACT_SHEET_NAME)

    def test_adapter_uses_camera_depth_without_mutating_assets(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("world_to_camera_view", self.adapter_source)
        self.assertIn("camera.matrix_world.inverted()", self.adapter_source)
        self.assertIn("mesh.calc_loop_triangles()", self.adapter_source)
        self.assertIn("_build_head_depth_field", self.adapter_source)
        self.assertIn("_depth_aware_visible_blade_head_clearance", self.adapter_source)
        self.assertIn("camera_z <= head_depth - DEPTH_EPSILON_WORLD", self.adapter_source)
        self.assertIn("WEAPON_EDGE_SAMPLE_STEP_PIXELS", self.adapter_source)
        self.assertIn("weapon_geometry_changed", self.adapter_source)
        self.assertIn("root_translation_used", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)
        self.assertNotIn("obj.scale =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)

    def test_workflow_preserves_pass21_and_runs_pass22(self) -> None:
        pass21 = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_visible_blade_diagnostic_v21.py"
        )
        pass22 = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_depth_aware_diagnostic_v21.py"
        )
        self.assertIn(pass21, self.workflow_source)
        self.assertIn(pass22, self.workflow_source)


if __name__ == "__main__":
    unittest.main()
