from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass28 import (
    CORRECTION_PASS,
    FALLBACK_ERROR_PREFIXES,
    FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_UP_FALLBACK_REVISION,
    USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD,
)


class AttackSwordDirectionalCycleV21Pass28Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py"
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

    def test_on_demand_fallback_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass28")
        self.assertEqual(
            TWOHAND_UP_FALLBACK_REVISION,
            "twohand_up_on_demand_depth_search_v21_pass28",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAMES, tuple(range(1, 9)))
        self.assertEqual(len(FALLBACK_ERROR_PREFIXES), 2)
        self.assertTrue(FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED)
        self.assertTrue(USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30847584866)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8870099701)

    def test_adapter_uses_base_first_and_local_solver_only_on_failure(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("pass27_adapter.BASE_RENDER_FRAME_PASS26", self.adapter_source)
        self.assertIn("except RuntimeError as error", self.adapter_source)
        self.assertIn("_is_fallback_error", self.adapter_source)
        self.assertIn("ORIGINAL_PASS27_RENDER", self.adapter_source)
        self.assertIn(
            "pass23_adapter._depth_search_visible_blade_head_clearance",
            self.adapter_source,
        )
        self.assertIn("pass28_on_demand_fallback", self.adapter_source)
        self.assertIn("action_data_changed", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_ci_and_windows_launcher_use_pass28(self) -> None:
        adapter_name = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py"
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
