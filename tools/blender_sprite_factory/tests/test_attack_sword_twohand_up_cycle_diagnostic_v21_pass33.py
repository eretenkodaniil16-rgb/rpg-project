from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass33 import (
    ARM_BLEND,
    CORRECTION_PASS,
    DEPTH_BRANCH,
    FRAME_ORDER,
    REQUESTED_SCREEN_PROJECTION,
    SOURCE_FRAME,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_CYCLE_DIAGNOSTIC_REVISION,
    WEAPON_OFFSET_DEGREES,
)


class AttackSwordTwohandUpCycleDiagnosticV21Pass33Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass33.py"
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
        self.assertEqual(CORRECTION_PASS, "v21_pass33")
        self.assertEqual(
            TWOHAND_UP_CYCLE_DIAGNOSTIC_REVISION,
            "twohand_up_f01_central_candidate_full_cycle_diagnostic_v21_pass33",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(FRAME_ORDER, tuple(range(1, 9)))
        self.assertEqual(TARGET_FRAME, 1)
        self.assertEqual(SOURCE_FRAME, 5)
        self.assertEqual(ARM_BLEND, 0.60)
        self.assertEqual(DEPTH_BRANCH, "source")
        self.assertEqual(WEAPON_OFFSET_DEGREES, 0.0)
        self.assertEqual(REQUESTED_SCREEN_PROJECTION, 0.30)
        self.assertEqual(SOURCE_REVIEW_RUN_ID, 30853262733)
        self.assertEqual(SOURCE_REVIEW_ARTIFACT_ID, 8871647110)

    def test_adapter_renders_selected_f01_then_remaining_cycle(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_render_up_candidate", self.adapter_source)
        self.assertIn("_render_frame_v21_pass26", self.adapter_source)
        self.assertIn("FRAME_ORDER[1:]", self.adapter_source)
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertIn("manual_animation_review_required", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass33_and_keeps_full_entrypoint(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("twohand up cycle", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
