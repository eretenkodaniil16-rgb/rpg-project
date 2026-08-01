from __future__ import annotations

import unittest

from walk_right_profile_v01 import load_walk_right_profile_v01


class WalkRightProfileV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_walk_right_profile_v01("human_warrior_m01")

    def test_identity_direction_and_phase_order(self) -> None:
        self.assertEqual(self.profile.revision, "v01")
        self.assertEqual(self.profile.animation_revision, "v01")
        self.assertEqual(self.profile.animation_id, "walk_right")
        self.assertEqual(self.profile.direction, "right")
        self.assertEqual(self.profile.fps, 8)
        self.assertTrue(self.profile.loop)
        self.assertEqual(tuple(item.frame for item in self.profile.poses), (1, 2, 3, 4, 5, 6))
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

    def test_right_view_uses_original_asymmetric_motion(self) -> None:
        left_arm = tuple(item.upper_arm_left_x_degrees for item in self.profile.poses)
        right_arm = tuple(item.upper_arm_right_x_degrees for item in self.profile.poses)
        self.assertNotEqual(left_arm, tuple(-value for value in right_arm))
        self.assertLess(max(abs(value) for value in left_arm), max(abs(value) for value in right_arm))
        self.assertNotEqual(
            tuple(item.forearm_left_x_degrees for item in self.profile.poses),
            tuple(item.forearm_right_x_degrees for item in self.profile.poses),
        )

    def test_height_contact_and_loop_budgets(self) -> None:
        values = [item.pelvis_z for item in self.profile.poses]
        self.assertLessEqual(max(values) - min(values), 0.024)
        self.assertLessEqual(abs(self.profile.poses[0].foot_left_x_degrees), 5.0)
        self.assertLessEqual(abs(self.profile.poses[3].foot_right_x_degrees), 5.0)
        for index in range(len(self.profile.poses[0].numeric_channels())):
            delta = abs(
                self.profile.poses[-1].numeric_channels()[index]
                - self.profile.poses[0].numeric_channels()[index]
            )
            self.assertLessEqual(delta, 10.0)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No walk_right v01 profile"):
            load_walk_right_profile_v01("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
