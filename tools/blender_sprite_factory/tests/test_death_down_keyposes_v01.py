from __future__ import annotations

import unittest
from pathlib import Path

from tools.blender_sprite_factory.death_down_keyposes_profile_v01 import (
    DEATH_DOWN_KEYPOSE_FRAME_ORDER,
    DEATH_DOWN_KEYPOSE_PHASE_ORDER,
    HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01,
    load_death_down_keyposes_profile_v01,
)


ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "tools" / "blender_sprite_factory" / "death_down_keyposes_profile_v01.py"
BUILDER_PATH = ROOT / "tools" / "blender_sprite_factory" / "death_down_keyposes_builder_v01.py"
ADAPTER_PATH = ROOT / "tools" / "blender_sprite_factory" / "blender_sprite_factory_death_down_keyposes_v01.py"


class DeathDownKeyposesV01Tests(unittest.TestCase):
    def test_profile_identity_is_locked(self) -> None:
        profile = load_death_down_keyposes_profile_v01("human_warrior_m01")
        self.assertEqual(profile, HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01)
        self.assertEqual(profile.revision, "death_down_keyposes_v01_pass01")
        self.assertEqual(profile.animation_id, "death_01_onehand_down_keyposes_v01")
        self.assertEqual(profile.direction, "down")
        self.assertEqual(profile.frame_order, DEATH_DOWN_KEYPOSE_FRAME_ORDER)
        self.assertEqual(profile.phase_order, DEATH_DOWN_KEYPOSE_PHASE_ORDER)
        self.assertEqual(profile.fps, 8)
        self.assertFalse(profile.loop)
        self.assertTrue(profile.final_pose_persistent)
        self.assertTrue(profile.weapon_release_deferred)

    def test_stage_is_onehand_down_only(self) -> None:
        profile = load_death_down_keyposes_profile_v01("human_warrior_m01")
        self.assertEqual(profile.stance_variant_id, "onehand_ready")
        self.assertEqual(profile.stance_source_revision, "v09_artist_approved")
        self.assertEqual(profile.weapon_cycle_id, "onehand_ready")
        self.assertEqual(profile.fall_side, "character_right_back_diagonal")
        self.assertEqual(profile.appearance_revision, "v03")
        self.assertEqual(profile.head_revision, "v22")
        self.assertEqual(profile.proxy_revision, "v25")

    def test_motion_progresses_from_guard_to_stable_ground_pose(self) -> None:
        profile = load_death_down_keyposes_profile_v01("human_warrior_m01")
        poses = profile.poses
        self.assertTrue(all(value == 0.0 for value in poses[0].translation_deltas()))
        self.assertTrue(all(value == 0.0 for value in poses[0].rotation_deltas()))
        self.assertEqual([pose.phase for pose in poses], list(profile.phase_order))
        self.assertEqual([pose.frame for pose in poses], list(profile.frame_order))

        pelvis_z = [pose.pelvis_z for pose in poses]
        self.assertEqual(pelvis_z, sorted(pelvis_z, reverse=True))
        self.assertLess(poses[-1].pelvis_z, -0.5)
        self.assertLess(poses[-1].spine_pitch_x_degrees, -60.0)
        self.assertLess(poses[-1].pelvis_roll_z_degrees, -45.0)
        self.assertGreater(poses[-1].shin_left_x_degrees, 65.0)
        self.assertNotEqual(
            poses[-1].upper_arm_left_z_degrees,
            -poses[-1].upper_arm_right_z_degrees,
        )

    def test_profile_rejects_unknown_character(self) -> None:
        with self.assertRaises(KeyError):
            load_death_down_keyposes_profile_v01("unknown_character")

    def test_builder_reuses_existing_pose_channel_contract(self) -> None:
        source = BUILDER_PATH.read_text(encoding="utf-8")
        self.assertIn("create_combat_idle_directional_cycles_v14", source)
        self.assertIn("_hit_channels", source)
        self.assertIn("_assert_rig_contract", source)
        self.assertIn('action["animation_family"] = "death_01"', source)
        self.assertIn('action["root_translation_used"] = False', source)
        self.assertIn('action["mirroring_used"] = False', source)
        self.assertIn('action["weapon_release_deferred"]', source)

    def test_renderer_writes_review_artifact_and_contract(self) -> None:
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_FRAME_NUMBERS = (1, 2, 3, 4, 5)", source)
        self.assertIn("human_warrior_m01_death_01_onehand_down_keyposes_v01.png", source)
        self.assertIn("baseline_y", source)
        self.assertIn("edge_alpha", source)
        self.assertIn('"down_keyposes_only": True', source)
        self.assertIn('"full_cycle_not_yet_approved": True', source)
        self.assertIn('"runtime_connected": False', source)

    def test_source_files_exist(self) -> None:
        self.assertTrue(PROFILE_PATH.is_file())
        self.assertTrue(BUILDER_PATH.is_file())
        self.assertTrue(ADAPTER_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
