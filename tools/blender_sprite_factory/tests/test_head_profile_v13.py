from __future__ import annotations

import unittest

from head_profile_v12 import HUMAN_WARRIOR_M01_HEAD_V12
from head_profile_v13 import HUMAN_WARRIOR_M01_HEAD_V13, load_head_profile_v13


class HeadProfileV13Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_head_or_face_geometry(self) -> None:
        profile = load_head_profile_v13("human_warrior_m01")
        self.assertEqual(profile.revision, "v13")
        self.assertEqual(profile.proxy_revision, "v16")
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
                getattr(HUMAN_WARRIOR_M01_HEAD_V12, field_name),
            )
        self.assertIs(profile, HUMAN_WARRIOR_M01_HEAD_V13)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            load_head_profile_v13("unknown")


if __name__ == "__main__":
    unittest.main()
