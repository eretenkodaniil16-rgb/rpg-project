from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass40 import (
    CORRECTION_PASS,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_COMPLETE_ARTIFACT_ID,
    SOURCE_COMPLETE_RUN_ID,
    TARGETED_PROJECTION_SPECS,
    TWOHAND_UP_F03_TARGETED_PROJECTION_REVIEW_REVISION,
)


class AttackSwordTwohandUpF03ReviewV21Pass40Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass40.py"
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

    def test_targeted_projection_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass40")
        self.assertEqual(
            TWOHAND_UP_F03_TARGETED_PROJECTION_REVIEW_REVISION,
            "twohand_up_f03_upward_arc_projection_review_v21_pass40",
        )
        self.assertEqual(len(TARGETED_PROJECTION_SPECS), 6)
        self.assertEqual(
            [item["screen_projection"] for item in TARGETED_PROJECTION_SPECS],
            [0.55, 0.50, 0.45, 0.55, 0.50, 0.45],
        )
        self.assertEqual(
            [item["source_pose_code"] for item in TARGETED_PROJECTION_SPECS],
            [5, 5, 5, 4, 4, 4],
        )
        self.assertTrue(RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE)
        self.assertEqual(SOURCE_COMPLETE_RUN_ID, 30857617930)
        self.assertEqual(SOURCE_COMPLETE_ARTIFACT_ID, 8873199189)

    def test_adapter_changes_only_candidate_selection(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_select_targeted_projection_candidates", self.adapter_source)
        self.assertIn("requested_screen_projection", self.adapter_source)
        self.assertIn("selection_strategy", self.adapter_source)
        self.assertIn("_restore_pass39_contract", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass40_and_retains_pass39(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("targeted f03 projection review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass39.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
