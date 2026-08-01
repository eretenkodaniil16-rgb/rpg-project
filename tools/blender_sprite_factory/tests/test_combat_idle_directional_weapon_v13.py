from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_directional_weapon_profile_v13 import (
    load_combat_idle_directional_weapon_profile_v13,
)


class CombatIdleDirectionalWeaponV13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_directional_weapon_profile_v13(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder = (
            cls.tool_root / "combat_idle_directional_weapon_builder_v13.py"
        ).read_text(encoding="utf-8")
        cls.adapter = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_directional_weapon_v13.py"
        ).read_text(encoding="utf-8")

    def test_only_onehand_left_and_right_are_corrected(self) -> None:
        self.assertEqual(self.profile.revision, "v13")
        self.assertEqual(
            tuple(item.direction for item in self.profile.corrected_sides),
            ("left", "right"),
        )
        self.assertEqual(self.profile.locked_directions, ("down", "up"))
        for item in self.profile.corrected_sides:
            self.assertGreaterEqual(item.minimum_sprite_width, 45)
            self.assertLess(item.blade_vector[2], -0.65)
            self.assertLessEqual(max(abs(value) for value in item.anchor_offset), 0.35)

    def test_builder_adds_side_weapon_modules_without_actions(self) -> None:
        ast.parse(self.builder)
        self.assertIn("create_combat_idle_directional_weapon_v12(context)", self.builder)
        self.assertIn("ONE_HAND_LEFT_V13_OBJECT_NAMES", self.builder)
        self.assertIn("ONE_HAND_RIGHT_V13_OBJECT_NAMES", self.builder)
        self.assertIn("anchor_offset_applied", self.builder)
        self.assertNotIn("factory._new_action", self.builder)
        self.assertNotIn("scale.x = -1", self.builder)

    def test_adapter_locks_down_up_and_twohand_pixels(self) -> None:
        ast.parse(self.adapter)
        self.assertIn(
            'candidate_id == "twohand_center_high" or direction in profile.locked_directions',
            self.adapter,
        )
        self.assertIn("changed locked pixels", self.adapter)
        self.assertIn("all_twohand_pixels_unchanged", self.adapter)
        self.assertIn("down_and_up_onehand_pixels_unchanged", self.adapter)

    def test_side_candidates_have_visibility_and_boundary_contracts(self) -> None:
        self.assertIn("_assert_no_boundary_touch", self.adapter)
        self.assertIn("below {correction.minimum_sprite_width}px", self.adapter)
        self.assertIn(
            "corrected_onehand_side_candidates_require_manual_review",
            self.adapter,
        )

    def test_v13_is_retained_as_rejected_boundary_experiment(self) -> None:
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
            "Rejected boundary-touch experiment: blender_sprite_factory_combat_idle_directional_weapon_v13.py",
            launcher,
        )
        self.assertIn(
            "render-combat-idle-directional-weapon-v13 (rejected: left frame touched canvas boundary)",
            workflow,
        )
        self.assertIn(
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_walk_directional_weapon_v15.py"',
            launcher,
        )
        self.assertIn("render-walk-directional-weapon-v15", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat idle directional weapon v13"):
            load_combat_idle_directional_weapon_profile_v13("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
