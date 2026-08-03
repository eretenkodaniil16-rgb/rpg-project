from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass44 import (
    COMPACT_ANGLE_OFFSET_CANDIDATES,
    COMPACT_PROJECTION_CANDIDATES,
    CORRECTION_PASS,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_PASS43_ARTIFACT_ID,
    SOURCE_PASS43_RUN_ID,
    TARGETED_COMPACT_SPECS,
    TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION,
)


class AttackSwordTwohandUpF03ReviewV21Pass44Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass44.py"
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

    def test_compact_projection_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass44")
        self.assertEqual(
            TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION,
            "twohand_up_f03_upward_arc_compact_projection_review_v21_pass44",
        )
        self.assertEqual(COMPACT_PROJECTION_CANDIDATES, (0.30, 0.25, 0.20))
        self.assertEqual(
            COMPACT_ANGLE_OFFSET_CANDIDATES,
            (0.0, -4.0, -8.0, -12.0),
        )
        self.assertEqual(len(TARGETED_COMPACT_SPECS), 6)
        self.assertEqual(
            [item["screen_projection"] for item in TARGETED_COMPACT_SPECS],
            [0.30, 0.30, 0.25, 0.25, 0.25, 0.20],
        )
        self.assertEqual(
            [item["weapon_offset_degrees"] for item in TARGETED_COMPACT_SPECS],
            [-8.0, -12.0, 0.0, -4.0, -8.0, 0.0],
        )
        self.assertTrue(RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE)
        self.assertEqual(SOURCE_PASS43_RUN_ID, 30860714915)
        self.assertEqual(SOURCE_PASS43_ARTIFACT_ID, 8874331270)

    def test_adapter_changes_only_compact_search_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("COMPACT_PROJECTION_CANDIDATES", self.adapter_source)
        self.assertIn("COMPACT_ANGLE_OFFSET_CANDIDATES", self.adapter_source)
        self.assertIn("TARGETED_COMPACT_SPECS", self.adapter_source)
        self.assertIn("_restore_pass43_contract", self.adapter_source)
        self.assertIn("_write_manifest_v21_pass44", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass44_and_retains_pass43(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("f03 compact projection review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass43.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
