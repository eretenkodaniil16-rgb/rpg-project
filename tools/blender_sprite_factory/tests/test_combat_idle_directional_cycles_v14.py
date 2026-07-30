from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_directional_cycles_profile_v14 import (
    load_combat_idle_directional_cycles_profile_v14,
)


class CombatIdleDirectionalCyclesV14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_directional_cycles_profile_v14(
            "human_warrior_m01"
        )
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (
            cls.tool_root / "combat_idle_directional_cycles_builder_v14.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_combat_idle_directional_cycles_v14.py"
        ).read_text(encoding="utf-8")

    def test_profile_uses_artist_approved_v12_static_directions(self) -> None:
        self.assertEqual(self.profile.revision, "v14")
        self.assertEqual(self.profile.static_source_revision, "v12_artist_approved")
        self.assertEqual(
            self.profile.rejected_experiment_revision,
            "v13_boundary_failure",
        )
        self.assertEqual(
            self.profile.directions,
            ("down", "left", "right", "up"),
        )
        self.assertEqual(self.profile.frame_order, (1, 2, 3, 4))
        self.assertEqual(
            self.profile.phase_order,
            ("base", "inhale", "settle", "exhale"),
        )

    def test_both_grips_reuse_v10_actions_at_four_fps(self) -> None:
        self.assertEqual(
            tuple(cycle.cycle_id for cycle in self.profile.cycles),
            ("onehand_ready", "twohand_center_high"),
        )
        self.assertEqual(
            tuple(cycle.source_action_id for cycle in self.profile.cycles),
            (
                "combat_idle_onehand_ready_cycle_v10",
                "combat_idle_twohand_center_high_cycle_v10",
            ),
        )
        for cycle in self.profile.cycles:
            self.assertEqual(cycle.fps, 4)
            self.assertTrue(cycle.loop)

    def test_builder_reuses_actions_and_v12_weapon_modules(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_combat_idle_directional_weapon_v12(context)",
            self.builder_source,
        )
        self.assertIn("directional_action_reused_without_duplication", self.builder_source)
        self.assertIn("artist_approved_directional_sources", self.builder_source)
        self.assertNotIn("factory._new_action", self.builder_source)
        self.assertNotIn("factory._cylinder_between", self.builder_source)
        self.assertNotIn("factory._ellipsoid", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_renders_32_frames_and_locks_sources(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("rendered_count != 32", self.adapter_source)
        self.assertIn("changed approved v12 frame 01", self.adapter_source)
        self.assertIn("changed approved v10 down pixels", self.adapter_source)
        self.assertIn("_assert_no_boundary_touch", self.adapter_source)
        self.assertIn("MAX_WIDTH_DRIFT = 4", self.adapter_source)
        self.assertIn("MAX_HEIGHT_DRIFT = 4", self.adapter_source)
        self.assertIn("combat_idle_directional_cycles_v14.png", self.adapter_source)
        self.assertIn("directional_cycles_require_manual_animation_review", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_active_launcher_and_workflow_use_v14(self) -> None:
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
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_combat_idle_directional_cycles_v14.py"',
            launcher,
        )
        self.assertIn("render-combat-idle-directional-cycles-v14", workflow)
        self.assertIn(
            "blender_sprite_factory_combat_idle_directional_cycles_v14.py",
            workflow,
        )

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat idle directional cycles v14"):
            load_combat_idle_directional_cycles_profile_v14("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
