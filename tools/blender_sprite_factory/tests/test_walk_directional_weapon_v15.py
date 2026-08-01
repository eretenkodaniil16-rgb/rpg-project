from __future__ import annotations

import ast
import unittest
from pathlib import Path

from walk_directional_weapon_profile_v15 import (
    ARMED_WALK_FPS,
    ARMED_WALK_FRAME_ORDER,
    load_walk_directional_weapon_profile_v15,
)


class WalkDirectionalWeaponV15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_walk_directional_weapon_profile_v15(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "walk_directional_weapon_builder_v15.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_walk_directional_weapon_v15.py"
        ).read_text(encoding="utf-8")

    def test_profile_locks_two_grips_four_directions_and_six_frames(self) -> None:
        self.assertEqual(self.profile.revision, "v15")
        self.assertEqual(self.profile.animation_revision, "v01")
        self.assertEqual(self.profile.fps, ARMED_WALK_FPS)
        self.assertTrue(self.profile.loop)
        self.assertEqual(self.profile.frame_order, ARMED_WALK_FRAME_ORDER)
        self.assertEqual(
            tuple(item.direction for item in self.profile.directions),
            ("down", "left", "right", "up"),
        )
        self.assertEqual(
            tuple(item.grip_id for item in self.profile.grips),
            ("onehand_ready", "twohand_center_high"),
        )

    def test_profile_uses_only_artist_approved_sources(self) -> None:
        self.assertEqual(
            tuple(item.source_action_id for item in self.profile.directions),
            ("walk_down", "walk_left", "walk_right", "walk_up"),
        )
        self.assertEqual(
            tuple(item.source_animation_revision for item in self.profile.directions),
            ("v04", "v01", "v01", "v02"),
        )
        self.assertEqual(
            self.profile.static_weapon_source_revision,
            "directional_weapon_v12_artist_approved",
        )
        self.assertEqual(
            self.profile.combat_idle_source_revision,
            "directional_cycles_v14_artist_approved",
        )
        self.assertEqual(
            tuple(item.stance_variant_id for item in self.profile.grips),
            ("onehand_ready", "twohand_center_high"),
        )

    def test_twohand_passing_guard_is_lowered_after_boundary_failure(self) -> None:
        twohand = self.profile.grips[1]
        self.assertEqual(
            twohand.weapon_arm_step_offsets_degrees,
            (0.0, -0.8, -0.2, 0.0, -0.8, -0.2),
        )
        self.assertLessEqual(twohand.weapon_arm_step_offsets_degrees[2], 0.0)
        self.assertLessEqual(twohand.weapon_arm_step_offsets_degrees[5], 0.0)

    def test_builder_creates_eight_real_actions_without_new_geometry(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_combat_idle_directional_cycles_v14(context)",
            self.builder_source,
        )
        self.assertIn("factory._new_action", self.builder_source)
        self.assertIn("approved_lower_body_preserved", self.builder_source)
        self.assertIn("weapon_hand_stabilized", self.builder_source)
        self.assertIn("len(created_actions) != 8", self.builder_source)
        self.assertNotIn("factory._cylinder_between", self.builder_source)
        self.assertNotIn("factory._ellipsoid", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_onehand_and_twohand_upper_body_contracts_are_separate(self) -> None:
        self.assertIn("_onehand_channels", self.builder_source)
        self.assertIn("_twohand_channels", self.builder_source)
        self.assertIn("free_arm_swing_scale", self.builder_source)
        self.assertIn("WEAPON_FOREARM_COUNTER_SCALE", self.builder_source)
        self.assertIn('pose.bones["hand.L"].rotation_euler', self.builder_source)
        self.assertIn('pose.bones["hand.R"].rotation_euler', self.builder_source)

    def test_adapter_renders_and_validates_all_48_frames(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("rendered_count != 48", self.adapter_source)
        self.assertIn("changed approved lower body", self.adapter_source)
        self.assertIn("MAX_WIDTH_DRIFT = 8", self.adapter_source)
        self.assertIn("MAX_HEIGHT_DRIFT = 6", self.adapter_source)
        self.assertIn("walk_directional_weapon_v15.png", self.adapter_source)
        self.assertIn(
            "armed_directional_walk_cycles_require_manual_animation_review",
            self.adapter_source,
        )
        self.assertIn("weapon_adapter._set_v12_weapon", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_adapter_renders_only_v15_frames_after_direction_calibration(self) -> None:
        self.assertIn("raw_dir.mkdir()", self.adapter_source)
        self.assertIn("frame_dir.mkdir()", self.adapter_source)
        self.assertIn(
            "directional_adapter._direction_calibrations(context, run_dir)",
            self.adapter_source,
        )
        self.assertIn(
            '"historical_frames_replayed": False',
            self.adapter_source,
        )
        self.assertIn(
            '"render_scope": "v15_frames_only_with_four_direction_calibration"',
            self.adapter_source,
        )
        self.assertNotIn(
            "previous_adapter.render_combat_idle_directional_cycles_v14",
            self.adapter_source,
        )

    def test_active_launcher_and_workflow_use_v15(self) -> None:
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
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_walk_directional_weapon_v15.py"',
            launcher,
        )
        self.assertIn("render-walk-directional-weapon-v15", workflow)
        self.assertIn(
            "blender_sprite_factory_walk_directional_weapon_v15.py",
            workflow,
        )
        self.assertIn("Upload 48 armed directional walk frames v15", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No armed directional walk v15"):
            load_walk_directional_weapon_profile_v15("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
