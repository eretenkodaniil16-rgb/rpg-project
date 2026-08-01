from __future__ import annotations

import unittest

from hair_crown_profile_v11 import HUMAN_WARRIOR_M01_HAIR_CROWN_V11
from hair_crown_profile_v12 import (
    HUMAN_WARRIOR_M01_HAIR_CROWN_V12,
    load_hair_crown_profile_v12,
)


class HairCrownProfileV12Tests(unittest.TestCase):
    def test_profile_closes_only_the_internal_scalp_coverage_valleys(self) -> None:
        profile = load_hair_crown_profile_v12()
        self.assertEqual(profile.revision, "v12")
        self.assertEqual(profile.proxy_revision, "v15")
        self.assertEqual(profile.mesh_name, HUMAN_WARRIOR_M01_HAIR_CROWN_V11.mesh_name)

        adjusted_indices = {4, 6, 8}
        for previous_slice, current_slice in zip(
            HUMAN_WARRIOR_M01_HAIR_CROWN_V11.slices,
            profile.slices,
        ):
            self.assertEqual(current_slice.y, previous_slice.y)
            for index, (previous_point, current_point) in enumerate(
                zip(previous_slice.points_xz, current_slice.points_xz)
            ):
                self.assertEqual(current_point[0], previous_point[0])
                if index in adjusted_indices:
                    self.assertGreaterEqual(current_point[1] - previous_point[1], 0.055)
                else:
                    self.assertEqual(current_point[1], previous_point[1])

    def test_outer_dimensions_and_highest_wave_remain_locked(self) -> None:
        profile = load_hair_crown_profile_v12()
        previous = HUMAN_WARRIOR_M01_HAIR_CROWN_V11
        for previous_slice, current_slice in zip(previous.slices, profile.slices):
            self.assertEqual(
                (min(point[0] for point in current_slice.points_xz), max(point[0] for point in current_slice.points_xz)),
                (min(point[0] for point in previous_slice.points_xz), max(point[0] for point in previous_slice.points_xz)),
            )
        self.assertEqual(
            max(point[1] for point in profile.slices[0].points_xz),
            max(point[1] for point in previous.slices[0].points_xz),
        )
        self.assertIs(profile, HUMAN_WARRIOR_M01_HAIR_CROWN_V12)

    def test_coverage_floors_prevent_skin_breakthrough(self) -> None:
        profile = load_hair_crown_profile_v12()
        floors = (4.85, 4.86, 4.76)
        for profile_slice, floor in zip(profile.slices, floors):
            self.assertGreaterEqual(
                min(profile_slice.points_xz[index][1] for index in (4, 6, 8)),
                floor,
            )


if __name__ == "__main__":
    unittest.main()
