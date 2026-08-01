from __future__ import annotations

import unittest

from hair_lock_profile_v09 import load_hair_lock_profile_v09


class HairLockProfileV09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_hair_lock_profile_v09()

    def test_profile_matches_head_v09_proxy_v12(self) -> None:
        self.assertEqual(self.profile.revision, "v09")
        self.assertEqual(self.profile.proxy_revision, "v12")
        self.assertEqual(self.profile.mesh_name, "hair_reference_lock_separators_mesh")
        self.assertEqual(self.profile.material_role, "shadow")
        self.profile.assert_valid()

    def test_profile_uses_large_readable_zone_budget(self) -> None:
        zones = [item.zone for item in self.profile.grooves]
        self.assertEqual(zones.count("front"), 3)
        self.assertEqual(zones.count("back"), 3)
        self.assertEqual(zones.count("left"), 1)
        self.assertEqual(zones.count("right"), 1)
        self.assertTrue(all(len(item.points_uv) == 3 for item in self.profile.grooves))
        self.assertTrue(all(item.half_width >= 0.022 for item in self.profile.grooves))

    def test_side_grooves_keep_physical_sides(self) -> None:
        left = next(item for item in self.profile.grooves if item.zone == "left")
        right = next(item for item in self.profile.grooves if item.zone == "right")
        self.assertEqual(left.plane, "YZ")
        self.assertEqual(right.plane, "YZ")
        self.assertGreater(left.fixed_coordinate, 0.0)
        self.assertLess(right.fixed_coordinate, 0.0)

    def test_front_and_back_grooves_sit_outside_crown_surfaces(self) -> None:
        front = [item for item in self.profile.grooves if item.zone == "front"]
        back = [item for item in self.profile.grooves if item.zone == "back"]
        self.assertTrue(all(item.plane == "XZ" for item in front + back))
        self.assertTrue(all(item.fixed_coordinate < -0.49 for item in front))
        self.assertTrue(all(item.fixed_coordinate > 0.29 for item in back))


if __name__ == "__main__":
    unittest.main()
