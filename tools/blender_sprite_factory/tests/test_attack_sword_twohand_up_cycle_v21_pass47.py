from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass47 import (
    CORRECTION_PASS,
    F04_CAMERA_SHIFT_X_CANDIDATES,
    F04_FIXED_CENTER_COMPENSATION_USED,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_FRAME,
    TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION,
)


class AttackSwordTwohandUpCycleV21Pass47Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass47.py"
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

    def test_pass47_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass47")
        self.assertIn("f04_horizontal_overscan", (
            TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION
        ))
        self.assertEqual(TARGET_FRAME, 4)
        self.assertEqual(FRAME_ORDER, (1, 2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(
            F04_CAMERA_SHIFT_X_CANDIDATES,
            (-0.010, -0.015, -0.020, -0.025, -0.030, -0.040),
        )
        self.assertFalse(F04_FIXED_CENTER_COMPENSATION_USED)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30862305118)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8874892768)

    def test_adapter_changes_only_temporary_export_framing(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("camera.data.shift_x", self.adapter_source)
        self.assertIn("finally:", self.adapter_source)
        self.assertIn("camera.data.shift_x = original_shift_x", self.adapter_source)
        self.assertIn("_edge_alpha_counts", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass47_and_retains_historical_markers(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        lowered = self.workflow_source.lower()
        self.assertIn("f04 horizontal overscan", lowered)
        self.assertIn("complete f03 review", lowered)
        self.assertIn("targeted f03 projection review", lowered)
        self.assertIn("fine f03 offset review", lowered)
        self.assertIn("extended f03 offset review", lowered)
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "cycle_diagnostic_v21_pass46.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
