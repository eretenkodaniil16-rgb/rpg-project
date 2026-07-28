from __future__ import annotations

import unittest

from hair_lock_exposure_profile_v15 import load_hair_lock_exposure_profile_v15


class HairLockExposureProfileV15Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_lock_exposure_profile_v15()

    def test_profile_targets_exactly_eight_existing_profile_locks(self) -> None:
        self.assertEqual(self.profile.revision, "v15")
        self.assertEqual(self.profile.proxy_revision, "v18")
        self.assertEqual(len(self.profile.transforms), 8)
        self.assertEqual(
            {item.name for item in self.profile.transforms},
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

    def test_central_shell_shrinks_and_moves_up(self) -> None:
        shell = next(
            item for item in self.profile.transforms if item.name == "hair_back_shell"
        )
        self.assertTrue(all(value < 1.0 for value in shell.scale_multiplier))
        self.assertGreater(shell.world_offset[2], 0.0)

    def test_remaining_locks_move_rearward_and_downward(self) -> None:
        hanging = [
            item for item in self.profile.transforms if item.name != "hair_back_shell"
        ]
        self.assertTrue(all(item.world_offset[1] > 0.0 for item in hanging))
        self.assertTrue(all(item.world_offset[2] < 0.0 for item in hanging))

    def test_physical_side_offsets_are_not_mirrored(self) -> None:
        left = next(
            item for item in self.profile.transforms if item.name == "hair_side_mass_left"
        )
        right = next(
            item for item in self.profile.transforms if item.name == "hair_side_mass_right"
        )
        self.assertNotEqual(
            left.world_offset,
            tuple(-value for value in right.world_offset),
        )
        self.assertNotEqual(
            left.rotation_delta_degrees,
            tuple(-value for value in right.rotation_delta_degrees),
        )


if __name__ == "__main__":
    unittest.main()
