from __future__ import annotations

import unittest

from hair_lock_profile_v10 import load_hair_lock_profile_v10


class HairLockProfileV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_hair_lock_profile_v10()

    def test_profile_matches_head_v10_proxy_v13(self) -> None:
        self.assertEqual(self.profile.revision, "v10")
        self.assertEqual(self.profile.proxy_revision, "v13")
        self.assertEqual(self.profile.mesh_name, "hair_reference_lock_separators_mesh")
        self.assertEqual(self.profile.material_role, "separator")
        self.profile.assert_valid()

    def test_eight_grooves_keep_front_back_and_physical_side_contract(self) -> None:
        zones = [item.zone for item in self.profile.grooves]
        self.assertEqual(zones.count("front"), 3)
        self.assertEqual(zones.count("back"), 3)
        self.assertEqual(zones.count("left"), 1)
        self.assertEqual(zones.count("right"), 1)
        left = next(item for item in self.profile.grooves if item.zone == "left")
        right = next(item for item in self.profile.grooves if item.zone == "right")
        self.assertGreater(left.fixed_coordinate, 0.0)
        self.assertLess(right.fixed_coordinate, 0.0)

    def test_every_groove_uses_four_points_and_visible_curvature(self) -> None:
        for groove in self.profile.grooves:
            self.assertEqual(len(groove.points_uv), 4)
            steps = [
                groove.points_uv[index + 1][0] - groove.points_uv[index][0]
                for index in range(3)
            ]
            self.assertGreater(max(steps) - min(steps), 0.035)
            self.assertGreater(
                max(point[1] for point in groove.points_uv)
                - min(point[1] for point in groove.points_uv),
                0.24,
            )


if __name__ == "__main__":
    unittest.main()
