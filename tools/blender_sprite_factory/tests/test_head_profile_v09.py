from __future__ import annotations

import unittest

from head_profile_v08 import HUMAN_WARRIOR_M01_HEAD_V08
from head_profile_v09 import HUMAN_WARRIOR_M01_HEAD_V09, load_head_profile_v09


class HeadProfileV09Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_head_geometry(self) -> None:
        profile = load_head_profile_v09("human_warrior_m01")
        self.assertEqual(profile.revision, "v09")
        self.assertEqual(profile.proxy_revision, "v12")
        self.assertEqual(profile.head_base, HUMAN_WARRIOR_M01_HEAD_V08.head_base)
        self.assertEqual(profile.jaw, HUMAN_WARRIOR_M01_HEAD_V08.jaw)
        self.assertEqual(profile.ears, HUMAN_WARRIOR_M01_HEAD_V08.ears)
        self.assertEqual(profile.nose, HUMAN_WARRIOR_M01_HEAD_V08.nose)
        self.assertEqual(profile.brows, HUMAN_WARRIOR_M01_HEAD_V08.brows)
        self.assertEqual(profile.eyes, HUMAN_WARRIOR_M01_HEAD_V08.eyes)
        self.assertEqual(profile.mouth, HUMAN_WARRIOR_M01_HEAD_V08.mouth)
        self.assertEqual(profile.hair_cap, HUMAN_WARRIOR_M01_HEAD_V08.hair_cap)
        self.assertEqual(profile.hair_back_masses, HUMAN_WARRIOR_M01_HEAD_V08.hair_back_masses)
        self.assertEqual(profile.hair_front_locks, HUMAN_WARRIOR_M01_HEAD_V08.hair_front_locks)
        self.assertEqual(profile.hair_side_locks, HUMAN_WARRIOR_M01_HEAD_V08.hair_side_locks)
        self.assertIs(profile, HUMAN_WARRIOR_M01_HEAD_V09)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            load_head_profile_v09("unknown")


if __name__ == "__main__":
    unittest.main()
