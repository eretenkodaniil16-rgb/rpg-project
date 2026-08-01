from __future__ import annotations

import unittest

from hair_integrated_crown_back_profile_v16 import (
    HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16,
)
from hair_organic_crown_back_profile_v17 import (
    load_hair_organic_crown_back_profile_v17,
)


class HairOrganicCrownBackProfileV17Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_organic_crown_back_profile_v17()

    def test_revision_and_topology_contract(self) -> None:
        self.assertEqual(self.profile.revision, "v17")
        self.assertEqual(self.profile.proxy_revision, "v20")
        self.assertEqual(self.profile.mesh_name, "hair_reference_crown_mesh")
        self.assertEqual(len(self.profile.slices), 7)
        self.assertTrue(
            all(len(item.control_points_xz) == 16 for item in self.profile.slices)
        )
        self.assertTrue(all(len(item.points_xz) == 32 for item in self.profile.slices))
        self.profile.assert_valid()

    def test_chaikin_sampling_smooths_without_expanding_the_head_budget(self) -> None:
        for profile_slice in self.profile.slices:
            controls = set(profile_slice.control_points_xz)
            sampled = profile_slice.points_xz
            self.assertTrue(all(point not in controls for point in sampled))
            self.assertGreaterEqual(min(point[0] for point in sampled), -0.47)
            self.assertLessEqual(max(point[0] for point in sampled), 0.47)
            self.assertGreaterEqual(min(point[1] for point in sampled), 4.00)
            self.assertLessEqual(max(point[1] for point in sampled), 5.00)

    def test_top_profile_is_lower_and_uses_broad_waves(self) -> None:
        previous = HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16
        self.assertLess(
            max(point[1] for point in self.profile.slices[0].points_xz),
            max(point[1] for point in previous.slices[0].points_xz),
        )
        self.assertLess(
            max(point[1] for point in self.profile.slices[-1].points_xz),
            max(point[1] for point in previous.slices[-1].points_xz),
        )
        for profile_slice in self.profile.slices:
            top_z = [
                profile_slice.control_points_xz[index][1]
                for index in (3, 4, 5, 6, 7, 8)
            ]
            self.assertLessEqual(max(top_z) - min(top_z), 0.14)

    def test_rear_edge_keeps_three_broad_tips_and_two_separators(self) -> None:
        rear = self.profile.slices[-1].control_points_xz
        tips = [rear[index][1] for index in (11, 13, 15)]
        separators = [rear[index][1] for index in (12, 14)]
        self.assertLessEqual(max(tips), 4.10)
        self.assertGreaterEqual(min(separators), 4.22)
        self.assertGreaterEqual(min(separators) - max(tips), 0.10)

    def test_object_and_overlay_contracts_are_preserved(self) -> None:
        previous = HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16
        self.assertEqual(
            self.profile.removed_overlay_names,
            previous.removed_overlay_names,
        )
        self.assertEqual(
            self.profile.retained_profile_lock_names,
            previous.retained_profile_lock_names,
        )


if __name__ == "__main__":
    unittest.main()
