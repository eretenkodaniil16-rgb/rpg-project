from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass37 import (
    CORRECTION_PASS,
    F01_ARM_BLEND,
    F01_SOURCE_FRAME,
    F02_ARM_BLEND,
    F02_CONTINUITY_FROM_F01_RMS_DEGREES,
    F02_CONTINUITY_TO_F03_RMS_DEGREES,
    F02_DEPTH_BRANCH,
    F02_SOURCE_FRAME,
    F02_WEAPON_OFFSET_DEGREES,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_RUN_ID,
    SOURCE_REVIEW_VARIANT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_GRIP_ID,
    TWOHAND_UP_SELECTED_CYCLE_REVISION,
)


class AttackSwordTwohandUpCycleDiagnosticV21Pass37Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass37.py"
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

    def test_selected_cycle_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass37")
        self.assertEqual(
            TWOHAND_UP_SELECTED_CYCLE_REVISION,
            "twohand_up_f01_f02_selected_full_cycle_diagnostic_v21_pass37",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(FRAME_ORDER, (1, 2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(F01_SOURCE_FRAME, 5)
        self.assertEqual(F01_ARM_BLEND, 0.60)
        self.assertEqual(F02_SOURCE_FRAME, 4)
        self.assertEqual(F02_ARM_BLEND, 0.40)
        self.assertEqual(F02_DEPTH_BRANCH, "flipped")
        self.assertEqual(F02_WEAPON_OFFSET_DEGREES, 0.0)
        self.assertLess(F02_CONTINUITY_FROM_F01_RMS_DEGREES, 13.0)
        self.assertLess(F02_CONTINUITY_TO_F03_RMS_DEGREES, 13.5)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_REVIEW_RUN_ID, 30855993842)
        self.assertEqual(SOURCE_REVIEW_ARTIFACT_ID, 8872611253)
        self.assertEqual(SOURCE_REVIEW_VARIANT, 3)

    def test_adapter_renders_selected_first_frames_then_cycle(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_render_corrected_f01_reference", self.adapter_source)
        self.assertIn("_render_f02_candidate", self.adapter_source)
        self.assertIn("FRAME_ORDER[2:]", self.adapter_source)
        self.assertIn("_render_frame_v21_pass26", self.adapter_source)
        self.assertIn("action_data_changed", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass37_and_retains_full_entrypoint(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("selected full cycle", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f02_review_v21_pass36.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
