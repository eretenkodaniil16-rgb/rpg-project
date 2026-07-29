from __future__ import annotations

import unittest

from appearance_readability_profile_v01 import (
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01,
    load_appearance_readability_profile_v01,
)


class AppearanceReadabilityProfileV01Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_appearance_readability_profile_v01("human_warrior_m01")

    def test_revision_and_contract(self) -> None:
        self.assertEqual(self.profile.revision, "v01")
        self.assertEqual(self.profile.head_revision, "v22")
        self.assertEqual(self.profile.proxy_revision, "v25")
        self.profile.assert_valid()

    def test_hair_density_is_increased_without_mirroring(self) -> None:
        self.assertEqual(len(self.profile.hair_transforms), 5)
        self.assertEqual(len(self.profile.temple_fills), 2)
        for transform in self.profile.hair_transforms:
            self.assertTrue(all(value >= 1.0 for value in transform.scale_multiplier))
        left = next(item for item in self.profile.temple_fills if item.physical_side == "left")
        right = next(item for item in self.profile.temple_fills if item.physical_side == "right")
        self.assertNotEqual(left.scale, right.scale)
        self.assertNotEqual(left.rotation_degrees, tuple(-value for value in right.rotation_degrees))

    def test_scarf_and_clothing_colors_are_quantized_explicitly(self) -> None:
        additions = set(self.profile.quantization_additions)
        self.assertIn("#741522", additions)
        self.assertIn("#A83242", additions)
        self.assertEqual(self.profile.material_override_map()["scarf"], "#741522")
        self.assertEqual(self.profile.scarf_highlight_hex, "#A83242")
        self.assertTrue(set(self.profile.material_override_map().values()).issubset(additions))

    def test_clothing_accents_are_small_and_stable(self) -> None:
        self.assertEqual(
            {item.name for item in self.profile.clothing_details},
            {"armor_chest_lower_trim", "belt_buckle_front"},
        )
        self.assertEqual(
            {item.name for item in self.profile.object_transforms},
            {"scarf_wrap", "scarf_front", "armor_chest", "belt"},
        )

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No appearance readability v01 profile"):
            load_appearance_readability_profile_v01("elf_warrior_m01")

    def test_constant_instance_remains_valid(self) -> None:
        HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01.assert_valid()


if __name__ == "__main__":
    unittest.main()
