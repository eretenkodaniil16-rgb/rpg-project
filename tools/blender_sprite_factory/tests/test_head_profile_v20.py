from __future__ import annotations

import unittest

from head_profile_v18 import HUMAN_WARRIOR_M01_HEAD_V18
from head_profile_v19 import HUMAN_WARRIOR_M01_HEAD_V19
from head_profile_v20 import HUMAN_WARRIOR_M01_HEAD_V20, load_head_profile_v20


class HeadProfileV20Tests(unittest.TestCase):
    def test_revision_advances_from_accepted_v18_identity(self) -> None:
        profile = load_head_profile_v20("human_warrior_m01")
        self.assertEqual(profile.revision, "v20")
        self.assertEqual(profile.proxy_revision, "v23")
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

    def test_rejected_v19_is_preserved_but_not_used_as_identity_parent(self) -> None:
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V19.proxy_revision, "v22")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V20.character_id, "human_warrior_m01")
        self.assertEqual(
            HUMAN_WARRIOR_M01_HEAD_V20.head_base,
            HUMAN_WARRIOR_M01_HEAD_V18.head_base,
        )

    def test_unknown_character_cannot_use_v20_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head v20 profile"):
            load_head_profile_v20("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
