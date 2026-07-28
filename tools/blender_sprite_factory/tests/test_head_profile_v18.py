from __future__ import annotations

import unittest

from head_profile_v17 import HUMAN_WARRIOR_M01_HEAD_V17
from head_profile_v18 import HUMAN_WARRIOR_M01_HEAD_V18, load_head_profile_v18


class HeadProfileV18Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_identity_data(self) -> None:
        profile = load_head_profile_v18("human_warrior_m01")
        self.assertEqual(profile.revision, "v18")
        self.assertEqual(profile.proxy_revision, "v21")
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
                getattr(HUMAN_WARRIOR_M01_HEAD_V17, field_name),
            )
        profile.assert_valid()

    def test_previous_revision_is_not_mutated(self) -> None:
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V17.revision, "v17")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V17.proxy_revision, "v20")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V18.character_id, "human_warrior_m01")

    def test_unknown_character_cannot_use_v18_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v18 profile"):
            load_head_profile_v18("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
