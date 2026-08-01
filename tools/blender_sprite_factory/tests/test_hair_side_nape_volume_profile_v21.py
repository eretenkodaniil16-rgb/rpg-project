from __future__ import annotations

import unittest

from hair_side_nape_volume_profile_v21 import (
    load_hair_side_nape_volume_profile_v21,
)


class HairSideNapeVolumeProfileV21Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_side_nape_volume_profile_v21()

    def test_revision_and_targets(self) -> None:
        self.assertEqual(self.profile.revision, "v21")
        self.assertEqual(self.profile.proxy_revision, "v24")
        self.assertEqual(
            {item.name for item in self.profile.transforms},
            {
                "hair_side_mass_left",
                "hair_side_mass_right",
                "hair_nape_left",
                "hair_nape_center",
                "hair_nape_right",
            },
        )
        self.profile.assert_valid()

    def test_pass_only_adds_restrained_volume(self) -> None:
        for transform in self.profile.transforms:
            self.assertTrue(all(value >= 1.0 for value in transform.scale_multiplier))
            self.assertTrue(all(value <= 1.08 for value in transform.scale_multiplier))
            self.assertGreaterEqual(transform.world_offset[1], 0.0)
            self.assertLessEqual(transform.world_offset[1], 0.026)
            self.assertGreaterEqual(transform.world_offset[2], -0.020)
            self.assertLessEqual(transform.world_offset[2], 0.0)

    def test_side_transforms_are_asymmetrical_without_mirroring(self) -> None:
        left = next(
            item for item in self.profile.transforms if item.name == "hair_side_mass_left"
        )
        right = next(
            item for item in self.profile.transforms if item.name == "hair_side_mass_right"
        )
        self.assertNotEqual(left.scale_multiplier, right.scale_multiplier)
        self.assertNotEqual(
            left.rotation_delta_degrees,
            tuple(-value for value in right.rotation_delta_degrees),
        )

    def test_nape_remains_medium_length(self) -> None:
        nape = [item for item in self.profile.transforms if item.zone == "nape"]
        self.assertEqual(len(nape), 3)
        self.assertTrue(all(item.scale_multiplier[2] <= 1.06 for item in nape))
        self.assertTrue(all(item.world_offset[2] >= -0.020 for item in nape))


if __name__ == "__main__":
    unittest.main()
