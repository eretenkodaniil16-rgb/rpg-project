from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_directional_profile_v11 import (
    DIRECTION_ORDER,
    REVIEW_DIRECTION_ORDER,
    load_combat_idle_directional_profile_v11,
)


class CombatIdleDirectionalV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_combat_idle_directional_profile_v11("human_warrior_m01")
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_combat_idle_directional_v11.py"
        ).read_text(encoding="utf-8")

    def test_selected_sources_and_direction_order_are_locked(self) -> None:
        self.assertEqual(self.profile.revision, "v11")
        self.assertEqual(self.profile.approved_direction, "down")
        self.assertEqual(self.profile.review_directions, REVIEW_DIRECTION_ORDER)
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in self.profile.candidates),
            ("onehand_ready", "twohand_center_high"),
        )
        self.assertEqual(
            tuple(candidate.source_animation_id for candidate in self.profile.candidates),
            (
                "combat_idle_onehand_ready_cycle_v10",
                "combat_idle_twohand_center_high_cycle_v10",
            ),
        )
        for candidate in self.profile.candidates:
            self.assertEqual(candidate.directions, DIRECTION_ORDER)

    def test_adapter_uses_real_rig_rotations_and_only_frame_one(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("config.directions[direction]", self.adapter_source)
        self.assertIn("factory.bpy.context.scene.frame_set(1)", self.adapter_source)
        self.assertIn("source_animation_id", self.adapter_source)
        self.assertIn("combat_idle_directional_v11.png", self.adapter_source)
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_approved_down_pixels_are_enforced(self) -> None:
        self.assertIn(
            'rendered["down"].output_path.read_bytes() != approved.output_path.read_bytes()',
            self.adapter_source,
        )
        self.assertIn("down_pixels_identical_to_approved_v10", self.adapter_source)
        self.assertIn("directional_static_candidates_require_manual_review", self.adapter_source)

    def test_stage_does_not_rebuild_actions_or_weapon_geometry(self) -> None:
        self.assertIn("create_combat_idle_cycles_v10", self.adapter_source)
        self.assertIn("previous_adapter._set_cycle_weapon(cycle)", self.adapter_source)
        self.assertNotIn("factory._new_action", self.adapter_source)
        self.assertNotIn("factory._cylinder_between", self.adapter_source)
        self.assertNotIn("factory._ellipsoid", self.adapter_source)

    def test_v11_is_historical_rejected_source_for_active_v12(self) -> None:
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
            "Rejected raw directional rotation: blender_sprite_factory_combat_idle_directional_v11.py",
            launcher,
        )
        self.assertIn(
            "render-combat-idle-directional-v11 (rejected: raw rotation caused one-hand occlusion and boundary touches)",
            workflow,
        )
        self.assertIn(
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_combat_idle_directional_weapon_v12.py"',
            launcher,
        )
        self.assertIn("render-combat-idle-directional-weapon-v12", workflow)

    def test_unknown_character_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "No combat idle directional v11"):
            load_combat_idle_directional_profile_v11("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
