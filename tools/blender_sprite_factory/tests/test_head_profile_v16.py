from __future__ import annotations

import unittest

from head_profile_v15 import HUMAN_WARRIOR_M01_HEAD_V15
from head_profile_v16 import HUMAN_WARRIOR_M01_HEAD_V16, load_head_profile_v16


class HeadProfileV16Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_identity(self) -> None:
        profile = load_head_profile_v16("human_warrior_m01")
        self.assertEqual(profile.revision, "v16")
        self.assertEqual(profile.proxy_revision, "v19")
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
                getattr(HUMAN_WARRIOR_M01_HEAD_V15, field_name),
            )
        self.assertEqual(profile, HUMAN_WARRIOR_M01_HEAD_V16)
        profile.assert_valid()

    def test_unknown_character_cannot_use_v16_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v16 profile"):
            load_head_profile_v16("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
