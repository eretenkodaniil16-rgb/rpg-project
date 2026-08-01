from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_keyposes_correction_v19_pass07 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    TARGET_HEAD_CLEARANCE_PIXELS,
    TWOHAND_ANTICIPATION_REVISION,
    WEAPON_SCREEN_PROJECTION_MAGNITUDE,
)


class AttackSwordDownKeyposesV19Pass07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass07.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_search_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v19_pass07")
        self.assertEqual(
            TWOHAND_ANTICIPATION_REVISION,
            "clearance_planned_rigid_arc_v19_pass07",
        )
        self.assertEqual(WEAPON_SCREEN_PROJECTION_MAGNITUDE, 0.74)
        self.assertEqual(ANGLE_SEARCH_LIMIT_DEGREES, 80)
        self.assertEqual(ANGLE_SEARCH_STEP_DEGREES, 5)
        self.assertEqual(MIN_CAMERA_MARGIN_PIXELS, 1.0)
        self.assertEqual(TARGET_HEAD_CLEARANCE_PIXELS, 6.0)

    def test_adapter_searches_head_safe_camera_contained_candidates(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_actual_weapon_head_clearance", self.adapter_source)
        self.assertIn("_weapon_camera_margin", self.adapter_source)
        self.assertIn("ANGLE_SEARCH_LIMIT_DEGREES", self.adapter_source)
        self.assertIn("ANGLE_SEARCH_STEP_DEGREES", self.adapter_source)
        self.assertIn("TARGET_HEAD_CLEARANCE_PIXELS", self.adapter_source)
        self.assertIn("MIN_CAMERA_MARGIN_PIXELS", self.adapter_source)
        self.assertIn("candidate_x >= -0.05", self.adapter_source)
        self.assertIn("candidate_y <= -0.35", self.adapter_source)
        self.assertIn("max(valid, key=lambda item: float(item[\"score\"]))", self.adapter_source)

    def test_adapter_uses_rigid_group_and_actual_clearance_validator(self) -> None:
        self.assertIn("previous_adapter._weapon_objects()", self.adapter_source)
        self.assertIn("transform @ obj.matrix_world", self.adapter_source)
        self.assertIn("previous_adapter._restore_weapon(saved_basis)", self.adapter_source)
        self.assertIn("v19_base._segment_rect_distance", self.adapter_source)
        self.assertIn("v19_base.TWOHAND_WEAPON_OBJECT_NAMES", self.adapter_source)
        self.assertIn("previous_adapter._apply_rigid_weapon_depth_projection", self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)

    def test_adapter_preserves_locked_character_contracts(self) -> None:
        self.assertIn('"onehand_v19_pass03_unchanged": True', self.adapter_source)
        self.assertIn('"twohand_pose_source": "v19_pass04"', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertIn('"approved_guard_frames_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
