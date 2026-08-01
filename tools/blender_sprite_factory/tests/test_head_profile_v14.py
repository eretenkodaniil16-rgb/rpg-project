from __future__ import annotations

import unittest

from head_profile_v13 import HUMAN_WARRIOR_M01_HEAD_V13
from head_profile_v14 import HUMAN_WARRIOR_M01_HEAD_V14, load_head_profile_v14


class HeadProfileV14Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_character_geometry(self) -> None:
        profile = load_head_profile_v14("human_warrior_m01")
        self.assertEqual(profile.revision, "v14")
        self.assertEqual(profile.proxy_revision, "v17")
        for field_name in (
            "head_base",
            "jaw",
            "ears",
            "nose",
            "hair_cap",
            "hair_back_masses",
            "hair_front_locks",
            "hair_side_locks",
            "brows",
            "eyes",
            "mouth",
        ):
            self.assertEqual(
                getattr(profile, field_name),
                getattr(HUMAN_WARRIOR_M01_HEAD_V13, field_name),
            )
        self.assertIs(profile, HUMAN_WARRIOR_M01_HEAD_V14)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            load_head_profile_v14("unknown")


if __name__ == "__main__":
    unittest.main()
