from __future__ import annotations

import unittest
from pathlib import Path

from tools.blender_sprite_factory.death_down_keyposes_profile_v01 import (
    DEATH_DOWN_KEYPOSE_FRAME_ORDER,
    DEATH_DOWN_KEYPOSE_PHASE_ORDER,
    DEATH_DOWN_VARIANT_IDS,
    HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01,
    load_death_down_keyposes_profile_v01,
    load_death_down_keyposes_profiles_v01,
)


ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "tools" / "blender_sprite_factory" / "death_down_keyposes_profile_v01.py"
BUILDER_PATH = ROOT / "tools" / "blender_sprite_factory" / "death_down_keyposes_builder_v01.py"
ADAPTER_PATH = ROOT / "tools" / "blender_sprite_factory" / "blender_sprite_factory_death_down_keyposes_v01.py"


class DeathDownKeyposesV01Tests(unittest.TestCase):
    def test_three_weapon_agnostic_variants_are_locked(self) -> None:
        profiles = load_death_down_keyposes_profiles_v01("human_warrior_m01")
        self.assertEqual(profiles, HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01)
        self.assertEqual(
            tuple(profile.death_variant_id for profile in profiles),
            DEATH_DOWN_VARIANT_IDS,
        )
        self.assertEqual(len(profiles), 3)
        self.assertTrue(all(not profile.weapon_visible for profile in profiles))
        self.assertTrue(
            all(profile.source_stance_variant_id == "onehand_ready" for profile in profiles)
        )
        self.assertTrue(
            all(profile.source_stance_revision.endswith("source_only") for profile in profiles)
        )

    def test_shared_keypose_contract(self) -> None:
        for profile in load_death_down_keyposes_profiles_v01("human_warrior_m01"):
            self.assertEqual(profile.direction, "down")
            self.assertEqual(profile.frame_order, DEATH_DOWN_KEYPOSE_FRAME_ORDER)
            self.assertEqual(profile.phase_order, DEATH_DOWN_KEYPOSE_PHASE_ORDER)
            self.assertEqual(profile.fps, 8)
            self.assertFalse(profile.loop)
            self.assertTrue(profile.final_pose_persistent)
            self.assertEqual(profile.appearance_revision, "v03")
            self.assertEqual(profile.head_revision, "v22")
            self.assertEqual(profile.proxy_revision, "v25")
            self.assertEqual([pose.phase for pose in profile.poses], list(profile.phase_order))
            self.assertEqual([pose.frame for pose in profile.poses], list(profile.frame_order))
            self.assertTrue(all(value == 0.0 for value in profile.poses[0].translation_deltas()))
            self.assertTrue(all(value == 0.0 for value in profile.poses[0].rotation_deltas()))
            self.assertLess(profile.poses[-1].pelvis_z, -0.59)

    def test_death_01_preserves_approved_pass02(self) -> None:
        profile = load_death_down_keyposes_profile_v01(
            "human_warrior_m01",
            "death_01_base",
        )
        self.assertEqual(
            profile.revision,
            "death_01_base_down_keyposes_v01_pass02_approved",
        )
        self.assertEqual(profile.gore_mode, "none")
        self.assertIsNone(profile.detached_part_id)
        self.assertIsNone(profile.detachment_frame)
        self.assertEqual(profile.poses[-1].pelvis_roll_z_degrees, -68.0)
        self.assertEqual(profile.poses[-1].spine_pitch_x_degrees, -74.0)

    def test_death_02_and_death_03_are_visually_distinct(self) -> None:
        death_02 = load_death_down_keyposes_profile_v01(
            "human_warrior_m01",
            "death_02_base",
        )
        death_03 = load_death_down_keyposes_profile_v01(
            "human_warrior_m01",
            "death_03_base",
        )
        self.assertEqual(death_02.gore_mode, "severe_impact")
        self.assertGreater(death_02.poses[-1].spine_pitch_x_degrees, 80.0)
        self.assertGreater(death_02.poses[-1].pelvis_roll_z_degrees, 70.0)
        self.assertEqual(death_03.gore_mode, "waist_torso_legs_separation")
        self.assertEqual(death_03.detached_part_id, "upper_torso_and_lower_body")
        self.assertEqual(death_03.detachment_frame, 4)
        self.assertLess(death_03.poses[-1].pelvis_x, -0.20)
        self.assertLess(death_03.poses[-1].pelvis_roll_z_degrees, -60.0)
        self.assertGreater(death_03.poses[-1].spine_pitch_x_degrees, 20.0)

    def test_profile_rejects_unknown_identifiers(self) -> None:
        with self.assertRaises(KeyError):
            load_death_down_keyposes_profiles_v01("unknown_character")
        with self.assertRaises(KeyError):
            load_death_down_keyposes_profile_v01(
                "human_warrior_m01",
                "death_99_base",
            )

    def test_builder_creates_base_actions_and_gore_modules(self) -> None:
        source = BUILDER_PATH.read_text(encoding="utf-8")
        self.assertIn("create_combat_idle_directional_cycles_v14", source)
        self.assertIn("_hit_channels", source)
        self.assertIn('action["grip_mode"] = "base"', source)
        self.assertIn('action["weapon_agnostic"] = True', source)
        self.assertIn('action["weapon_visible"]', source)
        self.assertIn("death03_upper_waist_cut_cap", source)
        self.assertIn("death03_lower_waist_cut_cap", source)
        self.assertIn("_GORE_UPPER_BODY_BONES", source)
        self.assertIn('"cloth.L"', source)
        self.assertIn('"cloth.C"', source)
        self.assertIn('"cloth.R"', source)
        self.assertIn('scene["death_down_action_count"] = len(actions)', source)
        self.assertIn('scene["death_down_runtime_connected"] = False', source)

    def test_renderer_exports_three_rows_without_weapon(self) -> None:
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_FRAME_NUMBERS = (1, 2, 3, 4, 5)", source)
        self.assertIn("human_warrior_m01_death_base_down_keyposes_v01.png", source)
        self.assertIn("weapon_adapter._set_v12_weapon(None, None)", source)
        self.assertNotIn("profile.weapon_cycle_id", source)
        self.assertIn("_apply_gore_state", source)
        self.assertIn("_detach_upper_body", source)
        self.assertIn("return (0.35, 0.30, 0.45)", source)
        self.assertIn("return (0.42, 0.40, 0.55)", source)
        self.assertIn("_restore_upper_body", source)
        self.assertIn("_opaque_component_sizes", source)
        self.assertIn("torso and legs are not visually separated", source)
        self.assertIn("waist_torso_legs_separation", source)
        self.assertIn('"variant_count": len(profiles)', source)
        self.assertIn('"weapon_agnostic": True', source)
        self.assertIn('"random_runtime_selection_not_started": True', source)
        self.assertIn('"runtime_connected": False', source)

    def test_source_files_exist(self) -> None:
        self.assertTrue(PROFILE_PATH.is_file())
        self.assertTrue(BUILDER_PATH.is_file())
        self.assertTrue(ADAPTER_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
