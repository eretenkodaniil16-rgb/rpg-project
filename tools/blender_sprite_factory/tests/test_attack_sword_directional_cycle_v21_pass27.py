from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass27 import (
    ALLOW_BLADE_OCCLUSION_BEHIND_HEAD,
    CORRECTION_PASS,
    MAX_RENDER_ATTEMPTS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SEARCH_DEPTH_BRANCHES,
    SEARCH_OFFSET_LIMIT_DEGREES,
    SEARCH_OFFSET_STEP_DEGREES,
    SEARCH_SCREEN_PROJECTIONS,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_SOLVER_REVISION,
)


class AttackSwordDirectionalCycleV21Pass27Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass27.py"
        ).read_text(encoding="utf-8")
        cls.launcher_source = (
            cls.tool_root / "run_blender_sprite_pilot.ps1"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_twohand_up_f01_solver_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass27")
        self.assertEqual(
            TWOHAND_UP_F01_SOLVER_REVISION,
            "twohand_up_f01_depth_aware_rigid_weapon_solver_v21_pass27",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAMES, (1,))
        self.assertEqual(SEARCH_DEPTH_BRANCHES, ("source", "flipped"))
        self.assertGreaterEqual(SEARCH_OFFSET_LIMIT_DEGREES, 90)
        self.assertLessEqual(SEARCH_OFFSET_STEP_DEGREES, 6)
        self.assertGreaterEqual(max(SEARCH_SCREEN_PROJECTIONS), 0.95)
        self.assertLessEqual(min(SEARCH_SCREEN_PROJECTIONS), 0.30)
        self.assertGreaterEqual(MAX_RENDER_ATTEMPTS, 8)
        self.assertGreaterEqual(
            MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
            1.0,
        )
        self.assertGreaterEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertTrue(ALLOW_BLADE_OCCLUSION_BEHIND_HEAD)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30774895237)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8841935284)

    def test_adapter_is_local_rigid_weapon_correction(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("BASE_RENDER_FRAME_PASS26", self.adapter_source)
        self.assertIn(
            "_depth_aware_visible_blade_head_clearance",
            self.adapter_source,
        )
        self.assertIn('depth_branch == "source"', self.adapter_source)
        self.assertIn('depth_branch == "flipped"', self.adapter_source)
        self.assertIn("TARGET_FRAMES", self.adapter_source)
        self.assertIn("rigid_weapon_transform_used", self.adapter_source)
        self.assertIn("action_data_changed", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_ci_and_windows_launcher_use_pass27(self) -> None:
        adapter_name = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass27.py"
        )
        self.assertIn(adapter_name, self.workflow_source)
        self.assertIn(adapter_name, self.launcher_source)
        self.assertIn("full directional cycle", self.workflow_source)
        self.assertIn(
            "attack_sword_01_directional_cycle_v21.png",
            self.launcher_source,
        )


if __name__ == "__main__":
    unittest.main()
