from __future__ import annotations

import unittest

from hair_organic_tone_profile_v18 import load_hair_organic_tone_profile_v18


class HairOrganicToneProfileV18Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_organic_tone_profile_v18()

    def test_revision_and_roles(self) -> None:
        self.assertEqual(self.profile.revision, "v18")
        self.assertEqual(self.profile.proxy_revision, "v21")
        self.assertEqual(self.profile.highlight_region.role, "highlight")
        self.assertEqual(self.profile.main_mid_region.role, "mid")
        self.assertEqual(self.profile.rear_mid_region.role, "mid")
        self.profile.assert_valid()

    def test_highlight_is_smaller_than_main_mid_region(self) -> None:
        for highlight, mid in zip(
            self.profile.highlight_region.radius_xyz,
            self.profile.main_mid_region.radius_xyz,
        ):
            self.assertLess(highlight, mid)

    def test_local_highlight_contains_center_but_not_broad_crown_edges(self) -> None:
        center = self.profile.highlight_region.center_xyz
        self.assertTrue(self.profile.highlight_region.contains(*center))
        self.assertFalse(self.profile.highlight_region.contains(-0.40, -0.10, 4.88))
        self.assertFalse(self.profile.highlight_region.contains(0.35, -0.10, 4.88))
        self.assertFalse(self.profile.highlight_region.contains(-0.08, 0.40, 4.88))

    def test_shadow_boundaries_stay_in_lower_and_rear_hair(self) -> None:
        self.assertLessEqual(self.profile.lower_shadow_base_z, 4.35)
        self.assertGreaterEqual(self.profile.rear_shadow_min_y, 0.20)
        self.assertLessEqual(self.profile.rear_shadow_base_z, 4.55)


if __name__ == "__main__":
    unittest.main()
