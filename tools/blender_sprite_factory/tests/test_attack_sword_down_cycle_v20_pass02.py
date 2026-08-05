from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_cycle_correction_v20_pass02 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_CONTAINMENT_REVISION,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)


class AttackSwordDownCycleV20Pass02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_cycle_v20_pass02.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_target_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v20_pass02")
        self.assertEqual(
            ONEHAND_CONTAINMENT_REVISION,
            "minimal_rigid_inward_rotation_v20_pass02",
        )
        self.assertEqual(TARGET_ANIMATION_ID, "attack_sword_01_onehand_down_v20")
        self.assertEqual(TARGET_FRAME, 6)
        self.assertEqual(ANGLE_SEARCH_LIMIT_DEGREES, 40)
        self.assertEqual(ANGLE_SEARCH_STEP_DEGREES, 2)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)

    def test_adapter_searches_minimal_contained_rigid_rotation(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("ONE_HAND_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass07_adapter._weapon_camera_margin", self.adapter_source)
        self.assertIn("v19_base._segment_rect_distance", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon(saved_basis)", self.adapter_source)
        self.assertIn("abs(float(item[\"offset_degrees\"]))", self.adapter_source)
        self.assertIn("MIN_CAMERA_MARGIN_PIXELS", self.adapter_source)
        self.assertIn("MIN_HEAD_CLEARANCE_PIXELS", self.adapter_source)

    def test_adapter_changes_only_rendered_weapon_transform(self) -> None:
        self.assertIn('"body_pose_changed": False', self.adapter_source)
        self.assertIn('"approved_v19_anchor_frames_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_adapter_preserves_base_cycle_for_all_other_frames(self) -> None:
        self.assertIn("BASE_RENDER_FRAME_V20", self.adapter_source)
        self.assertIn(
            "animation_id != TARGET_ANIMATION_ID or frame_number != TARGET_FRAME",
            self.adapter_source,
        )
        self.assertIn("return base_adapter.main()", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
