from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass30 import (
    APPROVED_REFERENCE_ACTION_ID,
    CORRECTION_PASS,
    REVIEW_ARM_BLEND,
    REVIEW_SELECTIONS,
    REVIEW_SOURCE_FRAMES,
    REVIEW_VARIANTS_PER_SOURCE,
    SOURCE_DIAGNOSTIC_ARTIFACT_ID,
    SOURCE_DIAGNOSTIC_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_REVIEW_REVISION,
)


class AttackSwordTwohandUpF01ReviewV21Pass30Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f01_review_v21_pass30.py"
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

    def test_review_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass30")
        self.assertEqual(
            TWOHAND_UP_F01_REVIEW_REVISION,
            "twohand_up_f01_multi_candidate_grip_review_v21_pass30",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAME, 1)
        self.assertEqual(REVIEW_ARM_BLEND, 0.20)
        self.assertEqual(REVIEW_SOURCE_FRAMES, (4, 5, 6))
        self.assertEqual(REVIEW_VARIANTS_PER_SOURCE, 2)
        self.assertEqual(REVIEW_SELECTIONS, ("continuity", "clearance"))
        self.assertEqual(
            APPROVED_REFERENCE_ACTION_ID,
            "attack_sword_01_twohand_down_v20",
        )
        self.assertEqual(SOURCE_DIAGNOSTIC_RUN_ID, 30850912312)
        self.assertEqual(SOURCE_DIAGNOSTIC_ARTIFACT_ID, 8870631298)

    def test_review_is_non_destructive_and_compares_approved_down(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_render_reference", self.adapter_source)
        self.assertIn("_review_candidates", self.adapter_source)
        self.assertIn("_render_up_candidate", self.adapter_source)
        self.assertIn("_write_review_sheet", self.adapter_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass26",
            self.adapter_source,
        )
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertIn("manual_review_required", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass30_review_and_keeps_full_entrypoint(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("twohand up f01 review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
