from __future__ import annotations

import unittest

from hair_forelock_profile_v08 import load_hair_forelock_profile_v08


class HairForelockProfileV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_hair_forelock_profile_v08()

    def test_profile_matches_head_v08_proxy_v11(self) -> None:
        self.assertEqual(self.profile.revision, "v08")
        self.assertEqual(self.profile.proxy_revision, "v11")
        self.assertEqual(self.profile.mesh_name, "hair_reference_forelock_mesh")
        self.profile.assert_valid()

    def test_three_slices_project_from_crown_to_forehead(self) -> None:
        self.assertEqual(len(self.profile.slices), 3)
        self.assertLess(self.profile.slices[0].y, -0.54)
        self.assertGreater(self.profile.slices[-1].y, -0.42)
        self.assertTrue(all(len(item.points_xz) == 7 for item in self.profile.slices))

    def test_forelock_stays_asymmetric_and_above_eye_line(self) -> None:
        front = self.profile.slices[0].points_xz
        lowest = min(front, key=lambda point: point[1])
        self.assertLess(lowest[0], 0.0)
        self.assertGreaterEqual(lowest[1], 4.27)
        self.assertLessEqual(lowest[1], 4.34)
        self.assertGreater(max(point[1] for point in front), 4.68)
        self.assertLess(max(point[0] for point in front), 0.08)

    def test_forelock_is_one_coarse_mesh_not_fragmented_parts(self) -> None:
        all_points = sum(len(item.points_xz) for item in self.profile.slices)
        self.assertEqual(all_points, 21)
        x_span = max(
            point[0] for item in self.profile.slices for point in item.points_xz
        ) - min(point[0] for item in self.profile.slices for point in item.points_xz)
        z_span = max(
            point[1] for item in self.profile.slices for point in item.points_xz
        ) - min(point[1] for item in self.profile.slices for point in item.points_xz)
        self.assertGreater(x_span, 0.22)
        self.assertGreater(z_span, 0.40)


if __name__ == "__main__":
    unittest.main()
