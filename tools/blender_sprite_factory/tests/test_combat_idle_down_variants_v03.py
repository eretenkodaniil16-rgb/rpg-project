from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_profile_v01 import HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01
from combat_idle_down_variants_profile_v03 import (
    load_combat_idle_down_variants_profile_v03,
)


class CombatIdleDownVariantsV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_down_variants_profile_v03(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_variants_builder_v03.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_combat_idle_down_variants_v03.py"
        ).read_text(encoding="utf-8")

    def test_profile_contains_three_centered_static_variants(self) -> None:
        self.assertEqual(self.profile.revision, "v03")
        self.assertEqual(
            tuple(item.variant_id for item in self.profile.variants),
            ("center_low", "center_mid", "center_vertical"),
        )
        self.assertEqual(len(self.profile.variants), 3)

    def test_left_arm_stays_open_while_blade_rotation_moves_inward(self) -> None:
        baseline = HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01.pose
        for item in self.profile.variants:
            with self.subTest(variant=item.variant_id):
                self.assertGreater(
                    item.pose.upper_arm_left_z_degrees,
                    baseline.upper_arm_left_z_degrees,
                )
                self.assertLess(
                    item.pose.hand_right_z_degrees,
                    baseline.hand_right_z_degrees,
                )
                self.assertLessEqual(abs(item.pose.upper_arm_left_x_degrees), 18.0)

    def test_centering_progresses_monotonically(self) -> None:
        upper_arm_z = tuple(
            item.pose.upper_arm_right_z_degrees for item in self.profile.variants
        )
        hand_z = tuple(item.pose.hand_right_z_degrees for item in self.profile.variants)
        self.assertEqual(upper_arm_z, tuple(sorted(upper_arm_z, reverse=True)))
        self.assertEqual(hand_z, tuple(sorted(hand_z, reverse=True)))

    def test_builder_reuses_v01_weapon_and_marks_v02_rejected(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "base_builder.create_combat_idle_down_actions_v01(context)",
            self.builder_source,
        )
        self.assertIn('action["centered_sword_correction"] = True', self.builder_source)
        self.assertIn('action["rejected_variant_source_revision"] = "v02"', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_remains_reproducible_as_centered_historical_pass(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("blade_moved_outward_instead_of_toward_center", self.adapter_source)
        self.assertIn("combat_idle_down_variants_v03.png", self.adapter_source)
        self.assertIn("right_hand_rotates_blade_toward_center", self.adapter_source)
        self.assertIn("technical_variant_set_requires_manual_selection", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_historical_v03_remains_while_active_stage_advances_to_v06(self) -> None:
        launcher = (self.tool_root / "run_blender_sprite_pilot.ps1").read_text(
            encoding="ascii"
        )
        workflow = (
            self.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-blender-sprite-factory.yml"
        ).read_text(encoding="utf-8")
        self.assertTrue(
            (
                self.tool_root
                / "blender_sprite_factory_combat_idle_down_variants_v03.py"
            ).is_file()
        )
        self.assertIn(
            "Previous visual candidate: blender_sprite_factory_combat_idle_down_weapon_variants_v05.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-variants-v03", workflow)
        self.assertIn("render-combat-idle-down-weapon-variants-v06", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat_idle_down variants v03"):
            load_combat_idle_down_variants_profile_v03("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
