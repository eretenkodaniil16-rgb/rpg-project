from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass21 import (
    ALLOW_HILT_OCCLUSION_BEHIND_HEAD,
    BLADE_CLEARANCE_PART_IDS,
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    HILT_OCCLUSION_PART_IDS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TECHNICAL_FAILED_ARTIFACT_ID,
    TECHNICAL_FAILED_RUN_ID,
)


class AttackSwordDirectionalCycleV21Pass21Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_onehand_up_visible_blade_diagnostic_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_visible_blade_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass21")
        self.assertEqual(
            ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION,
            "onehand_up_f05_f08_visible_blade_clearance_v21_pass21",
        )
        self.assertEqual(BLADE_CLEARANCE_PART_IDS, ("blade", "highlight", "tip"))
        self.assertEqual(HILT_OCCLUSION_PART_IDS, ("guard", "grip", "pommel"))
        self.assertTrue(ALLOW_HILT_OCCLUSION_BEHIND_HEAD)
        self.assertEqual(MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30753294334)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8835191378)
        self.assertEqual(TECHNICAL_FAILED_RUN_ID, 30754498101)
        self.assertEqual(TECHNICAL_FAILED_ARTIFACT_ID, 8835541839)
        self.assertIn("visible_blade", DIAGNOSTIC_SCENE_KEY)
        self.assertIn("visible_blade", CONTACT_SHEET_NAME)

    def test_adapter_filters_collision_only_not_render_objects(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("ORIGINAL_HEAD_CLEARANCE", self.adapter_source)
        self.assertIn("_objects_by_weapon_part", self.adapter_source)
        self.assertIn('obj.get("weapon_part", "")', self.adapter_source)
        self.assertIn("_visible_blade_head_clearance", self.adapter_source)
        self.assertIn("blade_objects", self.adapter_source)
        self.assertIn("ORIGINAL_HEAD_CLEARANCE(blade_objects)", self.adapter_source)
        self.assertIn("weapon_parts_removed_from_render", self.adapter_source)
        self.assertIn("weapon_geometry_changed", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_workflow_preserves_pass20_and_runs_pass21(self) -> None:
        pass20 = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_tail_diagnostic_v21.py"
        )
        pass21 = (
            "blender_sprite_factory_attack_sword_"
            "onehand_up_visible_blade_diagnostic_v21.py"
        )
        self.assertIn(pass20, self.workflow_source)
        self.assertIn(pass21, self.workflow_source)


if __name__ == "__main__":
    unittest.main()
