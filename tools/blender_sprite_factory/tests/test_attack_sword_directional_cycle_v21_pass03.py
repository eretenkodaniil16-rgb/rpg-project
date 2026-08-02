from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass03 import (
    ARM_CLEARANCE_REVISION,
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    SELECTED_DEPTH_DEGREES,
    SELECTED_HEAD_CLEARANCE_PIXELS,
    SELECTED_LIFT_DEGREES,
    SELECTED_SWEEP_DEGREES,
    SMOOTHING_WEIGHTS,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
)


class AttackSwordDirectionalCycleV21Pass03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root
            / "attack_sword_directional_cycle_builder_v21_pass03.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass03.py"
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

    def test_selected_diagnostic_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass03")
        self.assertEqual(
            ARM_CLEARANCE_REVISION,
            "left_onehand_windup_arm_clearance_v21_pass03",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_onehand_left_v21")
        self.assertEqual(TARGET_DIRECTION, "left")
        self.assertEqual(TARGET_FRAME, 2)
        self.assertEqual(SELECTED_LIFT_DEGREES, -40.0)
        self.assertEqual(SELECTED_SWEEP_DEGREES, 0.0)
        self.assertEqual(SELECTED_DEPTH_DEGREES, 20.0)
        self.assertGreaterEqual(
            SELECTED_HEAD_CLEARANCE_PIXELS,
            MIN_HEAD_CLEARANCE_PIXELS,
        )
        self.assertGreater(MIN_CAMERA_MARGIN_PIXELS, 0.0)
        self.assertEqual(SMOOTHING_WEIGHTS, {1: 0.30, 2: 1.00, 3: 0.40})
        self.assertEqual(DIAGNOSTIC_FRAME_SIZE, (96, 96))
        self.assertEqual(DIAGNOSTIC_ALPHA_BBOX, (35, 23, 93, 92))
        self.assertEqual(
            DIAGNOSTIC_EDGE_ALPHA_COUNTS,
            {"left": 0, "right": 0, "top": 0, "bottom": 0},
        )

    def test_builder_changes_only_target_action_channels(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("create_attack_sword_directional_cycle_actions_v21", self.builder_source)
        self.assertIn("TARGET_ACTION_ID", self.builder_source)
        self.assertIn('pose.bones["{bone_name}"].rotation_euler', self.builder_source)
        self.assertIn("SMOOTHING_WEIGHTS", self.builder_source)
        self.assertIn("point.co[1]", self.builder_source)
        self.assertIn('scene["attack_sword_directional_cycle_v21_pass03_down_changed"] = False', self.builder_source)
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("mesh.vertices", self.builder_source)

    def test_adapter_wraps_pass02_without_replacing_render_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("pass02_adapter.main()", self.adapter_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass03",
            self.adapter_source,
        )
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"mirroring_used": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)

    def test_pass03_remains_source_under_pass09(self) -> None:
        pass03_target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass03.py"
        )
        active_target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
        )
        self.assertTrue((self.tool_root / pass03_target).is_file())
        self.assertIn(active_target, self.workflow_source)
        self.assertIn(active_target, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
