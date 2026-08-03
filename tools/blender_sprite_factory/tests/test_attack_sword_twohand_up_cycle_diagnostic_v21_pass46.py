from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass46 import (
    CORRECTION_PASS,
    F03_ARM_BLEND,
    F03_CAMERA_SHIFT_Y,
    F03_EDGE_COUNTS,
    F03_REQUESTED_SCREEN_PROJECTION,
    F03_SOURCE_POSE_LABEL,
    F03_VALIDATED_VISIBLE_BLADE_SAMPLES,
    F03_WEAPON_OFFSET_DEGREES,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_OVERSCAN_ARTIFACT_ID,
    SOURCE_OVERSCAN_RUN_ID,
    TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION,
)


class AttackSwordTwohandUpCycleDiagnosticV21Pass46Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass46.py"
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

    def test_selected_f03_cycle_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass46")
        self.assertEqual(
            TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION,
            "twohand_up_f01_f02_f03_selected_full_cycle_diagnostic_v21_pass46",
        )
        self.assertEqual(FRAME_ORDER, (1, 2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(F03_SOURCE_POSE_LABEL, "original_f05")
        self.assertEqual(F03_ARM_BLEND, 0.60)
        self.assertEqual(F03_REQUESTED_SCREEN_PROJECTION, 0.25)
        self.assertEqual(F03_WEAPON_OFFSET_DEGREES, 0.0)
        self.assertEqual(F03_CAMERA_SHIFT_Y, 0.02)
        self.assertEqual(F03_VALIDATED_VISIBLE_BLADE_SAMPLES, 557)
        self.assertEqual(
            F03_EDGE_COUNTS,
            {"bottom": 0, "left": 0, "right": 0, "top": 0},
        )
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_OVERSCAN_RUN_ID, 30861784696)
        self.assertEqual(SOURCE_OVERSCAN_ARTIFACT_ID, 8874697772)

    def test_adapter_uses_selected_f03_without_action_mutation(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_render_frame_v21_pass46", self.adapter_source)
        self.assertIn("pass38_adapter._render_f03_candidate", self.adapter_source)
        self.assertIn("camera.data.shift_y = F03_CAMERA_SHIFT_Y", self.adapter_source)
        self.assertIn("camera.data.shift_y = original_shift_y", self.adapter_source)
        self.assertIn("selected_manual_candidate_used", self.adapter_source)
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("camera.rotation_euler =", self.adapter_source)
        self.assertNotIn("camera.data.ortho_scale =", self.adapter_source)

    def test_workflow_uses_pass46_and_retains_pass45(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("f01 f02 f03 selected full cycle", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass45.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass37.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
