from __future__ import annotations

import unittest

from walk_down_profile_v01 import load_walk_down_profile_v01


class WalkDownProfileV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_walk_down_profile_v01("human_warrior_m01")

    def test_revision_frame_order_and_fps_are_locked(self) -> None:
        self.assertEqual(self.profile.revision, "v01")
        self.assertEqual(self.profile.animation_revision, "v02")
        self.assertEqual(self.profile.animation_id, "walk_down")
        self.assertEqual(self.profile.fps, 8)
        self.assertTrue(self.profile.loop)
        self.assertEqual(tuple(item.frame for item in self.profile.poses), (1, 2, 3, 4, 5, 6))
        self.assertEqual(
            tuple(item.phase for item in self.profile.poses),
            (
                "left_contact",
                "left_recoil",
                "left_passing",
                "right_contact",
                "right_recoil",
                "right_passing",
            ),
        )
        self.profile.assert_valid()

    def test_pelvis_has_weight_transfer_and_three_height_phases(self) -> None:
        left_contact, left_recoil, left_passing, right_contact, right_recoil, right_passing = (
            self.profile.poses
        )
        self.assertLess(left_contact.pelvis_x, 0.0)
        self.assertGreater(right_contact.pelvis_x, 0.0)
        self.assertEqual(left_contact.pelvis_z, right_contact.pelvis_z)
        self.assertEqual(left_recoil.pelvis_z, right_recoil.pelvis_z)
        self.assertEqual(left_passing.pelvis_z, right_passing.pelvis_z)
        self.assertLess(left_recoil.pelvis_z, left_contact.pelvis_z)
        self.assertLess(left_contact.pelvis_z, left_passing.pelvis_z)

    def test_head_stabilizes_against_chest_rotation(self) -> None:
        for pose in self.profile.poses:
            self.assertLessEqual(pose.chest_yaw_z_degrees * pose.head_yaw_z_degrees, 0.0)
            self.assertLessEqual(abs(pose.head_yaw_z_degrees), 1.0)

    def test_asymmetric_pauldron_arm_budget_is_preserved(self) -> None:
        left = tuple(item.upper_arm_left_x_degrees for item in self.profile.poses)
        right = tuple(item.upper_arm_right_x_degrees for item in self.profile.poses)
        self.assertNotEqual(left, tuple(-value for value in right))
        self.assertLess(max(abs(value) for value in left), max(abs(value) for value in right))

    def test_feet_and_cloth_have_explicit_secondary_motion(self) -> None:
        self.assertGreater(
            len({item.foot_left_x_degrees for item in self.profile.poses}),
            3,
        )
        self.assertGreater(
            len({item.foot_right_x_degrees for item in self.profile.poses}),
            3,
        )
        self.assertGreater(
            len({item.cloth_left_x_degrees for item in self.profile.poses}),
            3,
        )

    def test_loop_wrap_stays_inside_channel_budget(self) -> None:
        first = self.profile.poses[0].numeric_channels()
        last = self.profile.poses[-1].numeric_channels()
        self.assertEqual(len(first), len(last))
        self.assertLessEqual(max(abs(end - start) for start, end in zip(first, last)), 14.0)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_down v02 profile"):
            load_walk_down_profile_v01("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
