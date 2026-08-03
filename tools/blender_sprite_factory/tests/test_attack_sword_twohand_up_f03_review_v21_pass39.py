from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass39 import (
    CORRECTION_PASS,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    SOURCE_PARTIAL_ARTIFACT_ID,
    SOURCE_PARTIAL_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION,
)


class AttackSwordTwohandUpF03ReviewV21Pass39Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass39.py"
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

    def test_complete_review_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass39")
        self.assertEqual(
            TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION,
            "twohand_up_f03_complete_edge_annotated_review_v21_pass39",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAME, 3)
        self.assertTrue(RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE)
        self.assertEqual(SOURCE_PARTIAL_RUN_ID, 30857179867)
        self.assertEqual(SOURCE_PARTIAL_ARTIFACT_ID, 8872998835)

    def test_adapter_records_edges_without_accepting_them(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("pass38_adapter.REQUIRE_ZERO_EDGE_ALPHA = False", self.adapter_source)
        self.assertIn("accepted_by_boundary_contract", self.adapter_source)
        self.assertIn("edge_touching", self.adapter_source)
        self.assertIn("_restore_pass38_contract", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass39_and_retains_pass38(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("complete f03 review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass38.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
