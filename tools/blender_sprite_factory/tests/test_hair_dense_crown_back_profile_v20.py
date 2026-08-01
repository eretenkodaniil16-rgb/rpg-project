from __future__ import annotations

import unittest

from hair_dense_crown_back_profile_v20 import (
    load_hair_dense_crown_back_profile_v20,
)
from hair_organic_crown_back_profile_v17 import (
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17,
)


class HairDenseCrownBackProfileV20Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_dense_crown_back_profile_v20()
        self.previous = HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17

    def test_revision_and_topology_contract(self) -> None:
        self.assertEqual(self.profile.revision, "v20")
        self.assertEqual(self.profile.proxy_revision, "v23")
        self.assertEqual(self.profile.mesh_name, "hair_reference_crown_mesh")
        self.assertEqual(len(self.profile.slices), 7)
        self.assertTrue(all(len(item.control_points_xz) == 16 for item in self.profile.slices))
        self.assertTrue(all(len(item.points_xz) == 32 for item in self.profile.slices))
        self.profile.assert_valid()

    def test_proxy_v21_width_is_restored_exactly(self) -> None:
        for current, previous in zip(self.profile.slices, self.previous.slices):
            self.assertEqual(
                tuple(point[0] for point in current.control_points_xz),
                tuple(point[0] for point in previous.control_points_xz),
            )
            current_width = max(point[0] for point in current.points_xz) - min(
                point[0] for point in current.points_xz
            )
            previous_width = max(point[0] for point in previous.points_xz) - min(
                point[0] for point in previous.points_xz
            )
            self.assertAlmostEqual(current_width, previous_width)

    def test_dense_correction_never_reduces_top_volume(self) -> None:
        for current, previous in zip(self.profile.slices, self.previous.slices):
            self.assertGreater(
                max(point[1] for point in current.points_xz),
                max(point[1] for point in previous.points_xz),
            )

    def test_only_three_broad_top_controls_change(self) -> None:
        changed_indices = {5, 6, 7}
        for current, previous in zip(self.profile.slices, self.previous.slices):
            for index, (current_point, previous_point) in enumerate(
                zip(current.control_points_xz, previous.control_points_xz)
            ):
                if index in changed_indices:
                    self.assertGreater(current_point[1], previous_point[1])
                else:
                    self.assertEqual(current_point, previous_point)

    def test_object_and_lock_contracts_are_preserved(self) -> None:
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
