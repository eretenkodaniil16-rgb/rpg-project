from __future__ import annotations

import unittest

from walk_down_profile_v02 import load_walk_down_profile_v02
from walk_down_profile_v03 import load_walk_down_profile_v03


class WalkDownProfileV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.previous = load_walk_down_profile_v02("human_warrior_m01")
        cls.profile = load_walk_down_profile_v03("human_warrior_m01")

    def test_revision_frame_order_and_fps_are_locked(self) -> None:
        self.assertEqual(self.profile.revision, "v03")
        self.assertEqual(self.profile.animation_revision, "v04")
        self.assertEqual(self.profile.animation_id, "walk_down")
        self.assertEqual(self.profile.fps, 8)
        self.assertTrue(self.profile.loop)
        self.assertEqual(tuple(item.frame for item in self.profile.poses), (1, 2, 3, 4, 5, 6))
        self.profile.assert_valid()

    def test_vertical_range_is_reduced_again(self) -> None:
        current = max(item.pelvis_z for item in self.profile.poses) - min(
            item.pelvis_z for item in self.profile.poses
        )
        previous = max(item.pelvis_z for item in self.previous.poses) - min(
            item.pelvis_z for item in self.previous.poses
        )
        self.assertLessEqual(current, 0.026)
        self.assertLess(current, previous * 0.70)

    def test_left_recoil_is_straighter_than_v03(self) -> None:
        current = self.profile.poses[1]
        previous = self.previous.poses[1]
        self.assertLess(abs(current.shin_left_x_degrees), abs(previous.shin_left_x_degrees))
        self.assertLess(abs(current.shin_right_x_degrees), abs(previous.shin_right_x_degrees))

    def test_right_contact_is_compressed_for_perspective(self) -> None:
        current = self.profile.poses[3]
        previous = self.previous.poses[3]
        self.assertLess(abs(current.thigh_left_x_degrees), abs(previous.thigh_left_x_degrees))
        self.assertLess(abs(current.thigh_right_x_degrees), abs(previous.thigh_right_x_degrees))
        self.assertGreater(current.spine_pitch_x_degrees, self.profile.poses[0].spine_pitch_x_degrees)

    def test_approved_asymmetric_arm_budget_is_preserved(self) -> None:
        left = tuple(item.upper_arm_left_x_degrees for item in self.profile.poses)
        right = tuple(item.upper_arm_right_x_degrees for item in self.profile.poses)
        self.assertNotEqual(left, tuple(-value for value in right))
        self.assertLess(max(abs(value) for value in left), max(abs(value) for value in right))

    def test_loop_wrap_stays_inside_v04_budget(self) -> None:
        first = self.profile.poses[0].numeric_channels()
        last = self.profile.poses[-1].numeric_channels()
        self.assertEqual(len(first), len(last))
        self.assertLessEqual(max(abs(end - start) for start, end in zip(first, last)), 10.0)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_down v04 profile"):
            load_walk_down_profile_v03("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
