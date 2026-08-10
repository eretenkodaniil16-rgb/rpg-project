from __future__ import annotations

import unittest
from pathlib import Path

from tools.blender_sprite_factory.death_down_cycle_profile_v01 import (
    APPROVED_ANCHOR_FRAMES,
    CORPSE_HOLD_FRAME,
    DEATH_DOWN_CYCLE_DURATION_SECONDS,
    DEATH_DOWN_CYCLE_FPS,
    DEATH_DOWN_CYCLE_FRAME_ORDER,
    DEATH_DOWN_CYCLE_PHASE_ORDER,
    DETACHMENT_CYCLE_FRAME,
    INTERPOLATED_FRAMES,
    SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME,
    SOURCE_KEYPOSE_REVISIONS,
    load_death_down_cycle_profile_v01,
    load_death_down_cycle_profiles_v01,
)
from tools.blender_sprite_factory.death_down_keyposes_profile_v01 import (
    DEATH_DOWN_KEYPOSE_FRAME_ORDER,
    DEATH_DOWN_VARIANT_IDS,
    load_death_down_keyposes_profile_v01,
)


ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "tools" / "blender_sprite_factory" / "death_down_cycle_profile_v01.py"
BUILDER_PATH = ROOT / "tools" / "blender_sprite_factory" / "death_down_cycle_builder_v01.py"
ADAPTER_PATH = (
    ROOT
    / "tools"
    / "blender_sprite_factory"
    / "blender_sprite_factory_death_down_cycle_v01.py"
)
DOC_PATH = ROOT / "docs" / "HUMAN_WARRIOR_DEATH_DOWN_CYCLES_V01.md"


