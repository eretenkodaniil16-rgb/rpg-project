from __future__ import annotations

import unittest

from hair_major_lock_profile_v14 import load_hair_major_lock_profile_v14


class HairMajorLockProfileV14Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_major_lock_profile_v14()

    def test_profile_replaces_exactly_eight_existing_masses(self) -> None:
        self.assertEqual(self.profile.revision, "v14")
        self.assertEqual(self.profile.proxy_revision, "v17")
        self.assertEqual(len(self.profile.locks), 8)
        self.assertEqual(
            {lock.name for lock in self.profile.locks},
            {
                "hair_back_shell",
                "hair_back_sweep_left",
                "hair_back_sweep_right",
                "hair_side_mass_left",
                "hair_side_mass_right",
                "hair_nape_left",
                "hair_nape_center",
                "hair_nape_right",
            },
        )

    def test_every_lock_is_a_coarse_pointed_profile_mesh(self) -> None:
        for lock in self.profile.locks:
            self.assertEqual(lock.ring_sides, 6)
            self.assertEqual(len(lock.rings), 6)
            self.assertEqual(lock.rings[0].z_ratio, 1.0)
            self.assertEqual(lock.rings[-1].z_ratio, -1.0)
            self.assertLess(lock.rings[0].radius_x_ratio, 0.45)
            self.assertLess(lock.rings[-1].radius_x_ratio, 0.35)
            self.assertGreaterEqual(
                max(ring.radius_x_ratio for ring in lock.rings[1:-1]),
                0.85,
            )

    def test_physical_sides_are_asymmetric_instead_of_mirrored(self) -> None:
        left = next(lock for lock in self.profile.locks if lock.name == "hair_side_mass_left")
        right = next(lock for lock in self.profile.locks if lock.name == "hair_side_mass_right")
        left_path = tuple((ring.center_x_ratio, ring.center_y_ratio) for ring in left.rings)
        right_path = tuple((ring.center_x_ratio, ring.center_y_ratio) for ring in right.rings)
        self.assertNotEqual(left_path, tuple((-x, y) for x, y in right_path))
        self.assertNotEqual(left.rings[-1].center_y_ratio, right.rings[-1].center_y_ratio)

    def test_three_nape_tips_form_distinct_hanging_endpoints(self) -> None:
        nape = [lock for lock in self.profile.locks if lock.zone == "nape"]
        self.assertEqual(len(nape), 3)
        self.assertEqual(
            len(
                {
                    (lock.rings[-1].center_x_ratio, lock.rings[-1].center_y_ratio)
                    for lock in nape
                }
            ),
            3,
        )


if __name__ == "__main__":
    unittest.main()
