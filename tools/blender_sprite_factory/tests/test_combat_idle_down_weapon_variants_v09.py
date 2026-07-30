from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_weapon_variants_profile_v08 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V08,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    ONE_HAND_BEHIND_Y,
    ONE_HAND_DOWN_Z,
    ONE_HAND_SIDE_X,
    load_weapon_stance_profile_v09,
)


class CombatIdleDownWeaponVariantsV09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_weapon_stance_profile_v09("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_weapon_variants_builder_v09.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_down_weapon_variants_v09.py"
        ).read_text(encoding="utf-8")

    def test_only_one_hand_variants_advance_to_v09(self) -> None:
        self.assertEqual(self.profile.revision, "v09")
        self.assertEqual(
            tuple(item.animation_id for item in self.profile.variants),
            (
                "combat_idle_onehand_low_v09",
                "combat_idle_onehand_ready_v09",
                "combat_idle_twohand_center_low_v06",
                "combat_idle_twohand_center_high_v06",
            ),
        )

    def test_body_poses_and_two_hand_variants_are_unchanged(self) -> None:
        previous = HUMAN_WARRIOR_M01_WEAPON_STANCES_V08.variants
        for index, item in enumerate(self.profile.variants):
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.pose, previous[index].pose)
        self.assertEqual(self.profile.variants[2:], previous[2:])

    def test_one_hand_direction_leaves_physical_right_side_and_remains_behind(self) -> None:
        self.assertLess(ONE_HAND_SIDE_X, 0.0)
        self.assertGreater(abs(ONE_HAND_SIDE_X), ONE_HAND_BEHIND_Y * 2.0)
        self.assertGreaterEqual(ONE_HAND_BEHIND_Y, 0.24)
        self.assertLessEqual(ONE_HAND_BEHIND_Y, 0.40)
        self.assertLessEqual(ONE_HAND_DOWN_Z, -0.70)
        for item in self.profile.variants[:2]:
            with self.subTest(variant=item.variant_id):
                self.assertEqual(item.blade_tip, "down")
                self.assertEqual(item.weapon_id, "sword_01_onehand_outward_back_v09")
                self.assertGreaterEqual(item.pose.upper_arm_left_z_degrees, 26.0)

    def test_builder_adds_only_pose_fitted_one_hand_v09_modules(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "previous_builder.create_weapon_stance_actions_v08(context)",
            self.builder_source,
        )
        self.assertIn("ONE_HAND_LOW_V09_OBJECT_NAMES", self.builder_source)
        self.assertIn("ONE_HAND_READY_V09_OBJECT_NAMES", self.builder_source)
        self.assertIn(
            "(ONE_HAND_SIDE_X, ONE_HAND_BEHIND_Y, ONE_HAND_DOWN_Z)",
            self.builder_source,
        )
        self.assertIn(
            "combat_idle_one_hand_v08_rejected_for_cross_torso_projection",
            self.builder_source,
        )
        self.assertIn("combat_idle_two_hand_geometry_unchanged", self.builder_source)
        self.assertNotIn("_build_two_hand_v09", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_reuses_exact_v06_two_hand_actions_and_modules(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("TWO_HAND_LOW_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn("TWO_HAND_HIGH_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn('"combat_idle_twohand_center_low_v06"', self.adapter_source)
        self.assertIn('"combat_idle_twohand_center_high_v06"', self.adapter_source)
        self.assertIn("two_hand_v06_preserved_exactly", self.adapter_source)
        self.assertIn(
            "blade_projected_across_lower_torso_instead_of_outward_side",
            self.adapter_source,
        )
        self.assertIn(
            "one_hand_blade_physical_right_outward_and_partly_behind",
            self.adapter_source,
        )
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_v09_remains_selected_static_source_under_v12(self) -> None:
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
            "Selected static source adapter: blender_sprite_factory_combat_idle_down_weapon_variants_v09.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-weapon-variants-v09", workflow)
        self.assertIn(
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_combat_idle_directional_weapon_v12.py"',
            launcher,
        )
        self.assertIn("render-combat-idle-directional-weapon-v12", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No weapon stance v09"):
            load_weapon_stance_profile_v09("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
