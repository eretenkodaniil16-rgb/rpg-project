from __future__ import annotations

import unittest

from head_profile_v10 import HUMAN_WARRIOR_M01_HEAD_V10
from head_profile_v11 import HUMAN_WARRIOR_M01_HEAD_V11, load_head_profile_v11


class HeadProfileV11Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_head_or_face_geometry(self) -> None:
        profile = load_head_profile_v11("human_warrior_m01")
        self.assertEqual(profile.revision, "v11")
        self.assertEqual(profile.proxy_revision, "v14")
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
                getattr(HUMAN_WARRIOR_M01_HEAD_V10, field_name),
            )
        self.assertIs(profile, HUMAN_WARRIOR_M01_HEAD_V11)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            load_head_profile_v11("unknown")


if __name__ == "__main__":
    unittest.main()
