from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass02 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CLEARANCE_FRAMES,
    CORRECTION_PASS,
    DIRECTIONAL_CLEARANCE_REVISION,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_BY_GRIP,
    MIN_NONKEY_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_DIRECTIONS,
)


class AttackSwordDirectionalCycleV21Pass02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass02.py"
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

    def test_correction_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass02")
        self.assertEqual(
            DIRECTIONAL_CLEARANCE_REVISION,
            "rigid_weapon_export_planner_v21_pass02",
        )
        self.assertEqual(TARGET_DIRECTIONS, ("left", "right", "up"))
        self.assertEqual(CLEARANCE_FRAMES, (2, 3, 4))
        self.assertEqual(ANGLE_SEARCH_LIMIT_DEGREES, 40)
        self.assertEqual(ANGLE_SEARCH_STEP_DEGREES, 2)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertEqual(MIN_NONKEY_HEAD_CLEARANCE_PIXELS, 1.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_BY_GRIP["onehand_ready"], 2.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_BY_GRIP["twohand_center_high"], 4.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30739200539)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8830826692)

    def test_adapter_parses_and_uses_rigid_weapon_planner(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon", self.adapter_source)
        self.assertIn("export_adapter._weapon_head_clearance", self.adapter_source)
        self.assertIn("keypose_adapter._edge_alpha_counts", self.adapter_source)
        self.assertIn("export_adapter._render_candidate", self.adapter_source)
        self.assertIn("MIN_NONKEY_HEAD_CLEARANCE_PIXELS", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_down_source_is_not_replanned(self) -> None:
        self.assertIn("if direction not in TARGET_DIRECTIONS:", self.adapter_source)
        self.assertIn("return BASE_RENDER_FRAME(", self.adapter_source)
        self.assertIn('"approved_down_v20_changed": False', self.adapter_source)
        self.assertIn('"body_pose_changed": False', self.adapter_source)

    def test_pass02_remains_reproducible_under_pass09(self) -> None:
        pass02_target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass02.py"
        )
        active_target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
        )
        self.assertTrue((self.tool_root / pass02_target).is_file())
        self.assertIn(active_target, self.workflow_source)
        self.assertIn(active_target, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
