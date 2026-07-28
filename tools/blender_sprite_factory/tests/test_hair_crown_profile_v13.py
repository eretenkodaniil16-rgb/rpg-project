from __future__ import annotations

import unittest

from hair_crown_profile_v12 import HUMAN_WARRIOR_M01_HAIR_CROWN_V12
from hair_crown_profile_v13 import (
    HUMAN_WARRIOR_M01_HAIR_CROWN_V13,
    load_hair_crown_profile_v13,
)


class HairCrownProfileV13Tests(unittest.TestCase):
    def test_front_silhouette_and_scalp_coverage_remain_locked(self) -> None:
        profile = load_hair_crown_profile_v13()
        previous = HUMAN_WARRIOR_M01_HAIR_CROWN_V12
        self.assertEqual(profile.revision, "v13")
        self.assertEqual(profile.proxy_revision, "v16")
        self.assertEqual(profile.slices[0].y, previous.slices[0].y)
        self.assertEqual(profile.slices[0].points_xz, previous.slices[0].points_xz)
        for slice_index in range(3):
            for point_index in (4, 6, 8):
                self.assertGreaterEqual(
                    profile.slices[slice_index].points_xz[point_index][1],
                    previous.slices[slice_index].points_xz[point_index][1],
                )

    def test_rear_depth_and_lower_edge_gain_broad_hanging_masses(self) -> None:
        profile = HUMAN_WARRIOR_M01_HAIR_CROWN_V13
        previous = HUMAN_WARRIOR_M01_HAIR_CROWN_V12
        self.assertGreater(profile.slices[-1].y, previous.slices[-1].y)
        rear_indices = (11, 12, 13, 14, 15, 0)
        rear_z = [
            profile.slices[-1].points_xz[index][1]
            for index in rear_indices
        ]
        self.assertGreaterEqual(max(rear_z) - min(rear_z), 0.18)
        changed = sum(
            profile.slices[-1].points_xz[index]
            != previous.slices[-1].points_xz[index]
            for index in rear_indices
        )
        self.assertGreaterEqual(changed, 5)

    def test_width_and_medium_length_budgets_remain(self) -> None:
        profile = HUMAN_WARRIOR_M01_HAIR_CROWN_V13
        for profile_slice in profile.slices:
            x_values = [point[0] for point in profile_slice.points_xz]
            self.assertGreaterEqual(min(x_values), -0.47)
            self.assertLessEqual(max(x_values), 0.47)
        rear_z = [
            profile.slices[-1].points_xz[index][1]
            for index in (11, 12, 13, 14, 15, 0)
        ]
        self.assertGreaterEqual(min(rear_z), 4.12)


if __name__ == "__main__":
    unittest.main()
