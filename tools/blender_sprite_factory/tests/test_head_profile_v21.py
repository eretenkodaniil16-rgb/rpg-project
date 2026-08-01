from __future__ import annotations

import unittest

from head_profile_v20 import HUMAN_WARRIOR_M01_HEAD_V20
from head_profile_v21 import HUMAN_WARRIOR_M01_HEAD_V21, load_head_profile_v21


class HeadProfileV21Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_identity(self) -> None:
        profile = load_head_profile_v21("human_warrior_m01")
        self.assertEqual(profile.revision, "v21")
        self.assertEqual(profile.proxy_revision, "v24")
        for field_name in (
            "head_base",
            "jaw",
            "ears",
            "nose",
            "brows",
            "eyes",
            "mouth",
            "hair_cap",
            "hair_back_masses",
            "hair_front_locks",
            "hair_side_locks",
        ):
            self.assertEqual(
                getattr(profile, field_name),
                getattr(HUMAN_WARRIOR_M01_HEAD_V20, field_name),
            )
        profile.assert_valid()

    def test_previous_revision_is_not_mutated(self) -> None:
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V20.revision, "v20")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V20.proxy_revision, "v23")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V21.character_id, "human_warrior_m01")

    def test_unknown_character_cannot_use_v21_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v21 profile"):
            load_head_profile_v21("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
