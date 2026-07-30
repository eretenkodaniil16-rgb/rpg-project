from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_profile_v01 import HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01
from combat_idle_down_variants_profile_v04 import (
    load_combat_idle_down_variants_profile_v04,
)


class CombatIdleDownVariantsV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_down_variants_profile_v04(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_variants_builder_v04.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_combat_idle_down_variants_v04.py"
        ).read_text(encoding="utf-8")

    def test_profile_contains_three_wide_side_static_variants(self) -> None:
        self.assertEqual(self.profile.revision, "v04")
        self.assertEqual(
            tuple(item.variant_id for item in self.profile.variants),
            ("wide_low", "wide_ready", "wide_high"),
        )
        self.assertEqual(len(self.profile.variants), 3)

    def test_both_arms_move_away_from_torso_center(self) -> None:
        baseline = HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01.pose
        for item in self.profile.variants:
            with self.subTest(variant=item.variant_id):
                self.assertGreaterEqual(item.pose.upper_arm_left_z_degrees, 18.0)
                self.assertGreaterEqual(item.pose.upper_arm_right_z_degrees, 14.0)
                self.assertGreater(
                    item.pose.upper_arm_left_z_degrees,
                    baseline.upper_arm_left_z_degrees,
                )
                self.assertGreater(
                    item.pose.upper_arm_right_z_degrees,
                    baseline.upper_arm_right_z_degrees,
                )
                self.assertGreater(
                    item.pose.hand_right_z_degrees,
                    baseline.hand_right_z_degrees,
                )

    def test_side_opening_progresses_monotonically(self) -> None:
        left_arm_z = tuple(
            item.pose.upper_arm_left_z_degrees for item in self.profile.variants
        )
        right_arm_z = tuple(
            item.pose.upper_arm_right_z_degrees for item in self.profile.variants
        )
        hand_z = tuple(item.pose.hand_right_z_degrees for item in self.profile.variants)
        self.assertEqual(left_arm_z, tuple(sorted(left_arm_z)))
        self.assertEqual(right_arm_z, tuple(sorted(right_arm_z)))
        self.assertEqual(hand_z, tuple(sorted(hand_z)))

    def test_builder_reuses_v01_weapon_and_marks_centered_v03_rejected(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "base_builder.create_combat_idle_down_actions_v01(context)",
            self.builder_source,
        )
        self.assertIn('action["wide_side_guard"] = True', self.builder_source)
        self.assertIn(
            'action["supersedes_centered_revision"] = "v03"',
            self.builder_source,
        )
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_records_wide_side_contract_and_comparison(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("closed_guard_converged_toward_torso_center", self.adapter_source)
        self.assertIn("combat_idle_down_variants_v04.png", self.adapter_source)
        self.assertIn("both_arms_move_away_from_torso_center", self.adapter_source)
        self.assertIn(
            "technical_wide_side_variant_set_requires_manual_selection",
            self.adapter_source,
        )
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_v04_remains_reproducible_while_active_stage_uses_v06(self) -> None:
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
                / "blender_sprite_factory_combat_idle_down_variants_v04.py"
            ).is_file()
        )
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_weapon_variants_v06.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-variants-v04", workflow)
        self.assertIn("render-combat-idle-down-weapon-variants-v06", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat_idle_down variants v04"):
            load_combat_idle_down_variants_profile_v04("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
