from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_profile_v21 import (
    DIRECTIONAL_CYCLE_REVISION,
    DIRECTION_ORDER,
    GRIP_ORDER,
    TOTAL_ACTION_COUNT,
    TOTAL_RENDERED_FRAME_COUNT,
    load_attack_sword_directional_cycle_profile_v21,
)


class AttackSwordDirectionalCycleV21Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile_source = (
            cls.tool_root / "attack_sword_directional_cycle_profile_v21.py"
        ).read_text(encoding="utf-8")
        cls.builder_source = (
            cls.tool_root / "attack_sword_directional_cycle_builder_v21.py"
        ).read_text(encoding="utf-8")
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_directional_cycle_v21.py"
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")
        cls.launcher_source = (
            cls.tool_root / "run_blender_sprite_pilot.ps1"
        ).read_text(encoding="utf-8")

    def test_profile_defines_two_grips_in_four_directions(self) -> None:
        profile = load_attack_sword_directional_cycle_profile_v21(
            "human_warrior_m01"
        )
        self.assertEqual(profile.revision, DIRECTIONAL_CYCLE_REVISION)
        self.assertEqual(profile.directions, DIRECTION_ORDER)
        self.assertEqual(len(profile.actions), TOTAL_ACTION_COUNT)
        self.assertEqual(TOTAL_RENDERED_FRAME_COUNT, 64)
        self.assertEqual(
            {(action.direction, action.grip_id) for action in profile.actions},
            {(direction, grip_id) for direction in DIRECTION_ORDER for grip_id in GRIP_ORDER},
        )

    def test_down_actions_remain_v20_sources(self) -> None:
        profile = load_attack_sword_directional_cycle_profile_v21(
            "human_warrior_m01"
        )
        down_actions = [action for action in profile.actions if action.direction == "down"]
        self.assertEqual(
            [action.action_id for action in down_actions],
            ["attack_sword_01_onehand_down_v20", "attack_sword_01_twohand_down_v20"],
        )
        for action in profile.actions:
            if action.direction != "down":
                self.assertTrue(action.action_id.endswith("_v21"))

    def test_sources_parse_without_blender(self) -> None:
        ast.parse(self.profile_source)
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_copies_actions_without_mirroring(self) -> None:
        self.assertIn("source_action.copy()", self.builder_source)
        self.assertIn('action["mirroring_used"] = False', self.builder_source)
        self.assertIn(
            'scene["attack_sword_directional_cycle_real_rig_rotation_used"] = True',
            self.builder_source,
        )
        self.assertNotIn("obj.scale", self.builder_source)
        self.assertNotIn("rig.scale", self.builder_source)

    def test_adapter_renders_64_frames_with_directional_modules(self) -> None:
        self.assertIn("TOTAL_RENDERED_FRAME_COUNT", self.adapter_source)
        self.assertIn("directional_adapter._direction_calibrations", self.adapter_source)
        self.assertIn("weapon_adapter._set_v12_weapon", self.adapter_source)
        self.assertIn("ONE_HAND_V12_OBJECTS_BY_DIRECTION", self.adapter_source)
        self.assertIn("TWO_HAND_HIGH_V06_OBJECT_NAMES", self.adapter_source)
        self.assertIn("down_pass05._render_frame_v20_pass05", self.adapter_source)
        self.assertIn('"mirroring_used": False', self.adapter_source)
        self.assertIn('"physical_equipment_sides_preserved": True', self.adapter_source)

    def test_adapter_requires_export_and_head_safety(self) -> None:
        self.assertIn("keypose_adapter._edge_alpha_counts", self.adapter_source)
        self.assertIn("export_adapter._weapon_head_clearance", self.adapter_source)
        self.assertIn("MIN_HEAD_CLEARANCE_BY_GRIP", self.adapter_source)
        self.assertIn("baseline_y", self.adapter_source)
        self.assertIn("96x96", self.adapter_source)

    def test_active_entrypoints_use_full_pass09(self) -> None:
        target = (
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass09.py"
        )
        self.assertIn(target, self.workflow_source)
        self.assertIn("attack_directional_cycle_v21", self.launcher_source)
        self.assertIn(target, self.launcher_source)


if __name__ == "__main__":
    unittest.main()
