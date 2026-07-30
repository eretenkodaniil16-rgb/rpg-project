from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_weapon_variants_profile_v06 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V06,
)
from combat_idle_down_weapon_variants_profile_v07 import (
    ONE_HAND_BEHIND_Y,
    ONE_HAND_DOWN_Z,
    ONE_HAND_SIDE_X,
    load_weapon_stance_profile_v07,
)


class CombatIdleDownWeaponVariantsV07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_weapon_stance_profile_v07("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_weapon_variants_builder_v07.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_down_weapon_variants_v07.py"
        ).read_text(encoding="utf-8")

    def test_only_one_hand_variants_advance_to_v07(self) -> None:
        self.assertEqual(self.profile.revision, "v07")
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
            tuple(item.animation_id for item in self.profile.variants),
            (
                "combat_idle_onehand_low_v07",
                "combat_idle_onehand_ready_v07",
                "combat_idle_twohand_center_low_v06",
                "combat_idle_twohand_center_high_v06",
            ),
        )

    def test_body_poses_and_two_hand_variants_are_exact_v06(self) -> None:
        previous = HUMAN_WARRIOR_M01_WEAPON_STANCES_V06.variants
        for index, item in enumerate(self.profile.variants):
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.pose, previous[index].pose)
        self.assertEqual(self.profile.variants[2:], previous[2:])

    def test_one_hand_direction_moves_side_behind_and_down(self) -> None:
        self.assertGreaterEqual(ONE_HAND_SIDE_X, 0.55)
        self.assertGreaterEqual(ONE_HAND_BEHIND_Y, 0.45)
        self.assertLessEqual(ONE_HAND_DOWN_Z, -0.58)
        for item in self.profile.variants[:2]:
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.blade_tip, "down")
                self.assertEqual(item.weapon_id, "sword_01_onehand_backside_v07")
                self.assertGreaterEqual(item.pose.upper_arm_left_z_degrees, 26.0)

    def test_builder_adds_pose_fitted_one_hand_modules_only(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "previous_builder.create_weapon_stance_actions_v06(context)",
            self.builder_source,
        )
        self.assertIn("ONE_HAND_LOW_V07_OBJECT_NAMES", self.builder_source)
        self.assertIn("ONE_HAND_READY_V07_OBJECT_NAMES", self.builder_source)
        self.assertIn(
            "(ONE_HAND_SIDE_X, ONE_HAND_BEHIND_Y, ONE_HAND_DOWN_Z)",
            self.builder_source,
        )
        self.assertIn("combat_idle_two_hand_geometry_unchanged", self.builder_source)
        self.assertNotIn("_build_two_hand_v07", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_reuses_exact_v06_two_hand_actions_and_modules(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("TWO_HAND_LOW_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn("TWO_HAND_HIGH_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn('"combat_idle_twohand_center_low_v06"', self.adapter_source)
        self.assertIn('"combat_idle_twohand_center_high_v06"', self.adapter_source)
        self.assertIn("two_hand_v06_preserved_exactly", self.adapter_source)
        self.assertIn("one_hand_blade_moves_side_and_behind", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_active_launcher_and_workflow_use_weapon_variants_v07(self) -> None:
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
            "blender_sprite_factory_combat_idle_down_weapon_variants_v07.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-weapon-variants-v07", workflow)
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_weapon_variants_v07.py",
            workflow,
        )

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No weapon stance v07"):
            load_weapon_stance_profile_v07("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
