from __future__ import annotations

import unittest

from hair_forelock_profile_v08 import HUMAN_WARRIOR_M01_HAIR_FORELOCK_V08
from hair_forelock_profile_v11 import (
    HUMAN_WARRIOR_M01_HAIR_FORELOCK_V11,
    load_hair_forelock_profile_v11,
)


class HairForelockProfileV11Tests(unittest.TestCase):
    def test_profile_keeps_single_mesh_topology_and_advances_revision(self) -> None:
        profile = load_hair_forelock_profile_v11()
        self.assertEqual(profile.revision, "v11")
        self.assertEqual(profile.proxy_revision, "v14")
        self.assertEqual(profile.mesh_name, HUMAN_WARRIOR_M01_HAIR_FORELOCK_V08.mesh_name)
        self.assertEqual(len(profile.slices), 3)
        self.assertTrue(all(len(item.points_xz) == 7 for item in profile.slices))

    def test_forelock_projects_farther_and_breaks_left_hairline(self) -> None:
        current = HUMAN_WARRIOR_M01_HAIR_FORELOCK_V11.slices[0]
        previous = HUMAN_WARRIOR_M01_HAIR_FORELOCK_V08.slices[0]
        self.assertLess(current.y, previous.y)
        self.assertLess(
            min(point[1] for point in current.points_xz),
            min(point[1] for point in previous.points_xz),
        )
        self.assertLess(
            min(point[0] for point in current.points_xz),
            min(point[0] for point in previous.points_xz),
        )

    def test_tip_remains_on_physical_character_left(self) -> None:
        front = HUMAN_WARRIOR_M01_HAIR_FORELOCK_V11.slices[0].points_xz
        lowest = min(front, key=lambda point: point[1])
        self.assertLess(lowest[0], 0.0)
        self.assertTrue(all(point[0] <= 0.04 for point in front))


if __name__ == "__main__":
    unittest.main()
