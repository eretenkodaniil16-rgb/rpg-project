from __future__ import annotations

import unittest

from walk_up_profile_v01 import load_walk_up_profile_v01


class WalkUpProfileV01Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_walk_up_profile_v01("human_warrior_m01")

    def test_identity_direction_frames_and_fps(self) -> None:
        self.assertEqual(self.profile.revision, "v01")
        self.assertEqual(self.profile.animation_revision, "v01")
        self.assertEqual(self.profile.animation_id, "walk_up")
        self.assertEqual(self.profile.direction, "up")
        self.assertEqual(self.profile.fps, 8)
        self.assertTrue(self.profile.loop)
        self.assertEqual(tuple(item.frame for item in self.profile.poses), (1, 2, 3, 4, 5, 6))
        self.profile.assert_valid()

    def test_rear_cycle_has_restrained_vertical_motion(self) -> None:
        values = [item.pelvis_z for item in self.profile.poses]
        self.assertLessEqual(max(values) - min(values), 0.022)
        self.assertEqual(self.profile.poses[0].pelvis_z, self.profile.poses[3].pelvis_z)
        self.assertEqual(self.profile.poses[1].pelvis_z, self.profile.poses[4].pelvis_z)
        self.assertEqual(self.profile.poses[2].pelvis_z, self.profile.poses[5].pelvis_z)

    def test_back_cloth_is_readable_but_bounded(self) -> None:
        maximum = max(
            max(abs(item.cloth_left_x_degrees), abs(item.cloth_right_x_degrees))
            for item in self.profile.poses
        )
        self.assertGreaterEqual(maximum, 2.5)
        self.assertLessEqual(maximum, 3.0)
        self.assertTrue(all(abs(item.cloth_center_x_degrees) <= 1.2 for item in self.profile.poses))

    def test_large_left_pauldron_keeps_left_arm_restrained(self) -> None:
        left_maximum = max(abs(item.upper_arm_left_x_degrees) for item in self.profile.poses)
        right_maximum = max(abs(item.upper_arm_right_x_degrees) for item in self.profile.poses)
        self.assertLess(left_maximum, right_maximum)

    def test_loop_wrap_stays_inside_ten_degree_budget(self) -> None:
        first = self.profile.poses[0].numeric_channels()
        last = self.profile.poses[-1].numeric_channels()
        self.assertLessEqual(max(abs(end - start) for start, end in zip(first, last)), 10.0)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_up v01 profile"):
            load_walk_up_profile_v01("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
