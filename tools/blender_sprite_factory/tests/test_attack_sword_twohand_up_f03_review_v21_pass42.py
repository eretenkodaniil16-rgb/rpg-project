from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass42 import (
    CORRECTION_PASS,
    EXTENDED_ANGLE_OFFSET_CANDIDATES,
    EXTENDED_SCREEN_PROJECTION_CANDIDATES,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_PASS41_ARTIFACT_ID,
    SOURCE_PASS41_RUN_ID,
    TARGETED_OFFSET_SPECS,
    TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION,
)


class AttackSwordTwohandUpF03ReviewV21Pass42Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass42.py"
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

    def test_extended_offset_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass42")
        self.assertEqual(
            TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION,
            "twohand_up_f03_upward_arc_extended_offset_review_v21_pass42",
        )
        self.assertEqual(EXTENDED_SCREEN_PROJECTION_CANDIDATES, (0.45,))
        self.assertEqual(
            EXTENDED_ANGLE_OFFSET_CANDIDATES,
            (-12.0, -14.0, -16.0, -18.0, -20.0, -22.0),
        )
        self.assertEqual(len(TARGETED_OFFSET_SPECS), 6)
        self.assertEqual(
            [item["screen_projection"] for item in TARGETED_OFFSET_SPECS],
            [0.45] * 6,
        )
        self.assertEqual(
            [item["weapon_offset_degrees"] for item in TARGETED_OFFSET_SPECS],
            list(EXTENDED_ANGLE_OFFSET_CANDIDATES),
        )
        self.assertTrue(RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE)
        self.assertEqual(SOURCE_PASS41_RUN_ID, 30859624987)
        self.assertEqual(SOURCE_PASS41_ARTIFACT_ID, 8873961062)

    def test_adapter_changes_only_fine_search_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("EXTENDED_SCREEN_PROJECTION_CANDIDATES", self.adapter_source)
        self.assertIn("EXTENDED_ANGLE_OFFSET_CANDIDATES", self.adapter_source)
        self.assertIn("TARGETED_OFFSET_SPECS", self.adapter_source)
        self.assertIn("_restore_pass41_contract", self.adapter_source)
        self.assertIn("_write_manifest_v21_pass42", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass42_and_retains_pass41(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("extended f03 offset review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass41.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
