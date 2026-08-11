from __future__ import annotations

import unittest
from pathlib import Path

from environment_profile_v01 import load_environment_profile
from geometry_plan_v01 import crack_segments, damp_spots, dust_spots, floor_blocks


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    REPO_ROOT
    / "tools/blender_environment_factory/configs/cold_ancient_stone_v01.json"
)


class GeometryPlanV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_environment_profile(CONFIG_PATH, REPO_ROOT)

    def test_floor_geometry_is_deterministic_and_variant_aware(self) -> None:
        first = self.profile.asset("cold_stone_floor_01")
        second = self.profile.asset("cold_stone_floor_02")

        first_once = floor_blocks(first)
        first_twice = floor_blocks(first)
        second_blocks = floor_blocks(second)

        self.assertEqual(first_once, first_twice)
        self.assertEqual(len(first_once), 9)
        self.assertNotEqual(first_once, second_blocks)
        for boundary_index in (0, 2, 6, 8):
            self.assertEqual(first_once[boundary_index], second_blocks[boundary_index])

    def test_floor_blocks_stay_inside_one_logical_tile(self) -> None:
        for asset in self.profile.assets_of_kind("floor"):
            for block in floor_blocks(asset):
                self.assertGreater(block.width, 0.17)
                self.assertLess(block.width, 0.42)
                self.assertGreater(block.depth, 0.28)
                self.assertLess(block.depth, 0.34)
                self.assertGreaterEqual(block.center_x - block.width * 0.5, -0.51)
                self.assertLessEqual(block.center_x + block.width * 0.5, 0.51)
                self.assertGreaterEqual(block.center_y - block.depth * 0.5, -0.51)
                self.assertLessEqual(block.center_y + block.depth * 0.5, 0.51)

    def test_overlay_plans_are_deterministic_and_bounded(self) -> None:
        crack = self.profile.asset("stone_crack_01")
        dust = self.profile.asset("stone_dust_01")
        damp = self.profile.asset("stone_damp_01")
        transition = self.profile.asset("dry_to_damp_north")

        self.assertEqual(crack_segments(crack), crack_segments(crack))
        self.assertEqual(len(crack_segments(crack)), 6)
        self.assertEqual(len(dust_spots(dust)), 18)
        self.assertEqual(len(damp_spots(damp)), 12)
        self.assertEqual(len(damp_spots(transition, count=18)), 18)
        for spot in (*dust_spots(dust), *damp_spots(damp)):
            self.assertGreaterEqual(spot.center_x, -0.5)
            self.assertLessEqual(spot.center_x, 0.5)
            self.assertGreaterEqual(spot.center_y, -0.5)
            self.assertLessEqual(spot.center_y, 0.5)


if __name__ == "__main__":
    unittest.main()
