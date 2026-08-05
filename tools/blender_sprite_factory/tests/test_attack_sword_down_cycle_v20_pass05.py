from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_cycle_correction_v20_pass05 import (
    ACTIVE_BLADE_OBJECT_NAME,
    ACTIVE_GRIP_OBJECT_NAME,
    ACTIVE_WEAPON_SOURCE_REVISION,
    ACTIVE_WEAPON_VARIANT_ID,
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    DIAGNOSTIC_ARTIFACT_IDS,
    DIAGNOSTIC_RUN_IDS,
    MIN_HEAD_CLEARANCE_PIXELS,
    MISIDENTIFIED_WEAPON_SOURCE_REVISION,
    ONEHAND_CONTAINMENT_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)


class AttackSwordDownCycleV20Pass05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_cycle_v20_pass05.py"
        ).read_text(encoding="utf-8")
        cls.weapon_builder_source = (
            cls.tool_root / "combat_idle_down_weapon_variants_builder_v09.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_active_weapon_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v20_pass05")
        self.assertEqual(
            ONEHAND_CONTAINMENT_REVISION,
            "active_v09_export_space_rotation_v20_pass05",
        )
        self.assertEqual(TARGET_ANIMATION_ID, "attack_sword_01_onehand_down_v20")
        self.assertEqual(TARGET_FRAME, 6)
        self.assertEqual(ACTIVE_WEAPON_VARIANT_ID, "onehand_ready")
        self.assertEqual(ACTIVE_WEAPON_SOURCE_REVISION, "v09")
        self.assertEqual(MISIDENTIFIED_WEAPON_SOURCE_REVISION, "v06")
        self.assertEqual(ACTIVE_BLADE_OBJECT_NAME, "combat_onehand_ready_v09_blade")
        self.assertEqual(ACTIVE_GRIP_OBJECT_NAME, "combat_onehand_ready_v09_grip")
        self.assertIn(f'"{ACTIVE_BLADE_OBJECT_NAME}"', self.weapon_builder_source)
        self.assertIn(f'"{ACTIVE_GRIP_OBJECT_NAME}"', self.weapon_builder_source)

    def test_search_and_safety_contract(self) -> None:
        self.assertEqual(ANGLE_SEARCH_LIMIT_DEGREES, 40)
        self.assertEqual(ANGLE_SEARCH_STEP_DEGREES, 2)
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)
        self.assertEqual(len(DIAGNOSTIC_RUN_IDS), len(DIAGNOSTIC_ARTIFACT_IDS))
        self.assertIn(30720688002, DIAGNOSTIC_RUN_IDS)
        self.assertIn(8824976123, DIAGNOSTIC_ARTIFACT_IDS)

    def test_adapter_targets_visible_v09_objects_only(self) -> None:
        ast.parse(self.adapter_source)
        ast.parse(self.weapon_builder_source)
        self.assertIn("ONE_HAND_READY_V09_OBJECT_NAMES", self.adapter_source)
        self.assertIn("ACTIVE_BLADE_OBJECT_NAME", self.adapter_source)
        self.assertIn("ACTIVE_GRIP_OBJECT_NAME", self.adapter_source)
        self.assertIn("if obj.hide_render:", self.adapter_source)
        self.assertNotIn('factory.bpy.data.objects.get("combat_onehand_v06_grip")', self.adapter_source)
        self.assertNotIn('factory.bpy.data.objects.get("combat_onehand_v06_blade")', self.adapter_source)

    def test_adapter_validates_actual_export_and_head_clearance(self) -> None:
        self.assertIn("export_adapter._render_candidate", self.adapter_source)
        self.assertIn("keypose_adapter._edge_alpha_counts", self.adapter_source)
        self.assertIn("export_adapter._weapon_head_clearance(objects)", self.adapter_source)
        self.assertIn("if not touched:", self.adapter_source)
        self.assertIn("ATTACK_SWORD_DOWN_CYCLE_V20_PASS05_SELECTED", self.adapter_source)
        self.assertIn('"export_space_validated": True', self.adapter_source)

    def test_adapter_uses_rigid_transform_and_restores_module(self) -> None:
        self.assertIn("pass07_adapter._apply_world_rotation", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon(saved_basis)", self.adapter_source)
        self.assertIn('"body_pose_changed": False', self.adapter_source)
        self.assertIn('"approved_v19_anchor_frames_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("mesh.vertices", self.adapter_source)

    def test_all_other_frames_keep_base_v20_renderer(self) -> None:
        self.assertIn("BASE_RENDER_FRAME_V20", self.adapter_source)
        self.assertIn(
            "animation_id != TARGET_ANIMATION_ID or frame_number != TARGET_FRAME",
            self.adapter_source,
        )
        self.assertIn("return base_adapter.main()", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
