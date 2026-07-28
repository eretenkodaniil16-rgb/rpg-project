from __future__ import annotations

import unittest

from hair_crown_profile_v08 import load_hair_crown_profile_v08


class HairCrownProfileV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_hair_crown_profile_v08()

    def test_profile_matches_head_v08_proxy_v11(self) -> None:
        self.assertEqual(self.profile.revision, "v08")
        self.assertEqual(self.profile.proxy_revision, "v11")
        self.assertEqual(self.profile.mesh_name, "hair_reference_crown_mesh")
        self.profile.assert_valid()

    def test_three_slices_cover_front_middle_and_back(self) -> None:
        self.assertEqual(len(self.profile.slices), 3)
        self.assertLess(self.profile.slices[0].y, -0.40)
        self.assertLess(self.profile.slices[1].y, 0.0)
        self.assertGreater(self.profile.slices[2].y, 0.20)
        self.assertTrue(all(len(item.points_xz) == 16 for item in self.profile.slices))

    def test_front_contour_is_compact_with_large_asymmetric_waves(self) -> None:
        front = self.profile.slices[0].points_xz
        z_values = [point[1] for point in front]
        self.assertGreater(min(z_values), 4.20)
        wave = front[3:9]
        self.assertGreaterEqual(
            max(point[1] for point in wave) - min(point[1] for point in wave),
            0.13,
        )
        highest = max(wave, key=lambda point: point[1])
        self.assertLess(highest[0], 0.0)
        self.assertLessEqual(highest[1], 5.00)
        self.assertGreater(wave[0][1], wave[1][1])
        self.assertGreater(wave[2][1], wave[3][1])
        self.assertGreater(wave[4][1], wave[5][1])

    def test_front_hairline_leaves_room_for_separate_forelock(self) -> None:
        hairline = self.profile.slices[0].points_xz[12:16]
        lowest = min(hairline, key=lambda point: point[1])
        self.assertLess(lowest[0], 0.0)
        self.assertGreaterEqual(lowest[1], 4.40)
        self.assertLessEqual(lowest[1], 4.44)
        self.assertGreaterEqual(max(point[1] for point in hairline), 4.50)

    def test_rear_contour_has_medium_length_drop_and_waves(self) -> None:
        rear = self.profile.slices[-1].points_xz
        self.assertLessEqual(min(point[1] for point in rear), 4.21)
        self.assertGreater(max(point[1] for point in rear), 4.87)
        self.assertLessEqual(max(point[1] for point in rear), 4.90)
        self.assertLess(min(point[0] for point in rear), -0.39)
        self.assertGreaterEqual(max(point[0] for point in rear), 0.40)
        rear_wave = rear[3:9]
        self.assertGreater(
            max(point[1] for point in rear_wave) - min(point[1] for point in rear_wave),
            0.14,
        )


if __name__ == "__main__":
    unittest.main()
