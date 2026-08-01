from __future__ import annotations

import unittest

from walk_left_profile_v01 import load_walk_left_profile_v01


class WalkLeftProfileV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_walk_left_profile_v01("human_warrior_m01")

    def test_revision_direction_frames_and_fps_are_locked(self) -> None:
        self.assertEqual(self.profile.revision, "v01")
        self.assertEqual(self.profile.animation_revision, "v01")
        self.assertEqual(self.profile.animation_id, "walk_left")
        self.assertEqual(self.profile.direction, "left")
        self.assertEqual(self.profile.fps, 8)
        self.assertTrue(self.profile.loop)
        self.assertEqual(tuple(item.frame for item in self.profile.poses), (1, 2, 3, 4, 5, 6))
        self.profile.assert_valid()

    def test_physical_phase_order_is_explicit(self) -> None:
        self.assertEqual(
            tuple(item.phase for item in self.profile.poses),
            (
                "physical_left_contact",
                "physical_left_recoil",
                "physical_left_passing",
                "physical_right_contact",
                "physical_right_recoil",
                "physical_right_passing",
            ),
        )

    def test_vertical_motion_is_restrained(self) -> None:
        heights = tuple(item.pelvis_z for item in self.profile.poses)
        self.assertLessEqual(max(heights) - min(heights), 0.024)
        self.assertEqual(heights[0], heights[3])
        self.assertEqual(heights[1], heights[4])
        self.assertEqual(heights[2], heights[5])

    def test_foreground_left_pauldron_arm_is_more_restrained(self) -> None:
        left = tuple(item.upper_arm_left_x_degrees for item in self.profile.poses)
        right = tuple(item.upper_arm_right_x_degrees for item in self.profile.poses)
        self.assertNotEqual(left, tuple(-value for value in right))
        self.assertLess(max(abs(value) for value in left), max(abs(value) for value in right))

    def test_side_view_adds_real_forearm_articulation(self) -> None:
        self.assertGreater(
            len({item.forearm_left_x_degrees for item in self.profile.poses}),
            3,
        )
        self.assertGreater(
            len({item.forearm_right_x_degrees for item in self.profile.poses}),
            3,
        )

    def test_loop_wrap_stays_inside_ten_degree_budget(self) -> None:
        first = self.profile.poses[0].numeric_channels()
        last = self.profile.poses[-1].numeric_channels()
        self.assertLessEqual(max(abs(end - start) for start, end in zip(first, last)), 10.0)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_left v01 profile"):
            load_walk_left_profile_v01("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
