from __future__ import annotations

import unittest

from head_profile_v21 import HUMAN_WARRIOR_M01_HEAD_V21
from head_profile_v22 import HUMAN_WARRIOR_M01_HEAD_V22, load_head_profile_v22


class HeadProfileV22Tests(unittest.TestCase):
    def test_revision_advances_without_identity_drift(self) -> None:
        profile = load_head_profile_v22("human_warrior_m01")
        self.assertEqual(profile.revision, "v22")
        self.assertEqual(profile.proxy_revision, "v25")
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
            self.assertEqual(getattr(profile, field_name), getattr(HUMAN_WARRIOR_M01_HEAD_V21, field_name))
        HUMAN_WARRIOR_M01_HEAD_V22.assert_valid()

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v22 profile"):
            load_head_profile_v22("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