class DeathDownCycleV01Tests(unittest.TestCase):
    def test_three_full_weapon_agnostic_cycles_are_locked(self) -> None:
        profiles = load_death_down_cycle_profiles_v01("human_warrior_m01")
        self.assertEqual(
            tuple(profile.death_variant_id for profile in profiles),
            DEATH_DOWN_VARIANT_IDS,
        )
        self.assertEqual(len(profiles), 3)
        for profile in profiles:
            self.assertEqual(profile.direction, "down")
            self.assertEqual(profile.frame_order, DEATH_DOWN_CYCLE_FRAME_ORDER)
            self.assertEqual(profile.phase_order, DEATH_DOWN_CYCLE_PHASE_ORDER)
            self.assertEqual(profile.fps, DEATH_DOWN_CYCLE_FPS)
            self.assertFalse(profile.loop)
            self.assertFalse(profile.weapon_visible)
            self.assertTrue(profile.final_pose_persistent)
            self.assertEqual(
                tuple(pose.frame for pose in profile.poses),
                DEATH_DOWN_CYCLE_FRAME_ORDER,
            )
            self.assertEqual(
                tuple(pose.phase for pose in profile.poses),
                DEATH_DOWN_CYCLE_PHASE_ORDER,
            )
        self.assertAlmostEqual(DEATH_DOWN_CYCLE_DURATION_SECONDS, 0.8)

    def test_all_source_keypose_anchors_are_preserved_exactly(self) -> None:
        for cycle in load_death_down_cycle_profiles_v01("human_warrior_m01"):
            source = load_death_down_keyposes_profile_v01(
                "human_warrior_m01",
                cycle.death_variant_id,
            )
            source_by_frame = {pose.frame: pose for pose in source.poses}
            cycle_by_frame = {pose.frame: pose for pose in cycle.poses}
            for cycle_frame, source_frame in (
                SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME.items()
            ):
                source_pose = source_by_frame[source_frame]
                cycle_pose = cycle_by_frame[cycle_frame]
                self.assertEqual(
                    source_pose.translation_deltas(),
                    cycle_pose.translation_deltas(),
                )
                self.assertEqual(
                    source_pose.rotation_deltas(),
                    cycle_pose.rotation_deltas(),
                )
            self.assertEqual(
                SOURCE_KEYPOSE_REVISIONS[cycle.death_variant_id],
                source.revision,
            )
        self.assertEqual(APPROVED_ANCHOR_FRAMES, (1, 3, 4, 6, 7, 8))
        self.assertEqual(INTERPOLATED_FRAMES, (2, 5))

    def test_interpolated_frames_stay_between_their_source_poses(self) -> None:
        for cycle in load_death_down_cycle_profiles_v01("human_warrior_m01"):
            poses = {pose.frame: pose for pose in cycle.poses}
            for attribute, start_frame, middle_frame, end_frame in (
                ("pelvis_z", 1, 2, 3),
                ("pelvis_z", 4, 5, 6),
            ):
                start = float(getattr(poses[start_frame], attribute))
                middle = float(getattr(poses[middle_frame], attribute))
                end = float(getattr(poses[end_frame], attribute))
                self.assertGreaterEqual(middle, min(start, end))
                self.assertLessEqual(middle, max(start, end))
                self.assertNotEqual(middle, start)
                self.assertNotEqual(middle, end)

    def test_final_frame_is_held_without_pose_drift(self) -> None:
        self.assertEqual(CORPSE_HOLD_FRAME, 8)
        for profile in load_death_down_cycle_profiles_v01("human_warrior_m01"):
            final = profile.poses[6]
            hold = profile.poses[7]
            self.assertEqual(final.translation_deltas(), hold.translation_deltas())
            self.assertEqual(final.rotation_deltas(), hold.rotation_deltas())

    def test_death_03_separates_on_impact_and_remains_distinct(self) -> None:
        death_03 = load_death_down_cycle_profile_v01(
            "human_warrior_m01",
            "death_03_base",
        )
        self.assertEqual(death_03.gore_mode, "waist_torso_legs_separation")
        self.assertEqual(death_03.detached_part_id, "upper_torso_and_lower_body")
        self.assertEqual(death_03.detachment_frame, DETACHMENT_CYCLE_FRAME)
        self.assertEqual(DEATH_DOWN_CYCLE_PHASE_ORDER[DETACHMENT_CYCLE_FRAME - 1], "ground_impact")
        death_01 = load_death_down_cycle_profile_v01(
            "human_warrior_m01",
            "death_01_base",
        )
        self.assertNotEqual(
            death_03.poses[-1].translation_deltas(),
            death_01.poses[-1].translation_deltas(),
        )
        self.assertNotEqual(
            death_03.poses[-1].rotation_deltas(),
            death_01.poses[-1].rotation_deltas(),
        )

    def test_keypose_source_contract_is_not_modified(self) -> None:
        for death_variant_id in DEATH_DOWN_VARIANT_IDS:
            source = load_death_down_keyposes_profile_v01(
                "human_warrior_m01",
                death_variant_id,
            )
            self.assertEqual(source.frame_order, DEATH_DOWN_KEYPOSE_FRAME_ORDER)
            if death_variant_id == "death_03_base":
                self.assertEqual(source.detachment_frame, 4)

    def test_profile_rejects_unknown_identifiers(self) -> None:
        with self.assertRaises(KeyError):
            load_death_down_cycle_profiles_v01("unknown_character")
        with self.assertRaises(KeyError):
            load_death_down_cycle_profile_v01(
                "human_warrior_m01",
                "death_99_base",
            )

    def test_builder_marks_review_only_full_cycles(self) -> None:
        source = BUILDER_PATH.read_text(encoding="utf-8")
        self.assertIn("create_death_down_keypose_actions_v01", source)
        self.assertIn('action["animation_revision"] = "full_cycle_v01"', source)
        self.assertIn('action["manual_keypose_review_required"] = False', source)
        self.assertIn('action["manual_full_cycle_review_required"] = True', source)
        self.assertIn('action["runtime_connected"] = False', source)
        self.assertIn('scene["death_down_cycle_action_count"]', source)

    def test_renderer_reuses_verified_separation_without_new_geometry(self) -> None:
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        self.assertIn("DEATH_DOWN_CYCLE_FRAME_ORDER", source)
        self.assertIn("_cycle_adapter_contract", source)
        self.assertIn("_BASE_WAIST_PIXEL_SEAM(4)", source)
        self.assertIn("_BASE_WAIST_PIXEL_SEAM(5)", source)
        self.assertIn("_BASE_UPPER_BODY_OFFSET(4)", source)
        self.assertIn("_BASE_UPPER_BODY_OFFSET(5)", source)
        self.assertIn("_assert_corpse_hold", source)
        self.assertIn("human_warrior_m01_death_base_down_cycles_v01.png", source)
        self.assertIn('"runtime_connected": False', source)
        self.assertNotIn("_ellipsoid(", source)

    def test_source_files_exist(self) -> None:
        self.assertTrue(PROFILE_PATH.is_file())
        self.assertTrue(BUILDER_PATH.is_file())
        self.assertTrue(ADAPTER_PATH.is_file())
        self.assertTrue(DOC_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
