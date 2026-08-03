from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass45 import (
    CAMERA_SHIFT_Y_CANDIDATES,
    CORRECTION_PASS,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    SELECTED_SCREEN_PROJECTION,
    SELECTED_WEAPON_OFFSET_DEGREES,
    SOURCE_PASS44_ARTIFACT_ID,
    SOURCE_PASS44_RUN_ID,
    TARGETED_OVERSCAN_SPECS,
    TWOHAND_UP_F03_CAMERA_OVERSCAN_REVIEW_REVISION,
)


class AttackSwordTwohandUpF03ReviewV21Pass45Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass45.py"
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

    def test_camera_overscan_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass45")
        self.assertEqual(
            TWOHAND_UP_F03_CAMERA_OVERSCAN_REVIEW_REVISION,
            "twohand_up_f03_camera_overscan_review_v21_pass45",
        )
        self.assertEqual(
            CAMERA_SHIFT_Y_CANDIDATES,
            (0.02, 0.04, 0.06, 0.08, 0.10, 0.12),
        )
        self.assertEqual(SELECTED_SCREEN_PROJECTION, 0.25)
        self.assertEqual(SELECTED_WEAPON_OFFSET_DEGREES, 0.0)
        self.assertEqual(len(TARGETED_OVERSCAN_SPECS), 6)
        self.assertEqual(
            [item["camera_shift_y"] for item in TARGETED_OVERSCAN_SPECS],
            list(CAMERA_SHIFT_Y_CANDIDATES),
        )
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE)
        self.assertEqual(SOURCE_PASS44_RUN_ID, 30861229962)
        self.assertEqual(SOURCE_PASS44_ARTIFACT_ID, 8874507849)

    def test_adapter_uses_temporary_camera_shift_only(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("camera.data.shift_y = shift_y", self.adapter_source)
        self.assertIn("camera.data.shift_y = original_shift_y", self.adapter_source)
        self.assertIn("_render_f03_candidate_v21_pass45", self.adapter_source)
        self.assertIn("camera_shift_persistent_change", self.adapter_source)
        self.assertIn("_restore_pass44_contract", self.adapter_source)
        self.assertNotIn("camera.rotation_euler =", self.adapter_source)
        self.assertNotIn("camera.data.ortho_scale =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)

    def test_workflow_uses_pass45_and_retains_pass44(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("f03 camera overscan review", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f03_review_v21_pass44.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
