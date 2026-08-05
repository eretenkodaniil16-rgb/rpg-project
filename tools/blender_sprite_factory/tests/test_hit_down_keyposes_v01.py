from __future__ import annotations

import ast
import unittest
from pathlib import Path

from hit_down_keyposes_profile_v01 import (
    HIT_DOWN_KEYPOSE_FRAME_ORDER,
    HIT_DOWN_KEYPOSE_PHASE_ORDER,
    MAX_PELVIS_TRANSLATION,
    MAX_ROTATION_DELTA_DEGREES,
    load_hit_down_keyposes_profile_v01,
)


class HitDownKeyposesV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_hit_down_keyposes_profile_v01("human_warrior_m01")
        cls.builder_source = (
            cls.tool_root / "hit_down_keyposes_builder_v01.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_hit_down_keyposes_v01.py"
        ).read_text(encoding="utf-8")

    def test_profile_identity_and_review_scope(self) -> None:
        self.assertEqual(self.profile.revision, "hit_down_keyposes_v01")
        self.assertEqual(self.profile.animation_id, "hit_01_onehand_down_keyposes_v01")
        self.assertEqual(self.profile.direction, "down")
        self.assertEqual(self.profile.incoming_direction, "front")
        self.assertEqual(self.profile.frame_order, HIT_DOWN_KEYPOSE_FRAME_ORDER)
        self.assertEqual(self.profile.phase_order, HIT_DOWN_KEYPOSE_PHASE_ORDER)
        self.assertEqual(self.profile.fps, 8)
        self.assertFalse(self.profile.loop)
        self.assertEqual(self.profile.stance_variant_id, "onehand_ready")
        self.assertEqual(self.profile.weapon_cycle_id, "onehand_ready")
        self.assertEqual(self.profile.appearance_revision, "v03")
        self.assertEqual(self.profile.head_revision, "v22")
        self.assertEqual(self.profile.proxy_revision, "v25")

    def test_guard_exactly_preserves_approved_stance(self) -> None:
        guard = self.profile.poses[0]
        self.assertEqual(guard.phase, "guard")
        self.assertTrue(all(value == 0.0 for value in guard.translation_deltas()))
        self.assertTrue(all(value == 0.0 for value in guard.rotation_deltas()))

    def test_recoil_is_short_readable_and_recovers(self) -> None:
        impact = self.profile.poses[1]
        peak = self.profile.poses[2]
        recovery = self.profile.poses[3]
        self.assertGreater(impact.pelvis_y, 0.0)
        self.assertGreater(peak.pelvis_y, impact.pelvis_y)
        self.assertGreater(peak.spine_pitch_x_degrees, impact.spine_pitch_x_degrees)
        self.assertGreater(peak.head_pitch_x_degrees, impact.head_pitch_x_degrees)
        self.assertLess(recovery.pelvis_y, impact.pelvis_y)
        self.assertLess(recovery.spine_pitch_x_degrees, impact.spine_pitch_x_degrees)
        self.assertLess(recovery.head_pitch_x_degrees, impact.head_pitch_x_degrees)
        self.assertLessEqual(
            max(
                abs(value)
                for pose in self.profile.poses
                for value in pose.translation_deltas()
            ),
            MAX_PELVIS_TRANSLATION,
        )
        self.assertLessEqual(
            max(
                abs(value)
                for pose in self.profile.poses
                for value in pose.rotation_deltas()
            ),
            MAX_ROTATION_DELTA_DEGREES,
        )

    def test_motion_keeps_feet_and_weapon_under_control(self) -> None:
        for pose in self.profile.poses:
            self.assertLessEqual(abs(pose.foot_left_x_degrees), 1.0)
            self.assertLessEqual(abs(pose.foot_right_x_degrees), 1.0)
            self.assertLessEqual(abs(pose.hand_right_z_degrees), 4.0)
            self.assertLessEqual(abs(pose.upper_arm_right_z_degrees), 5.0)
        self.assertGreater(self.profile.poses[2].upper_arm_left_z_degrees, 0.0)
        self.assertLess(self.profile.poses[2].upper_arm_right_z_degrees, 0.0)

    def test_builder_reuses_approved_onehand_stance(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_combat_idle_directional_cycles_v14(context)",
            self.builder_source,
        )
        self.assertIn("load_weapon_stance_profile_v09", self.builder_source)
        self.assertIn('action["shared_reaction_motion"] = True', self.builder_source)
        self.assertIn('action["root_translation_used"] = False', self.builder_source)
        self.assertIn('action["mirroring_used"] = False', self.builder_source)
        self.assertIn('action["geometry_changed"] = False', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_renders_only_four_down_keyposes(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("create_hit_down_keypose_actions_v01", self.adapter_source)
        self.assertIn("render_hit_down_keyposes_v01", self.adapter_source)
        self.assertIn("len(artifacts) != 4", self.adapter_source)
        self.assertIn(
            'weapon_adapter._set_v12_weapon(profile.weapon_cycle_id, "down")',
            self.adapter_source,
        )
        self.assertIn(
            'CONTACT_SHEET_NAME = "human_warrior_m01_hit_01_onehand_down_keyposes_v01.png"',
            self.adapter_source,
        )
        self.assertIn('"manual_keypose_review_required": True', self.adapter_source)
        self.assertIn('"full_hit_cycle_not_yet_approved": True', self.adapter_source)
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
