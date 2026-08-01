from __future__ import annotations

import unittest

from hair_crown_profile_v08 import HUMAN_WARRIOR_M01_HAIR_CROWN_V08
from hair_crown_profile_v11 import (
    HUMAN_WARRIOR_M01_HAIR_CROWN_V11,
    load_hair_crown_profile_v11,
)


class HairCrownProfileV11Tests(unittest.TestCase):
    def test_profile_keeps_topology_and_advances_physical_shape_revision(self) -> None:
        profile = load_hair_crown_profile_v11()
        self.assertEqual(profile.revision, "v11")
        self.assertEqual(profile.proxy_revision, "v14")
        self.assertEqual(profile.mesh_name, HUMAN_WARRIOR_M01_HAIR_CROWN_V08.mesh_name)
        self.assertEqual(len(profile.slices), 3)
        self.assertTrue(all(len(item.points_xz) == 16 for item in profile.slices))

    def test_front_silhouette_has_three_large_asymmetric_waves(self) -> None:
        front = HUMAN_WARRIOR_M01_HAIR_CROWN_V11.slices[0].points_xz
        for peak_index, left_valley, right_valley in ((3, 2, 4), (5, 4, 6), (7, 6, 8)):
            self.assertGreater(front[peak_index][1] - front[left_valley][1], 0.11)
            self.assertGreater(front[peak_index][1] - front[right_valley][1], 0.11)
        highest = max(front[3:9], key=lambda point: point[1])
        self.assertLess(highest[0], 0.0)
        self.assertNotEqual(front, HUMAN_WARRIOR_M01_HAIR_CROWN_V08.slices[0].points_xz)

    def test_rear_lower_edge_forms_broad_hanging_masses(self) -> None:
        back = HUMAN_WARRIOR_M01_HAIR_CROWN_V11.slices[-1].points_xz
        rear_lower_edge = (back[11], back[12], back[13], back[14], back[15], back[0])
        z_values = [point[1] for point in rear_lower_edge]
        self.assertGreater(max(z_values) - min(z_values), 0.13)
        self.assertLess(back[14][1], back[13][1])
        self.assertGreater(back[15][1], back[14][1])


if __name__ == "__main__":
    unittest.main()
