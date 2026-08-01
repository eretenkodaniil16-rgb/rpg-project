from __future__ import annotations

import unittest

from hair_lock_profile_v11 import load_hair_lock_profile_v11


class HairLockProfileV11Tests(unittest.TestCase):
    def test_profile_reduces_long_stripes_to_six_local_depressions(self) -> None:
        profile = load_hair_lock_profile_v11()
        self.assertEqual(profile.revision, "v11")
        self.assertEqual(profile.proxy_revision, "v14")
        self.assertEqual(len(profile.grooves), 6)
        zones = [item.zone for item in profile.grooves]
        self.assertEqual(zones.count("front"), 2)
        self.assertEqual(zones.count("back"), 2)
        self.assertEqual(zones.count("left"), 1)
        self.assertEqual(zones.count("right"), 1)

    def test_each_depression_is_short_curved_and_readable(self) -> None:
        profile = load_hair_lock_profile_v11()
        for groove in profile.grooves:
            self.assertEqual(len(groove.points_uv), 4)
            z_values = [point[1] for point in groove.points_uv]
            u_values = [point[0] for point in groove.points_uv]
            self.assertGreaterEqual(max(z_values) - min(z_values), 0.16)
            self.assertLessEqual(max(z_values) - min(z_values), 0.30)
            self.assertGreaterEqual(max(u_values) - min(u_values), 0.07)

    def test_physical_side_coordinates_remain_explicit(self) -> None:
        profile = load_hair_lock_profile_v11()
        left = next(item for item in profile.grooves if item.zone == "left")
        right = next(item for item in profile.grooves if item.zone == "right")
        self.assertGreater(left.fixed_coordinate, 0.0)
        self.assertLess(right.fixed_coordinate, 0.0)


if __name__ == "__main__":
    unittest.main()
