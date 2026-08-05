from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass38 import (
    CORRECTION_PASS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    NEXT_REFERENCE_FRAME,
    PREVIOUS_REFERENCE_FRAME,
    REQUIRE_ZERO_EDGE_ALPHA,
    REVIEW_VARIANT_COUNT,
    SELECTED_F02_ARM_BLEND,
    SELECTED_F02_SOURCE_FRAME,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F03_CONTINUITY_REVIEW_REVISION,
    USE_MINIMAX_CONTINUITY,
)


class AttackSwordTwohandUpF03ReviewV21Pass38Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass38.py"
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

    def test_f03_continuity_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass38")
        self.assertEqual(
            TWOHAND_UP_F03_CONTINUITY_REVIEW_REVISION,
            "twohand_up_f03_selected_f02_to_f04_continuity_review_v21_pass38",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAME, 3)
        self.assertEqual(PREVIOUS_REFERENCE_FRAME, 2)
        self.assertEqual(NEXT_REFERENCE_FRAME, 4)
        self.assertEqual(SELECTED_F02_SOURCE_FRAME, 4)
        self.assertEqual(SELECTED_F02_ARM_BLEND, 0.40)
        self.assertEqual(MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS, 0.0)
        self.assertGreaterEqual(MIN_VISIBLE_BLADE_SAMPLES, 8)
        self.assertEqual(REVIEW_VARIANT_COUNT, 6)
        self.assertTrue(USE_MINIMAX_CONTINUITY)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30856727623)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8872812482)

    def test_adapter_is_diagnostic_and_non_destructive(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("selected_f02_rotations", self.adapter_source)
        self.assertIn("continuity_from_selected_f02_rms_degrees", self.adapter_source)
        self.assertIn("continuity_to_original_f04_rms_degrees", self.adapter_source)
        self.assertIn("maximum_transition_rms_degrees", self.adapter_source)
        self.assertIn("_select_diverse_candidates", self.adapter_source)
        self.assertIn("_render_selected_f02_reference", self.adapter_source)
        self.assertIn("_render_original_f04_reference", self.adapter_source)
        self.assertIn('"action_data_changed": False', self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass38_and_retains_pass37(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("f03 continuity review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass37.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
