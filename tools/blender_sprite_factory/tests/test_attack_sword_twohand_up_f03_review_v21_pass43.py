from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass43 import (
    CORRECTION_PASS,
    DEPTH_CONTRACTION_ANGLE_CANDIDATES,
    DEPTH_CONTRACTION_PROJECTION_CANDIDATES,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_PASS42_ARTIFACT_ID,
    SOURCE_PASS42_RUN_ID,
    TARGETED_DEPTH_SPECS,
    TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION,
)


class AttackSwordTwohandUpF03ReviewV21Pass43Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass43.py"
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

    def test_depth_contraction_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass43")
        self.assertEqual(
            TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION,
            "twohand_up_f03_upward_arc_depth_contraction_review_v21_pass43",
        )
        self.assertEqual(
            DEPTH_CONTRACTION_PROJECTION_CANDIDATES,
            (0.40, 0.35),
        )
        self.assertEqual(
            DEPTH_CONTRACTION_ANGLE_CANDIDATES,
            (-8.0, -12.0, -16.0, -20.0),
        )
        self.assertEqual(len(TARGETED_DEPTH_SPECS), 6)
        self.assertEqual(
            [item["screen_projection"] for item in TARGETED_DEPTH_SPECS],
            [0.40, 0.40, 0.40, 0.35, 0.35, 0.35],
        )
        self.assertEqual(
            [item["weapon_offset_degrees"] for item in TARGETED_DEPTH_SPECS],
            [-12.0, -16.0, -20.0, -8.0, -12.0, -16.0],
        )
        self.assertTrue(RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE)
        self.assertEqual(SOURCE_PASS42_RUN_ID, 30860213569)
        self.assertEqual(SOURCE_PASS42_ARTIFACT_ID, 8874162733)

    def test_adapter_changes_only_depth_search_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("DEPTH_CONTRACTION_PROJECTION_CANDIDATES", self.adapter_source)
        self.assertIn("DEPTH_CONTRACTION_ANGLE_CANDIDATES", self.adapter_source)
        self.assertIn("TARGETED_DEPTH_SPECS", self.adapter_source)
        self.assertIn("_restore_pass42_contract", self.adapter_source)
        self.assertIn("_write_manifest_v21_pass43", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass43_and_retains_pass42(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("f03 depth contraction review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass42.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
