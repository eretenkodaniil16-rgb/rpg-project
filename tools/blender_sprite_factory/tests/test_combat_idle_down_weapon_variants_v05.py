from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_weapon_variants_profile_v05 import (
    ONE_HAND_BLADE_LENGTH,
    TWO_HAND_BLADE_LENGTH,
    load_weapon_stance_profile_v05,
)


class CombatIdleDownWeaponVariantsV05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_weapon_stance_profile_v05("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_weapon_variants_builder_v05.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_down_weapon_variants_v05.py"
        ).read_text(encoding="utf-8")

    def test_profile_contains_two_one_hand_and_two_two_hand_variants(self) -> None:
        self.assertEqual(self.profile.revision, "v05")
        self.assertEqual(
            tuple(item.variant_id for item in self.profile.variants),
            (
                "onehand_low",
                "onehand_ready",
                "twohand_center_low",
                "twohand_center_high",
            ),
        )
        self.assertEqual(
            tuple(item.grip_mode for item in self.profile.variants),
            ("one_handed", "one_handed", "two_handed", "two_handed"),
        )

    def test_one_hand_variants_point_down_and_move_free_arm_away(self) -> None:
        for item in self.profile.variants[:2]:
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.blade_tip, "down")
                self.assertGreaterEqual(item.pose.upper_arm_left_z_degrees, 26.0)
                self.assertGreaterEqual(item.pose.forearm_left_z_degrees, 12.0)

    def test_two_hand_variants_are_centered_and_point_up(self) -> None:
        for item in self.profile.variants[2:]:
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.blade_tip, "up")
                self.assertEqual(item.grip_mode, "two_handed")
                self.assertEqual(item.weapon_id, "sword_02_twohand_long")
                self.assertLessEqual(abs(item.pose.upper_arm_left_z_degrees), 10.0)
                self.assertLessEqual(abs(item.pose.upper_arm_right_z_degrees), 10.0)

    def test_both_blades_are_longer_and_two_hand_is_longest(self) -> None:
        self.assertGreater(ONE_HAND_BLADE_LENGTH, 1.34)
        self.assertGreater(TWO_HAND_BLADE_LENGTH, ONE_HAND_BLADE_LENGTH)

    def test_builder_adds_hand_left_channel_and_separate_weapon_modules(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn('pose.bones["hand.L"].rotation_euler', self.builder_source)
        self.assertIn("ONE_HAND_LONG_OBJECT_NAMES", self.builder_source)
        self.assertIn("TWO_HAND_LONG_OBJECT_NAMES", self.builder_source)
        self.assertIn('factory.Vector((0.34, -0.18, -1.0))', self.builder_source)
        self.assertIn('factory.Vector((0.0, -0.08, 1.0))', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_toggles_weapon_family_and_records_manual_selection(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn('"one_handed": ONE_HAND_LONG_OBJECT_NAMES', self.adapter_source)
        self.assertIn('"two_handed": TWO_HAND_LONG_OBJECT_NAMES', self.adapter_source)
        self.assertIn("one_hand_free_arm_away_from_torso", self.adapter_source)
        self.assertIn("two_hand_blade_centered_tip_up", self.adapter_source)
        self.assertIn("technical_weapon_variant_set_requires_manual_selection", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_active_launcher_and_workflow_use_weapon_variants_v05(self) -> None:
        launcher = (self.tool_root / "run_blender_sprite_pilot.ps1").read_text(
            encoding="ascii"
        )
        workflow = (
            self.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-blender-sprite-factory.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_weapon_variants_v05.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-weapon-variants-v05", workflow)
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_weapon_variants_v05.py",
            workflow,
        )

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No weapon stance v05"):
            load_weapon_stance_profile_v05("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
