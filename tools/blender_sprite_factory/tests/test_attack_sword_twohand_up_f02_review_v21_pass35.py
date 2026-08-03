from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass35 import (
    ALLOW_ZERO_SCREEN_GAP_WHEN_BLADE_IS_VISIBLE,
    CORRECTION_PASS,
    MAX_REFERENCE_RIGHT_EDGE_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    PREFER_SOURCE_DEPTH_BRANCH,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION,
)


class AttackSwordTwohandUpF02ReviewV21Pass35Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f02_review_v21_pass35.py"
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

    def test_rear_view_occlusion_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass35")
        self.assertEqual(
            TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION,
            "twohand_up_f02_rear_view_occlusion_continuity_review_v21_pass35",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAMES, (1, 2, 3))
        self.assertEqual(MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS, 0.0)
        self.assertGreaterEqual(MIN_VISIBLE_BLADE_SAMPLES, 8)
        self.assertTrue(ALLOW_ZERO_SCREEN_GAP_WHEN_BLADE_IS_VISIBLE)
        self.assertTrue(PREFER_SOURCE_DEPTH_BRANCH)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA_FOR_CANDIDATES)
        self.assertEqual(MAX_REFERENCE_RIGHT_EDGE_PIXELS, 4)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30854585534)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8872057458)

    def test_adapter_is_non_destructive_and_restores_history(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_candidate_sort_key_v21_pass35", self.adapter_source)
        self.assertIn("_render_original_f03_reference_v21_pass35", self.adapter_source)
        self.assertIn("pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS", self.adapter_source)
        self.assertIn("_restore_pass34_contract", self.adapter_source)
        self.assertIn("depth_branch", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass35_and_retains_pass34(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("rear-view", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f02_review_v21_pass34.py",
            self.workflow_source,
        )
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
