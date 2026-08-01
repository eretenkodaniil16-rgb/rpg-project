from __future__ import annotations

import unittest

from head_profile_v16 import HUMAN_WARRIOR_M01_HEAD_V16
from head_profile_v17 import HUMAN_WARRIOR_M01_HEAD_V17, load_head_profile_v17


class HeadProfileV17Tests(unittest.TestCase):
    def test_revision_advances_without_changing_locked_identity_data(self) -> None:
        profile = load_head_profile_v17("human_warrior_m01")
        self.assertEqual(profile.revision, "v17")
        self.assertEqual(profile.proxy_revision, "v20")
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
                getattr(HUMAN_WARRIOR_M01_HEAD_V16, field_name),
            )
        profile.assert_valid()

    def test_previous_revision_is_not_mutated(self) -> None:
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V16.revision, "v16")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V16.proxy_revision, "v19")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V17.character_id, "human_warrior_m01")

    def test_unknown_character_cannot_use_v17_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v17 profile"):
            load_head_profile_v17("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
