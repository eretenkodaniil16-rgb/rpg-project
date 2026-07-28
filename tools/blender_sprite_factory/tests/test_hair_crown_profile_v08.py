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
        self.assertTrue(all(len(item.points_xz) == 8 for item in self.profile.slices))

    def test_front_contour_is_asymmetric_and_keeps_face_open(self) -> None:
        front = self.profile.slices[0].points_xz
        z_values = [point[1] for point in front]
        self.assertGreater(min(z_values), 4.20)
        top_three = sorted(front, key=lambda point: point[1], reverse=True)[:3]
        self.assertEqual(len({point[1] for point in top_three}), 3)
        highest = max(front, key=lambda point: point[1])
        self.assertLess(highest[0], 0.0)

    def test_rear_contour_has_medium_length_drop(self) -> None:
        rear = self.profile.slices[-1].points_xz
        self.assertLessEqual(min(point[1] for point in rear), 4.21)
        self.assertGreater(max(point[1] for point in rear), 4.90)
        self.assertLess(min(point[0] for point in rear), -0.40)
        self.assertGreater(max(point[0] for point in rear), 0.40)


if __name__ == "__main__":
    unittest.main()
