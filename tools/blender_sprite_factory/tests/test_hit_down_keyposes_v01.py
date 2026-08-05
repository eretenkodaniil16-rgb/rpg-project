from __future__ import annotations

import ast
import unittest
from dataclasses import fields
from pathlib import Path

from hit_down_cycle_profile_v01 import (
    HIT_DOWN_CYCLE_DURATION_SECONDS,
    HIT_DOWN_CYCLE_FPS,
    HIT_DOWN_CYCLE_FRAME_ORDER,
    HIT_DOWN_CYCLE_PHASE_ORDER,
    RELEASE_BLEND_TO_RECOVERY,
    SETTLE_BLEND_TO_GUARD,
    load_hit_down_cycle_profile_v01,
)
from hit_down_keyposes_profile_v01 import (
    MAX_PELVIS_TRANSLATION,
    MAX_ROTATION_DELTA_DEGREES,
    HitDownPoseDeltaV01,
    load_hit_down_keyposes_profile_v01,
)
from hit_down_twohand_cycle_profile_v01 import (
    TWOHAND_ARM_RESPONSE_SCALE,
    TWOHAND_STANCE_VARIANT_ID,
    load_hit_down_twohand_cycle_profile_v01,
)


class HitDownCycleV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.keyposes = load_hit_down_keyposes_profile_v01("human_warrior_m01")
        cls.onehand = load_hit_down_cycle_profile_v01("human_warrior_m01")
        cls.twohand = load_hit_down_twohand_cycle_profile_v01("human_warrior_m01")
        cls.builder_source = (
            cls.tool_root / "hit_down_keyposes_builder_v01.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_hit_down_keyposes_v01.py"
        ).read_text(encoding="utf-8")

    @staticmethod
    def _numeric_values(pose: HitDownPoseDeltaV01) -> tuple[float, ...]:
        return tuple(
            float(getattr(pose, field.name))
            for field in fields(HitDownPoseDeltaV01)
            if field.name not in {"frame", "phase"}
        )

    def test_onehand_profile_identity_and_cycle_scope(self) -> None:
        self.assertEqual(
            self.onehand.revision,
            "hit_down_cycle_v01_from_keyposes_pass02",
        )
        self.assertEqual(self.onehand.source_keypose_revision, self.keyposes.revision)
        self.assertEqual(self.onehand.animation_id, "hit_01_onehand_down_v01")
        self.assertEqual(self.onehand.direction, "down")
        self.assertEqual(self.onehand.incoming_direction, "front")
        self.assertEqual(self.onehand.frame_order, HIT_DOWN_CYCLE_FRAME_ORDER)
        self.assertEqual(self.onehand.phase_order, HIT_DOWN_CYCLE_PHASE_ORDER)
        self.assertEqual(self.onehand.fps, HIT_DOWN_CYCLE_FPS)
        self.assertAlmostEqual(HIT_DOWN_CYCLE_DURATION_SECONDS, 0.4)
        self.assertFalse(self.onehand.loop)
        self.assertEqual(self.onehand.stance_variant_id, "onehand_ready")
        self.assertEqual(self.onehand.weapon_cycle_id, "onehand_ready")

    def test_approved_onehand_keyposes_are_preserved_exactly(self) -> None:
        guard, impact, recoil_peak, recovery = self.keyposes.poses
        cycle = self.onehand.poses
        self.assertEqual(self._numeric_values(cycle[0]), self._numeric_values(impact))
        self.assertEqual(self._numeric_values(cycle[1]), self._numeric_values(recoil_peak))
        self.assertEqual(self._numeric_values(cycle[3]), self._numeric_values(recovery))
        self.assertEqual(self._numeric_values(cycle[5]), self._numeric_values(guard))
        self.assertGreater(cycle[0].pelvis_y, 0.0)
        self.assertTrue(all(value == 0.0 for value in cycle[5].translation_deltas()))
        self.assertTrue(all(value == 0.0 for value in cycle[5].rotation_deltas()))

    def test_onehand_intermediate_frames_stay_between_approved_poses(self) -> None:
        guard, _, recoil_peak, recovery = self.keyposes.poses
        release_mid = self.onehand.poses[2]
        settle = self.onehand.poses[4]
        for peak_value, recovery_value, release_value in zip(
            self._numeric_values(recoil_peak),
            self._numeric_values(recovery),
            self._numeric_values(release_mid),
        ):
            self.assertGreaterEqual(release_value, min(peak_value, recovery_value))
            self.assertLessEqual(release_value, max(peak_value, recovery_value))
        for recovery_value, guard_value, settle_value in zip(
            self._numeric_values(recovery),
            self._numeric_values(guard),
            self._numeric_values(settle),
        ):
            self.assertGreaterEqual(settle_value, min(recovery_value, guard_value))
            self.assertLessEqual(settle_value, max(recovery_value, guard_value))
        self.assertGreater(RELEASE_BLEND_TO_RECOVERY, 0.5)
        self.assertGreater(SETTLE_BLEND_TO_GUARD, 0.5)

    def test_twohand_profile_preserves_body_motion_and_grip_symmetry(self) -> None:
        self.assertEqual(
            self.twohand.revision,
            "hit_down_twohand_cycle_v01_from_onehand_motion_pass01",
        )
        self.assertEqual(self.twohand.animation_id, "hit_01_twohand_down_v01")
        self.assertEqual(self.twohand.stance_variant_id, TWOHAND_STANCE_VARIANT_ID)
        self.assertEqual(self.twohand.weapon_cycle_id, TWOHAND_STANCE_VARIANT_ID)
        self.assertEqual(self.twohand.frame_order, self.onehand.frame_order)
        self.assertEqual(self.twohand.phase_order, self.onehand.phase_order)
        self.assertEqual(self.twohand.fps, self.onehand.fps)
        self.assertGreater(TWOHAND_ARM_RESPONSE_SCALE, 0.0)
        self.assertLessEqual(TWOHAND_ARM_RESPONSE_SCALE, 0.4)

        arm_fields = {
            name
            for name in (field.name for field in fields(HitDownPoseDeltaV01))
            if name.startswith(("upper_arm_", "forearm_", "hand_"))
        }
        for source, adapted in zip(self.onehand.poses, self.twohand.poses):
            for field in fields(HitDownPoseDeltaV01):
                if field.name in {"frame", "phase"} or field.name in arm_fields:
                    continue
                self.assertEqual(
                    getattr(source, field.name),
                    getattr(adapted, field.name),
                    field.name,
                )
            self.assertEqual(
                adapted.upper_arm_left_x_degrees,
                adapted.upper_arm_right_x_degrees,
            )
            self.assertEqual(
                adapted.forearm_left_x_degrees,
                adapted.forearm_right_x_degrees,
            )
            self.assertEqual(
                adapted.hand_left_x_degrees,
                adapted.hand_right_x_degrees,
            )
            self.assertEqual(
                adapted.upper_arm_left_z_degrees,
                -adapted.upper_arm_right_z_degrees,
            )
            self.assertEqual(
                adapted.forearm_left_z_degrees,
                -adapted.forearm_right_z_degrees,
            )
            self.assertEqual(
                adapted.hand_left_z_degrees,
                -adapted.hand_right_z_degrees,
            )

    def test_motion_budgets_remain_under_control(self) -> None:
        for profile in (self.onehand, self.twohand):
            for pose in profile.poses:
                self.assertLessEqual(abs(pose.foot_left_x_degrees), 1.0)
                self.assertLessEqual(abs(pose.foot_right_x_degrees), 1.0)
            self.assertLessEqual(
                max(
                    abs(value)
                    for pose in profile.poses
                    for value in pose.translation_deltas()
                ),
                MAX_PELVIS_TRANSLATION,
            )
            self.assertLessEqual(
                max(
                    abs(value)
                    for pose in profile.poses
                    for value in pose.rotation_deltas()
                ),
                MAX_ROTATION_DELTA_DEGREES,
            )

    def test_builder_creates_two_grip_actions_without_parallel_base(self) -> None:
        ast.parse(self.builder_source)
        self.assertEqual(
            self.builder_source.count("create_combat_idle_directional_cycles_v14(context)"),
            1,
        )
        self.assertIn("load_weapon_stance_profile_v09", self.builder_source)
        self.assertIn("load_hit_down_twohand_cycle_profile_v01", self.builder_source)
        self.assertIn('action["grip_mode"] = stance.grip_mode', self.builder_source)
        self.assertIn('action["approved_body_motion_preserved_exactly"] = True', self.builder_source)
        self.assertIn('action["twohand_grip_preservation_adjustment"] = not is_onehand', self.builder_source)
        self.assertIn('action["root_translation_used"] = False', self.builder_source)
        self.assertIn('action["mirroring_used"] = False', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_renders_twelve_frames_and_two_rows(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("load_hit_down_twohand_cycle_profile_v01", self.adapter_source)
        self.assertIn("expected_count = len(profiles) * len(EXPECTED_FRAME_NUMBERS)", self.adapter_source)
        self.assertIn(
            'weapon_adapter._set_v12_weapon(profile.weapon_cycle_id, "down")',
            self.adapter_source,
        )
        self.assertIn(
            'CONTACT_SHEET_NAME = "human_warrior_m01_hit_01_down_grips_v01.png"',
            self.adapter_source,
        )
        self.assertIn('"hit_01_grip_count": len(profiles)', self.adapter_source)
        self.assertIn('"hit_01_total_frame_count": len(artifacts)', self.adapter_source)
        self.assertIn('"runtime_connected": False', self.adapter_source)

    def test_manifest_uses_unpatched_base_writer(self) -> None:
        self.assertIn(
            "BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest",
            self.adapter_source,
        )
        self.assertIn(
            "manifest_path = BASE_WRITE_RUN_MANIFEST(",
            self.adapter_source,
        )
        self.assertNotIn(
            "manifest_path = factory._write_run_manifest(",
            self.adapter_source,
        )
        self.assertIn('"base_manifest_writer_restored": True', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
