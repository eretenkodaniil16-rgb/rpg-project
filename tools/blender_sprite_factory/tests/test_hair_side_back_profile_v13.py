from __future__ import annotations

import unittest

from hair_side_back_profile_v13 import (
    HUMAN_WARRIOR_M01_HAIR_SIDE_BACK_V13,
    load_hair_side_back_profile_v13,
)


class HairSideBackProfileV13Tests(unittest.TestCase):
    def test_profile_targets_only_eight_existing_side_back_masses(self) -> None:
        profile = load_hair_side_back_profile_v13()
        self.assertEqual(profile.revision, "v13")
        self.assertEqual(profile.proxy_revision, "v16")
        self.assertEqual(len(profile.transforms), 8)
        self.assertEqual(
            {item.name for item in profile.transforms},
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

    def test_side_masses_are_asymmetric_and_descend(self) -> None:
        profile = HUMAN_WARRIOR_M01_HAIR_SIDE_BACK_V13
        left = next(item for item in profile.transforms if item.name == "hair_side_mass_left")
        right = next(item for item in profile.transforms if item.name == "hair_side_mass_right")
        self.assertNotEqual(left.scale_multiplier, right.scale_multiplier)
        self.assertNotEqual(left.world_offset, right.world_offset)
        self.assertLess(left.world_offset[2], 0.0)
        self.assertLess(right.world_offset[2], 0.0)
        self.assertGreater(left.scale_multiplier[2], 1.0)
        self.assertGreater(right.scale_multiplier[2], 1.0)

    def test_nape_uses_three_broad_existing_masses_without_mirroring(self) -> None:
        profile = HUMAN_WARRIOR_M01_HAIR_SIDE_BACK_V13
        nape = [item for item in profile.transforms if item.zone == "nape"]
        self.assertEqual(len(nape), 3)
        self.assertTrue(all(item.world_offset[2] < 0.0 for item in nape))
        self.assertTrue(all(all(value > 0.0 for value in item.scale_multiplier) for item in nape))
        left = next(item for item in nape if item.physical_side == "left")
        right = next(item for item in nape if item.physical_side == "right")
        self.assertNotEqual(
            left.rotation_delta_degrees,
            tuple(-value for value in right.rotation_delta_degrees),
        )


if __name__ == "__main__":
    unittest.main()
