from __future__ import annotations

import unittest

from hair_crown_profile_v13 import HUMAN_WARRIOR_M01_HAIR_CROWN_V13
from hair_integrated_crown_back_profile_v16 import (
    load_hair_integrated_crown_back_profile_v16,
)


class HairIntegratedCrownBackProfileV16Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_hair_integrated_crown_back_profile_v16()

    def test_profile_identity_and_topology_contract(self) -> None:
        self.assertEqual(self.profile.revision, "v16")
        self.assertEqual(self.profile.proxy_revision, "v19")
        self.assertEqual(self.profile.mesh_name, "hair_reference_crown_mesh")
        self.assertEqual(len(self.profile.slices), 5)
        self.assertTrue(all(len(item.points_xz) == 16 for item in self.profile.slices))

    def test_front_silhouette_remains_locked_to_proxy_v18(self) -> None:
        previous_front = HUMAN_WARRIOR_M01_HAIR_CROWN_V13.slices[0]
        current_front = self.profile.slices[0]
        self.assertEqual(current_front.y, previous_front.y)
        self.assertEqual(current_front.points_xz, previous_front.points_xz)

    def test_depth_advances_into_an_integrated_rear_mass(self) -> None:
        y_values = [item.y for item in self.profile.slices]
        self.assertEqual(y_values, sorted(y_values))
        self.assertGreater(y_values[-1], HUMAN_WARRIOR_M01_HAIR_CROWN_V13.slices[-1].y)
        self.assertLessEqual(y_values[-1], 0.50)

    def test_rear_edge_contains_three_broad_tips_and_two_separators(self) -> None:
        rear = self.profile.slices[-1].points_xz
        tail_z = [rear[index][1] for index in (15, 13, 11)]
        separator_z = [rear[index][1] for index in (14, 12)]
        self.assertLessEqual(max(tail_z), 4.10)
        self.assertGreaterEqual(min(separator_z), 4.18)
        self.assertGreater(min(separator_z) - max(tail_z), 0.08)

    def test_redundant_overlays_are_replaced_but_side_nape_locks_remain(self) -> None:
        self.assertEqual(
            set(self.profile.removed_overlay_names),
            {
                "hair_back_shell",
                "hair_back_sweep_left",
                "hair_back_sweep_right",
            },
        )
        self.assertEqual(
            set(self.profile.retained_profile_lock_names),
            {
                "hair_side_mass_left",
                "hair_side_mass_right",
                "hair_nape_left",
                "hair_nape_center",
                "hair_nape_right",
            },
        )


if __name__ == "__main__":
    unittest.main()
