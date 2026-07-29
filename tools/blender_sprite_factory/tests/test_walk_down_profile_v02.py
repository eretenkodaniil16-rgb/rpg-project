from __future__ import annotations

import unittest

from walk_down_profile_v01 import load_walk_down_profile_v01
from walk_down_profile_v02 import load_walk_down_profile_v02


class WalkDownProfileV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.previous = load_walk_down_profile_v01("human_warrior_m01")
        cls.profile = load_walk_down_profile_v02("human_warrior_m01")

    def test_revision_frame_order_and_fps_are_locked(self) -> None:
        self.assertEqual(self.profile.revision, "v02")
        self.assertEqual(self.profile.animation_revision, "v03")
        self.assertEqual(self.profile.animation_id, "walk_down")
        self.assertEqual(self.profile.fps, 8)
        self.assertTrue(self.profile.loop)
        self.assertEqual(tuple(item.frame for item in self.profile.poses), (1, 2, 3, 4, 5, 6))
        self.profile.assert_valid()

    def test_vertical_bounce_is_materially_reduced_from_v02(self) -> None:
        previous_range = max(item.pelvis_z for item in self.previous.poses) - min(
            item.pelvis_z for item in self.previous.poses
        )
        current_range = max(item.pelvis_z for item in self.profile.poses) - min(
            item.pelvis_z for item in self.profile.poses
        )
        self.assertAlmostEqual(previous_range, 0.070)
        self.assertAlmostEqual(current_range, 0.039)
        self.assertLess(current_range, previous_range * 0.70)
        self.assertLessEqual(current_range, 0.045)

    def test_extreme_leg_and_foot_arcs_are_reduced(self) -> None:
        previous_shin = max(
            max(abs(item.shin_left_x_degrees), abs(item.shin_right_x_degrees))
            for item in self.previous.poses
        )
        current_shin = max(
            max(abs(item.shin_left_x_degrees), abs(item.shin_right_x_degrees))
            for item in self.profile.poses
        )
        previous_foot = max(
            max(abs(item.foot_left_x_degrees), abs(item.foot_right_x_degrees))
            for item in self.previous.poses
        )
        current_foot = max(
            max(abs(item.foot_left_x_degrees), abs(item.foot_right_x_degrees))
            for item in self.profile.poses
        )
        self.assertLess(current_shin, previous_shin)
        self.assertLess(current_foot, previous_foot)
        self.assertLessEqual(current_shin, 18.0)
        self.assertLessEqual(current_foot, 10.0)

    def test_contact_feet_are_visually_planted(self) -> None:
        left_contact = self.profile.poses[0]
        right_contact = self.profile.poses[3]
        self.assertLessEqual(abs(left_contact.foot_left_x_degrees), 6.0)
        self.assertLessEqual(abs(right_contact.foot_right_x_degrees), 6.0)

    def test_head_and_cloth_motion_are_restrained(self) -> None:
        for pose in self.profile.poses:
            self.assertLessEqual(abs(pose.head_yaw_z_degrees), 0.5)
            self.assertLessEqual(
                max(abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)),
                3.0,
            )
            self.assertLessEqual(pose.chest_yaw_z_degrees * pose.head_yaw_z_degrees, 0.0)

    def test_asymmetric_pauldron_arm_budget_is_preserved(self) -> None:
        left = tuple(item.upper_arm_left_x_degrees for item in self.profile.poses)
        right = tuple(item.upper_arm_right_x_degrees for item in self.profile.poses)
        self.assertNotEqual(left, tuple(-value for value in right))
        self.assertLess(max(abs(value) for value in left), max(abs(value) for value in right))

    def test_loop_wrap_is_tighter_than_the_previous_budget(self) -> None:
        first = self.profile.poses[0].numeric_channels()
        last = self.profile.poses[-1].numeric_channels()
        self.assertLessEqual(max(abs(end - start) for start, end in zip(first, last)), 12.0)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_down v03 profile"):
            load_walk_down_profile_v02("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
