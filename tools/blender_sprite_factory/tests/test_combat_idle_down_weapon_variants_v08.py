from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_weapon_variants_profile_v07 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V07,
)
from combat_idle_down_weapon_variants_profile_v08 import (
    ONE_HAND_BEHIND_Y,
    ONE_HAND_DOWN_Z,
    ONE_HAND_SIDE_X,
    load_weapon_stance_profile_v08,
)


class CombatIdleDownWeaponVariantsV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_weapon_stance_profile_v08("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_weapon_variants_builder_v08.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_down_weapon_variants_v08.py"
        ).read_text(encoding="utf-8")

    def test_only_one_hand_variants_advance_to_v08(self) -> None:
        self.assertEqual(self.profile.revision, "v08")
        self.assertEqual(
            tuple(item.animation_id for item in self.profile.variants),
            (
                "combat_idle_onehand_low_v08",
                "combat_idle_onehand_ready_v08",
                "combat_idle_twohand_center_low_v06",
                "combat_idle_twohand_center_high_v06",
            ),
        )

    def test_body_poses_and_two_hand_variants_are_unchanged(self) -> None:
        previous = HUMAN_WARRIOR_M01_WEAPON_STANCES_V07.variants
        for index, item in enumerate(self.profile.variants):
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.pose, previous[index].pose)
        self.assertEqual(self.profile.variants[2:], previous[2:])

    def test_one_hand_direction_favors_side_visibility_but_remains_behind(self) -> None:
        self.assertGreaterEqual(ONE_HAND_SIDE_X, 0.78)
        self.assertGreater(ONE_HAND_SIDE_X, ONE_HAND_BEHIND_Y * 2.0)
        self.assertGreaterEqual(ONE_HAND_BEHIND_Y, 0.22)
        self.assertLessEqual(ONE_HAND_BEHIND_Y, 0.38)
        self.assertLessEqual(ONE_HAND_DOWN_Z, -0.54)
        for item in self.profile.variants[:2]:
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.blade_tip, "down")
                self.assertEqual(item.weapon_id, "sword_01_onehand_side_back_v08")
                self.assertGreaterEqual(item.pose.upper_arm_left_z_degrees, 26.0)

    def test_builder_adds_only_pose_fitted_one_hand_v08_modules(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "previous_builder.create_weapon_stance_actions_v07(context)",
            self.builder_source,
        )
        self.assertIn("ONE_HAND_LOW_V08_OBJECT_NAMES", self.builder_source)
        self.assertIn("ONE_HAND_READY_V08_OBJECT_NAMES", self.builder_source)
        self.assertIn(
            "(ONE_HAND_SIDE_X, ONE_HAND_BEHIND_Y, ONE_HAND_DOWN_Z)",
            self.builder_source,
        )
        self.assertIn("combat_idle_one_hand_v07_rejected_for_occlusion", self.builder_source)
        self.assertIn("combat_idle_two_hand_geometry_unchanged", self.builder_source)
        self.assertNotIn("_build_two_hand_v08", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_reuses_exact_v06_two_hand_actions_and_modules(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("TWO_HAND_LOW_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn("TWO_HAND_HIGH_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn('"combat_idle_twohand_center_low_v06"', self.adapter_source)
        self.assertIn('"combat_idle_twohand_center_high_v06"', self.adapter_source)
        self.assertIn("two_hand_v06_preserved_exactly", self.adapter_source)
        self.assertIn("blade_was_over_occluded_behind_torso", self.adapter_source)
        self.assertIn("one_hand_blade_lateral_and_partly_behind", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_v08_adapter_remains_reproducible_after_v09_activation(self) -> None:
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
            "blender_sprite_factory_combat_idle_down_weapon_variants_v08.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-weapon-variants-v08", workflow)
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_weapon_variants_v09.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-weapon-variants-v09", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No weapon stance v08"):
            load_weapon_stance_profile_v08("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
