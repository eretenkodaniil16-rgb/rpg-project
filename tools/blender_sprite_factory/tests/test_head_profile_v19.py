from __future__ import annotations

import unittest

from head_profile_v18 import HUMAN_WARRIOR_M01_HEAD_V18
from head_profile_v19 import HUMAN_WARRIOR_M01_HEAD_V19, load_head_profile_v19


class HeadProfileV19Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_identity_data(self) -> None:
        profile = load_head_profile_v19("human_warrior_m01")
        self.assertEqual(profile.revision, "v19")
        self.assertEqual(profile.proxy_revision, "v22")
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
                getattr(HUMAN_WARRIOR_M01_HEAD_V18, field_name),
            )
        profile.assert_valid()

    def test_previous_revision_is_not_mutated(self) -> None:
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V18.revision, "v18")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V18.proxy_revision, "v21")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V19.character_id, "human_warrior_m01")

    def test_unknown_character_cannot_use_v19_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v19 profile"):
            load_head_profile_v19("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
