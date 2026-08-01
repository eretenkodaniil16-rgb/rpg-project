from __future__ import annotations

import unittest

from hair_organic_crown_back_profile_v17 import (
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17,
)
from hair_volume_crown_back_profile_v19 import (
    load_hair_volume_crown_back_profile_v19,
)


class HairVolumeCrownBackProfileV19Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_volume_crown_back_profile_v19()
        self.previous = HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17

    @staticmethod
    def _width(profile_slice: object) -> float:
        x_values = [point[0] for point in profile_slice.points_xz]
        return max(x_values) - min(x_values)

    def test_revision_and_topology_contract(self) -> None:
        self.assertEqual(self.profile.revision, "v19")
        self.assertEqual(self.profile.proxy_revision, "v22")
        self.assertEqual(self.profile.mesh_name, "hair_reference_crown_mesh")
        self.assertEqual(len(self.profile.slices), 7)
        self.assertTrue(
            all(len(item.control_points_xz) == 16 for item in self.profile.slices)
        )
        self.assertTrue(all(len(item.points_xz) == 32 for item in self.profile.slices))
        self.profile.assert_valid()

    def test_center_rise_is_broad_in_every_depth_slice(self) -> None:
        for profile_slice in self.profile.slices:
            central = [
                profile_slice.control_points_xz[index][1]
                for index in (5, 6, 7)
            ]
            shoulders = [
                profile_slice.control_points_xz[index][1]
                for index in (3, 4, 8)
            ]
            self.assertGreaterEqual(
                sum(central) / len(central) - sum(shoulders) / len(shoulders),
                0.04,
            )
            top = [
                profile_slice.control_points_xz[index][1]
                for index in (3, 4, 5, 6, 7, 8)
            ]
            self.assertLessEqual(max(top) - min(top), 0.10)

    def test_width_tapers_gradually_from_crown_center_to_nape(self) -> None:
        widths = [self._width(item) for item in self.profile.slices]
        self.assertLessEqual(
            abs(widths[0] - self._width(self.previous.slices[0])),
            0.03,
        )
        self.assertGreaterEqual(
            self._width(self.previous.slices[-1]) - widths[-1],
            0.07,
        )
        for current_width, next_width in zip(widths[2:], widths[3:]):
            self.assertLess(next_width, current_width)
            self.assertLessEqual(current_width - next_width, 0.07)

    def test_front_lift_is_restrained_and_rear_height_is_stable(self) -> None:
        previous_front_top = max(
            point[1] for point in self.previous.slices[0].points_xz
        )
        current_front_top = max(point[1] for point in self.profile.slices[0].points_xz)
        self.assertGreaterEqual(current_front_top - previous_front_top, 0.01)
        self.assertLessEqual(current_front_top - previous_front_top, 0.04)

        previous_rear_top = max(
            point[1] for point in self.previous.slices[-1].points_xz
        )
        current_rear_top = max(point[1] for point in self.profile.slices[-1].points_xz)
        self.assertLessEqual(abs(current_rear_top - previous_rear_top), 0.01)

    def test_existing_overlays_and_profile_locks_are_preserved(self) -> None:
        self.assertEqual(
            self.profile.removed_overlay_names,
            self.previous.removed_overlay_names,
        )
        self.assertEqual(
            self.profile.retained_profile_lock_names,
            self.previous.retained_profile_lock_names,
        )


if __name__ == "__main__":
    unittest.main()
