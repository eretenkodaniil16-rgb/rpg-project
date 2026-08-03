from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass36 import (
    CORRECTION_PASS,
    PREFER_SOURCE_DEPTH_BRANCH,
    REVIEW_VARIANT_COUNT,
    SELECT_UNIQUE_ARM_PROFILES_FIRST,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_RUN_ID,
    TARGET_ABS_WEAPON_OFFSET_DEGREES,
    TWOHAND_UP_F02_BALANCED_REVIEW_REVISION,
    USE_MINIMAX_CONTINUITY,
)


class AttackSwordTwohandUpF02ReviewV21Pass36Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f02_review_v21_pass36.py"
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

    def test_balanced_review_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass36")
        self.assertEqual(
            TWOHAND_UP_F02_BALANCED_REVIEW_REVISION,
            "twohand_up_f02_minimax_continuity_diverse_review_v21_pass36",
        )
        self.assertEqual(TARGET_ABS_WEAPON_OFFSET_DEGREES, 24.0)
        self.assertTrue(USE_MINIMAX_CONTINUITY)
        self.assertTrue(PREFER_SOURCE_DEPTH_BRANCH)
        self.assertTrue(SELECT_UNIQUE_ARM_PROFILES_FIRST)
        self.assertEqual(REVIEW_VARIANT_COUNT, 6)
        self.assertEqual(SOURCE_REVIEW_RUN_ID, 30855228696)
        self.assertEqual(SOURCE_REVIEW_ARTIFACT_ID, 8872322456)

    def test_adapter_minimizes_worst_transition_and_diversifies(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("maximum_transition = max(from_f01, to_f03)", self.adapter_source)
        self.assertIn("transition_imbalance", self.adapter_source)
        self.assertIn("seen_arm_profiles", self.adapter_source)
        self.assertIn("_select_diverse_candidates_v21_pass36", self.adapter_source)
        self.assertIn("_restore_pass35_contract", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass36_and_retains_pass35(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("balanced continuity", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f02_review_v21_pass35.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
