from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_down_cycles_profile_v10 import (
    COMBAT_IDLE_CYCLE_FPS,
    FRAME_ORDER,
    PHASE_ORDER,
    load_combat_idle_cycles_profile_v10,
)
from combat_idle_down_weapon_variants_profile_v09 import load_weapon_stance_profile_v09


class CombatIdleDownCyclesV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_cycles_profile_v10("human_warrior_m01")
        cls.stances = load_weapon_stance_profile_v09("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_down_cycles_builder_v10.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_combat_idle_down_cycles_v10.py"
        ).read_text(encoding="utf-8")

    def test_selected_best_stances_are_ready_v09_and_high_v06(self) -> None:
        self.assertEqual(self.profile.revision, "v10")
        self.assertEqual(
            tuple(cycle.cycle_id for cycle in self.profile.cycles),
            ("onehand_ready", "twohand_center_high"),
        )
        self.assertEqual(
            tuple(cycle.source_animation_id for cycle in self.profile.cycles),
            (
                "combat_idle_onehand_ready_v09",
                "combat_idle_twohand_center_high_v06",
            ),
        )
        self.assertEqual(
            tuple(cycle.source_revision for cycle in self.profile.cycles),
            ("v09", "v06"),
        )

    def test_each_cycle_is_four_frame_loop_with_restrained_breathing(self) -> None:
        for cycle in self.profile.cycles:
            self.assertEqual(cycle.fps, COMBAT_IDLE_CYCLE_FPS)
            self.assertTrue(cycle.loop)
            self.assertEqual(
                tuple(frame.pose.frame for frame in cycle.frames),
                FRAME_ORDER,
            )
            self.assertEqual(
                tuple(frame.pose.phase for frame in cycle.frames),
                PHASE_ORDER,
            )
            self.assertLessEqual(
                max(abs(frame.chest_lift_z) for frame in cycle.frames),
                0.04,
            )

    def test_frame_one_preserves_the_approved_pose(self) -> None:
        for cycle, source in zip(
            self.profile.cycles,
            (self.stances.variants[1], self.stances.variants[3]),
        ):
            self.assertEqual(
                cycle.frames[0].pose.numeric_channels(),
                source.pose.numeric_channels(),
            )
            self.assertEqual(
                cycle.frames[0].hand_left_x_degrees,
                source.hand_left_x_degrees,
            )
            self.assertEqual(
                cycle.frames[0].hand_left_z_degrees,
                source.hand_left_z_degrees,
            )

    def test_lower_body_is_planted_in_both_cycles(self) -> None:
        attributes = (
            "pelvis_x",
            "pelvis_z",
            "pelvis_roll_z_degrees",
            "thigh_left_x_degrees",
            "thigh_right_x_degrees",
            "thigh_left_z_degrees",
            "thigh_right_z_degrees",
            "shin_left_x_degrees",
            "shin_right_x_degrees",
            "foot_left_x_degrees",
            "foot_right_x_degrees",
        )
        for cycle in self.profile.cycles:
            base = cycle.frames[0].pose
            for frame in cycle.frames[1:]:
                for attribute in attributes:
                    self.assertEqual(
                        getattr(frame.pose, attribute),
                        getattr(base, attribute),
                    )

    def test_one_hand_sword_arm_remains_rotation_stable(self) -> None:
        cycle = self.profile.cycles[0]
        base = cycle.frames[0].pose
        for frame in cycle.frames:
            for attribute in (
                "upper_arm_right_x_degrees",
                "upper_arm_right_z_degrees",
                "forearm_right_x_degrees",
                "forearm_right_z_degrees",
                "hand_right_x_degrees",
                "hand_right_z_degrees",
            ):
                self.assertEqual(
                    getattr(frame.pose, attribute),
                    getattr(base, attribute),
                )

    def test_two_hand_motion_remains_centered_and_symmetric(self) -> None:
        for frame in self.profile.cycles[1].frames:
            pose = frame.pose
            self.assertEqual(
                pose.upper_arm_left_x_degrees,
                pose.upper_arm_right_x_degrees,
            )
            self.assertEqual(
                pose.forearm_left_x_degrees,
                pose.forearm_right_x_degrees,
            )
            self.assertEqual(
                pose.upper_arm_left_z_degrees,
                pose.upper_arm_right_z_degrees,
            )
            self.assertEqual(
                pose.forearm_left_z_degrees,
                -pose.forearm_right_z_degrees,
            )

    def test_builder_extends_v09_without_rebuilding_weapon_geometry(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "previous_builder.create_weapon_stance_actions_v09(context)",
            self.builder_source,
        )
        self.assertIn('pose.bones["chest"].location', self.builder_source)
        self.assertIn("selected_best_candidate", self.builder_source)
        self.assertNotIn("factory._cylinder_between", self.builder_source)
        self.assertNotIn("factory._ellipsoid", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)

    def test_adapter_renders_both_four_frame_cycles(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "previous_adapter.render_weapon_stance_variants_v09",
            self.adapter_source,
        )
        self.assertIn(
            "previous_adapter._set_weapon_variant_v09",
            self.adapter_source,
        )
        self.assertIn("combat_idle_down_cycles_v10.png", self.adapter_source)
        self.assertIn(
            "technical_cycles_require_manual_animation_review",
            self.adapter_source,
        )
        self.assertNotIn("scale.x = -1", self.adapter_source)

    def test_v10_remains_approved_down_source_under_active_v15(self) -> None:
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
            "Artist-approved down cycles: blender_sprite_factory_combat_idle_down_cycles_v10.py",
            launcher,
        )
        self.assertIn("render-combat-idle-down-cycles-v10", workflow)
        self.assertIn(
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_walk_directional_weapon_v15.py"',
            launcher,
        )
        self.assertIn("render-walk-directional-weapon-v15", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat idle cycles v10"):
            load_combat_idle_cycles_profile_v10("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
