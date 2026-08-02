from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass04 import (
    ANTICIPATION_CLEARANCE_REVISION,
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    SELECTED_CAMERA_MARGIN_PIXELS,
    SELECTED_HEAD_CLEARANCE_PIXELS,
    SELECTED_INCREMENTAL_WEIGHT,
    SELECTED_TOTAL_WEIGHT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
)


class AttackSwordDirectionalCycleV21Pass04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root
            / "attack_sword_directional_cycle_builder_v21_pass04.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass04.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")
        cls.launcher_source = (
            cls.tool_root / "run_blender_sprite_pilot.ps1"
        ).read_text(encoding="utf-8")

    def test_selected_anticipation_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass04")
        self.assertEqual(
            ANTICIPATION_CLEARANCE_REVISION,
            "left_onehand_anticipation_weight_v21_pass04",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_onehand_left_v21")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 3)
        self.assertEqual(SELECTED_TOTAL_WEIGHT, 1.60)
        self.assertAlmostEqual(SELECTED_INCREMENTAL_WEIGHT, 1.20)
        self.assertGreaterEqual(
            SELECTED_HEAD_CLEARANCE_PIXELS,
            MIN_HEAD_CLEARANCE_PIXELS,
        )
        self.assertGreaterEqual(
            SELECTED_CAMERA_MARGIN_PIXELS,
            MIN_CAMERA_MARGIN_PIXELS,
        )
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX, (35, 26, 93, 92))
        self.assertEqual(
            DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_changes_only_f03_action_channels(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass03",
            self.builder_source,
        )
        self.assertIn("SELECTED_INCREMENTAL_WEIGHT", self.builder_source)
        self.assertIn("TARGET_FRAME", self.builder_source)
        self.assertIn("point.co[1]", self.builder_source)
        self.assertIn(
            'scene["attack_sword_directional_cycle_v21_pass04_down_changed"] = False',
            self.builder_source,
        )
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_wraps_pass03_and_preserves_locked_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("pass03_adapter.main()", self.adapter_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass04",
            self.adapter_source,
        )
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"mirroring_used": False', self.adapter_source)
        self.assertIn('"negative_scale_used": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)

    def test_pass04_remains_source_under_pass09(self) -> None:
        pass04_target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass04.py"
        )
        active_target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
        )
        self.assertTrue((self.tool_root / pass04_target).is_file())
        self.assertIn(active_target, self.workflow_source)
        self.assertIn(active_target, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
