from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_weapon_variants_profile_v06 import (
    BLADE_TIP_LENGTH,
    ONE_HAND_BLADE_LENGTH,
    TWO_HAND_AWAY_Y,
    TWO_HAND_BLADE_LENGTH,
    TWO_HAND_CENTER_X_OFFSET,
    load_weapon_stance_profile_v06,
)


class CombatIdleDownWeaponVariantsV06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_weapon_stance_profile_v06("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_weapon_variants_builder_v06.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_down_weapon_variants_v06.py"
        ).read_text(encoding="utf-8")

    def test_profile_advances_same_four_stances_to_v06(self) -> None:
        self.assertEqual(self.profile.revision, "v06")
        self.assertEqual(
            tuple(item.variant_id for item in self.profile.variants),
            (
                "onehand_low",
                "onehand_ready",
                "twohand_center_low",
                "twohand_center_high",
            ),
        )
        self.assertTrue(
            all(item.animation_id.endswith("_v06") for item in self.profile.variants)
        )

    def test_corrected_blades_exceed_v05_lengths_and_use_pointed_tips(self) -> None:
        self.assertGreater(ONE_HAND_BLADE_LENGTH, 1.82)
        self.assertGreater(TWO_HAND_BLADE_LENGTH, 2.12)
        self.assertGreater(TWO_HAND_BLADE_LENGTH, ONE_HAND_BLADE_LENGTH)
        self.assertGreaterEqual(BLADE_TIP_LENGTH, 0.18)

    def test_two_hand_axis_stays_near_center_but_angles_away_from_face(self) -> None:
        self.assertGreaterEqual(TWO_HAND_CENTER_X_OFFSET, 0.05)
        self.assertLessEqual(TWO_HAND_CENTER_X_OFFSET, 0.15)
        self.assertGreater(TWO_HAND_AWAY_Y, 0.0)

    def test_builder_uses_separate_pose_fitted_two_hand_modules(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("TWO_HAND_LOW_V06_OBJECT_NAMES", self.builder_source)
        self.assertIn("TWO_HAND_HIGH_V06_OBJECT_NAMES", self.builder_source)
        self.assertIn("two_hand_separate_pose_fitted_modules", self.builder_source)
        self.assertIn("_pointed_tip", self.builder_source)
        self.assertIn("MAT_combat_sword_highlight_v06", self.builder_source)
        self.assertIn('factory.Vector((0.045, TWO_HAND_AWAY_Y, 1.0))', self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_rejects_v05_visual_issue_and_records_v06_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "two_hand_blade_crossed_face_and_tip_did_not_clear_head",
            self.adapter_source,
        )
        self.assertIn("combat_idle_down_weapon_variants_v06.png", self.adapter_source)
        self.assertIn("two_hand_blade_angled_away_from_face", self.adapter_source)
        self.assertIn("pointed_tips_used", self.adapter_source)
        self.assertIn("weapon_highlight_strips_used", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_v06_remains_reproducible_while_active_stage_uses_v07(self) -> None:
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
                / "blender_sprite_factory_combat_idle_down_weapon_variants_v06.py"
            ).is_file()
        )
        self.assertIn(
            "blender_sprite_factory_combat_idle_down_weapon_variants_v07.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-weapon-variants-v06", workflow)
        self.assertIn("render-combat-idle-down-weapon-variants-v07", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No weapon stance v06"):
            load_weapon_stance_profile_v06("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
