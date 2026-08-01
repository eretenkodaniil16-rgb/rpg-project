from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_cycle_correction_v20_pass03 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_CONTAINMENT_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)


class AttackSwordDownCycleV20Pass03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_cycle_v20_pass03.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_locked_target(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v20_pass03")
        self.assertEqual(
            ONEHAND_CONTAINMENT_REVISION,
            "export_space_rigid_rotation_search_v20_pass03",
        )
        self.assertEqual(TARGET_ANIMATION_ID, "attack_sword_01_onehand_down_v20")
        self.assertEqual(TARGET_FRAME, 6)
        self.assertEqual(ANGLE_SEARCH_LIMIT_DEGREES, 40)
        self.assertEqual(ANGLE_SEARCH_STEP_DEGREES, 2)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)

    def test_adapter_validates_actual_normalized_png(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("factory._normalize_render", self.adapter_source)
        self.assertIn("keypose_adapter._edge_alpha_counts", self.adapter_source)
        self.assertIn("if not touched:", self.adapter_source)
        self.assertIn("_render_candidate", self.adapter_source)
        self.assertIn("ATTACK_SWORD_DOWN_CYCLE_V20_PASS03_ATTEMPT", self.adapter_source)
        self.assertIn("export_space_validated", self.adapter_source)

    def test_candidate_order_prefers_minimal_inward_rotation(self) -> None:
        self.assertIn("ordered: list[float] = [0.0]", self.adapter_source)
        self.assertIn("ANGLE_SEARCH_STEP_DEGREES", self.adapter_source)
        self.assertIn("_projected_min_x(objects)", self.adapter_source)
        self.assertIn("scored.sort(key=lambda item: (-item[0], item[1]))", self.adapter_source)
        self.assertIn("break", self.adapter_source)

    def test_rigid_transform_and_restoration_contract(self) -> None:
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon(saved_basis)", self.adapter_source)
        self.assertIn('"body_pose_changed": False', self.adapter_source)
        self.assertIn('"approved_v19_anchor_frames_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_all_other_cycle_frames_use_unchanged_v20_renderer(self) -> None:
        self.assertIn("BASE_RENDER_FRAME_V20", self.adapter_source)
        self.assertIn(
            "animation_id != TARGET_ANIMATION_ID or frame_number != TARGET_FRAME",
            self.adapter_source,
        )
        self.assertIn("return base_adapter.main()", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
