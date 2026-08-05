from __future__ import annotations

import ast
import math
import unittest
from dataclasses import fields
from pathlib import Path

from attack_sword_down_cycle_profile_v20 import (
    FULL_CYCLE_FPS,
    FULL_CYCLE_FRAME_ORDER,
    FULL_CYCLE_PHASE_ORDER,
    REBOUND_BLEND,
    SOURCE_KEYPOSE_REVISION,
    WINDUP_BLEND,
    load_attack_sword_down_cycle_profile_v20,
)
from attack_sword_down_keyposes_correction_v19_pass04 import (
    load_attack_sword_down_keyposes_profile_v19_pass04,
)
from attack_sword_down_keyposes_profile_v17 import AttackSwordDownPoseDeltaV17


class AttackSwordDownCycleV20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_attack_sword_down_cycle_profile_v20(
            "human_warrior_m01"
        )
        cls.source = load_attack_sword_down_keyposes_profile_v19_pass04(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_attack_sword_down_cycle_v20.py"
        ).read_text(encoding="utf-8")
        cls.builder_source = (
            cls.tool_root / "attack_sword_down_cycle_builder_v20.py"
        ).read_text(encoding="utf-8")

    @staticmethod
    def _numeric_values(pose: AttackSwordDownPoseDeltaV17) -> tuple[float, ...]:
        return tuple(
            float(getattr(pose, field_info.name))
            for field_info in fields(AttackSwordDownPoseDeltaV17)
            if field_info.name not in ("frame", "phase")
        )

    def test_profile_identity_and_timing(self) -> None:
        self.assertEqual(self.profile.revision, "v20")
        self.assertEqual(self.profile.animation_id, "attack_sword_01_down")
        self.assertEqual(self.profile.direction, "down")
        self.assertEqual(self.profile.fps, FULL_CYCLE_FPS)
        self.assertEqual(FULL_CYCLE_FPS, 12)
        self.assertFalse(self.profile.loop)
        self.assertEqual(self.profile.frame_order, FULL_CYCLE_FRAME_ORDER)
        self.assertEqual(self.profile.phase_order, FULL_CYCLE_PHASE_ORDER)
        self.assertEqual(SOURCE_KEYPOSE_REVISION, "v19_pass07_artist_approved")

    def test_action_ids_and_eight_frame_contract(self) -> None:
        onehand, twohand = self.profile.grips
        self.assertEqual(onehand.action_id, "attack_sword_01_onehand_down_v20")
        self.assertEqual(twohand.action_id, "attack_sword_01_twohand_down_v20")
        for grip in self.profile.grips:
            self.assertEqual(tuple(pose.frame for pose in grip.poses), tuple(range(1, 9)))
            self.assertEqual(
                tuple(pose.phase for pose in grip.poses),
                FULL_CYCLE_PHASE_ORDER,
            )

    def test_approved_v19_anchor_values_are_exactly_preserved(self) -> None:
        source_indices = (0, 1, 2, 3, 4, 0)
        expanded_indices = (0, 2, 3, 4, 6, 7)
        for source_grip, expanded_grip in zip(self.source.grips, self.profile.grips):
            for source_index, expanded_index in zip(source_indices, expanded_indices):
                self.assertEqual(
                    self._numeric_values(source_grip.poses[source_index]),
                    self._numeric_values(expanded_grip.poses[expanded_index]),
                )

    def test_intermediate_frames_are_bounded_interpolations(self) -> None:
        self.assertEqual(WINDUP_BLEND, 0.58)
        self.assertEqual(REBOUND_BLEND, 0.48)
        for source_grip, expanded_grip in zip(self.source.grips, self.profile.grips):
            guard, anticipation, _contact, follow, recovery = source_grip.poses
            windup = expanded_grip.poses[1]
            rebound = expanded_grip.poses[5]
            for field_info in fields(AttackSwordDownPoseDeltaV17):
                if field_info.name in ("frame", "phase"):
                    continue
                guard_value = float(getattr(guard, field_info.name))
                anticipation_value = float(getattr(anticipation, field_info.name))
                expected_windup = guard_value + (
                    anticipation_value - guard_value
                ) * WINDUP_BLEND
                self.assertTrue(
                    math.isclose(
                        float(getattr(windup, field_info.name)),
                        expected_windup,
                        rel_tol=0.0,
                        abs_tol=1.0e-9,
                    )
                )
                follow_value = float(getattr(follow, field_info.name))
                recovery_value = float(getattr(recovery, field_info.name))
                expected_rebound = follow_value + (
                    recovery_value - follow_value
                ) * REBOUND_BLEND
                self.assertTrue(
                    math.isclose(
                        float(getattr(rebound, field_info.name)),
                        expected_rebound,
                        rel_tol=0.0,
                        abs_tol=1.0e-9,
                    )
                )

    def test_adapter_preserves_geometry_and_checks_head_clearance(self) -> None:
        ast.parse(self.adapter_source)
        ast.parse(self.builder_source)
        self.assertIn("TWOHAND_PLANNED_CLEARANCE_FRAMES = (2, 3)", self.adapter_source)
        self.assertIn("TWOHAND_CLEARANCE_FRAMES = (2, 3, 4)", self.adapter_source)
        self.assertIn(
            "pass07_adapter._apply_clearance_planned_weapon_projection()",
            self.adapter_source,
        )
        self.assertIn("v19_base._twohand_head_clearance_pixels", self.adapter_source)
        self.assertIn("pass06_adapter._restore_weapon(saved_basis)", self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)

    def test_adapter_requires_sixteen_review_frames(self) -> None:
        self.assertIn("rendered_count != 16", self.adapter_source)
        self.assertIn('"total_rendered_frames": 16', self.adapter_source)
        self.assertIn("ONEHAND_GUARD_FAMILY_FRAMES = (1, 7, 8)", self.adapter_source)
        self.assertIn('"approved_v19_anchor_values_preserved": True', self.adapter_source)
        self.assertIn('"manual_full_cycle_review_required": True', self.adapter_source)
        self.assertIn('"runtime_connected": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
