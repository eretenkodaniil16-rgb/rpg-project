from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_profile_v01 import HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01
from combat_idle_down_variants_profile_v02 import (
    load_combat_idle_down_variants_profile_v02,
)


class CombatIdleDownVariantsV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_down_variants_profile_v02(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_variants_builder_v02.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_combat_idle_down_variants_v02.py"
        ).read_text(encoding="utf-8")

    def test_profile_contains_three_ordered_static_variants(self) -> None:
        self.assertEqual(self.profile.revision, "v02")
        self.assertEqual(
            tuple(item.variant_id for item in self.profile.variants),
            ("center_low", "center_mid", "diagonal_guard"),
        )
        self.assertEqual(len(self.profile.variants), 3)
        self.profile.assert_valid()

    def test_all_variants_open_arms_and_move_weapon_arm_inward(self) -> None:
        baseline = HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01.pose
        for item in self.profile.variants:
            with self.subTest(variant=item.variant_id):
                self.assertGreater(
                    item.pose.upper_arm_left_z_degrees,
                    baseline.upper_arm_left_z_degrees,
                )
                self.assertGreater(
                    item.pose.upper_arm_right_z_degrees,
                    baseline.upper_arm_right_z_degrees,
                )
                self.assertLessEqual(abs(item.pose.upper_arm_left_x_degrees), 18.0)

    def test_sword_moves_progressively_toward_active_center_guard(self) -> None:
        right_arm_z = tuple(
            item.pose.upper_arm_right_z_degrees for item in self.profile.variants
        )
        hand_z = tuple(item.pose.hand_right_z_degrees for item in self.profile.variants)
        self.assertEqual(right_arm_z, tuple(sorted(right_arm_z)))
        self.assertEqual(hand_z, tuple(sorted(hand_z)))

    def test_builder_extends_v01_without_rebuilding_approved_walk_set(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "base_builder.create_combat_idle_down_actions_v01(context)",
            self.builder_source,
        )
        self.assertIn('action["approved_walk_set_unchanged"] = True', self.builder_source)
        self.assertIn('action["weapon_hand"] = "right"', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_keeps_v01_as_baseline_and_writes_comparison_sheet(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("BASE_RENDER", self.adapter_source)
        self.assertIn('"combat_idle"', self.adapter_source)
        self.assertIn("combat_idle_down_variants_v02.png", self.adapter_source)
        self.assertIn("single_shared_scale_and_baseline", self.adapter_source)
        self.assertIn("technical_variant_set_requires_manual_selection", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_active_launcher_and_workflow_use_variants_v02(self) -> None:
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
            "blender_sprite_factory_combat_idle_down_variants_v02.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-variants-v02", workflow)
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_variants_v02.py",
            workflow,
        )

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat_idle_down variants v02"):
            load_combat_idle_down_variants_profile_v02("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
