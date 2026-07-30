from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_directional_weapon_profile_v12 import (
    load_combat_idle_directional_weapon_profile_v12,
)


class CombatIdleDirectionalWeaponV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_directional_weapon_profile_v12(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_directional_weapon_builder_v12.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_directional_weapon_v12.py"
        ).read_text(encoding="utf-8")

    def test_only_left_right_up_onehand_projections_are_corrected(self) -> None:
        self.assertEqual(self.profile.revision, "v12")
        self.assertEqual(
            tuple(item.direction for item in self.profile.corrected_onehand_directions),
            ("left", "right", "up"),
        )
        self.assertEqual(
            self.profile.preserved_down_source,
            "combat_idle_onehand_ready_directional_v11_down",
        )
        self.assertEqual(
            self.profile.preserved_twohand_source,
            "combat_idle_twohand_center_high_directional_v11",
        )
        for item in self.profile.corrected_onehand_directions:
            self.assertGreaterEqual(abs(item.side_x), 0.40)
            self.assertLess(item.vertical_z, -0.45)
            self.assertGreaterEqual(item.minimum_sprite_width, 40)

    def test_builder_reuses_v10_actions_and_builds_weapon_only(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("create_combat_idle_cycles_v10(context)", self.builder_source)
        self.assertIn("ONE_HAND_LEFT_V12_OBJECT_NAMES", self.builder_source)
        self.assertIn("ONE_HAND_RIGHT_V12_OBJECT_NAMES", self.builder_source)
        self.assertIn("ONE_HAND_UP_V12_OBJECT_NAMES", self.builder_source)
        self.assertIn("pose_fitted_directional_module", self.builder_source)
        self.assertNotIn("factory._new_action", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_preserves_down_and_all_twohand_pixels(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("must_match_previous", self.adapter_source)
        self.assertIn("candidate_id == \"twohand_center_high\" or direction == \"down\"", self.adapter_source)
        self.assertIn("changed locked pixels", self.adapter_source)
        self.assertIn("twohand_all_direction_pixels_unchanged", self.adapter_source)

    def test_corrected_onehand_frames_must_clear_boundaries_and_width_budget(self) -> None:
        self.assertIn("_assert_no_boundary_touch", self.adapter_source)
        self.assertIn("is below readability budget", self.adapter_source)
        self.assertIn("onehand_corrected_frames_clear_canvas_boundaries", self.adapter_source)
        self.assertIn("corrected_directional_static_candidates_require_manual_review", self.adapter_source)

    def test_active_launcher_and_workflow_use_v12(self) -> None:
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
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_combat_idle_directional_weapon_v12.py"',
            launcher,
        )
        self.assertIn("render-combat-idle-directional-weapon-v12", workflow)
        self.assertIn(
            "blender_sprite_factory_combat_idle_directional_weapon_v12.py",
            workflow,
        )

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat idle directional weapon v12"):
            load_combat_idle_directional_weapon_profile_v12("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
