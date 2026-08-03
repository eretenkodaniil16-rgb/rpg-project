from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass32 import (
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    MAX_ABS_WEAPON_OFFSET_DEGREES,
    REVIEW_VARIANT_COUNT,
    SOURCE_FRAME_CANDIDATES,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_RUN_ID,
    TARGET_ABS_WEAPON_OFFSET_DEGREES,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_FULL_BLEND_REVIEW_REVISION,
)


class AttackSwordTwohandUpF01FullBlendReviewV21Pass32Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f01_full_blend_review_v21_pass32.py"
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

    def test_full_blend_review_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass32")
        self.assertEqual(
            TWOHAND_UP_F01_FULL_BLEND_REVIEW_REVISION,
            "twohand_up_f01_full_blend_minimum_offset_review_v21_pass32",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAME, 1)
        self.assertEqual(SOURCE_FRAME_CANDIDATES[0], 2)
        self.assertEqual(ARM_BLEND_CANDIDATES, (0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00))
        self.assertEqual(MAX_ABS_WEAPON_OFFSET_DEGREES, 48.0)
        self.assertEqual(TARGET_ABS_WEAPON_OFFSET_DEGREES, 24.0)
        self.assertEqual(REVIEW_VARIANT_COUNT, 6)
        self.assertEqual(SOURCE_REVIEW_RUN_ID, 30852711829)
        self.assertEqual(SOURCE_REVIEW_ARTIFACT_ID, 8871341984)

    def test_adapter_evaluates_all_blends_before_selection(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("all_candidates", self.adapter_source)
        self.assertIn("for arm_blend in ARM_BLEND_CANDIDATES", self.adapter_source)
        self.assertIn("minimum_offset_by_blend", self.adapter_source)
        self.assertIn("_select_diverse_candidates", self.adapter_source)
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass32_and_keeps_full_entrypoint(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("twohand up f01 full blend", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
