from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_directional_profile_v11 import DIRECTION_ORDER
from death_directional_cycles_profile_v01 import (
    PROFILE_REVISION,
    REVIEW_DIRECTION_ORDER,
    load_death_directional_cycles_profile_v01,
)
from death_down_cycle_profile_v01 import load_death_down_cycle_profiles_v01
from death_down_keyposes_profile_v01 import DEATH_DOWN_VARIANT_IDS


ROOT = Path(__file__).resolve().parents[3]
TOOL_ROOT = ROOT / "tools" / "blender_sprite_factory"
PROFILE_PATH = TOOL_ROOT / "death_directional_cycles_profile_v01.py"
BUILDER_PATH = TOOL_ROOT / "death_directional_cycles_builder_v01.py"
ADAPTER_PATH = TOOL_ROOT / "blender_sprite_factory_death_directional_v01.py"
DOC_PATH = ROOT / "docs" / "HUMAN_WARRIOR_DEATH_DIRECTIONAL_CYCLES_V01.md"
WORKFLOW_PATH = (
    ROOT
    / ".github"
    / "workflows"
    / "validate-human-warrior-death-directional-cycles-v01.yml"
)


class DeathDirectionalCyclesV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_death_directional_cycles_profile_v01(
            "human_warrior_m01"
        )
        cls.sources = load_death_down_cycle_profiles_v01("human_warrior_m01")
        cls.builder_source = BUILDER_PATH.read_text(encoding="utf-8")
        cls.adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")

    def test_profile_locks_three_variants_and_four_directions(self) -> None:
        self.assertEqual(self.profile.revision, PROFILE_REVISION)
        self.assertEqual(self.profile.directions, DIRECTION_ORDER)
        self.assertEqual(self.profile.directions, ("down", "left", "right", "up"))
        self.assertEqual(self.profile.review_directions, REVIEW_DIRECTION_ORDER)
        self.assertEqual(self.profile.review_directions, ("left", "right", "up"))
        self.assertEqual(self.profile.frame_order, (1, 2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(
            self.profile.phase_order,
            (
                "guard",
                "stagger",
                "balance_break",
                "knee_drop",
                "fall_acceleration",
                "ground_impact",
                "final",
                "corpse_hold",
            ),
        )
        self.assertEqual(self.profile.fps, 10)
        self.assertAlmostEqual(self.profile.duration_seconds, 0.8)
        self.assertFalse(self.profile.loop)
        self.assertFalse(self.profile.weapon_visible)
        self.assertTrue(self.profile.final_pose_persistent)
        self.assertEqual(
            tuple(item.death_variant_id for item in self.profile.variants),
            DEATH_DOWN_VARIANT_IDS,
        )

    def test_directional_variants_reuse_approved_down_profiles(self) -> None:
        source_by_variant = {
            source.death_variant_id: source for source in self.sources
        }
        for variant in self.profile.variants:
            source = source_by_variant[variant.death_variant_id]
            self.assertEqual(variant.animation_id, source.animation_id)
            self.assertEqual(
                variant.source_profile_revision,
                source.revision,
            )
            self.assertEqual(variant.gore_mode, source.gore_mode)
            self.assertEqual(variant.detached_part_id, source.detached_part_id)
            self.assertEqual(variant.detachment_frame, source.detachment_frame)

    def test_profile_rejects_unknown_character(self) -> None:
        with self.assertRaises(KeyError):
            load_death_directional_cycles_profile_v01("unknown_character")

    def test_builder_reuses_actions_and_marks_directional_review(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn(
            "create_death_down_cycle_actions_v01(context)",
            self.builder_source,
        )
        self.assertIn(
            'action["animation_revision"] = "directional_full_cycle_v01"',
            self.builder_source,
        )
        self.assertIn(
            'action["directional_variants_not_started"] = False',
            self.builder_source,
        )
        self.assertIn(
            'action["manual_directional_review_required"] = True',
            self.builder_source,
        )
        self.assertIn(
            'action["directional_render_contract_ready"] = True',
            self.builder_source,
        )
        self.assertIn(
            'action["directional_render_complete"] = False',
            self.builder_source,
        )
        self.assertIn(
            'scene["death_directional_real_rig_rotation"] = True',
            self.builder_source,
        )
        self.assertIn(
            'scene["death_directional_runtime_connected"] = False',
            self.builder_source,
        )

    def test_adapter_reuses_down_then_renders_three_new_directions(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "artifacts = down_adapter.render_death_down_cycles_v01(context, run_dir)",
            self.adapter_source,
        )
        self.assertIn(
            "for direction in directional.review_directions:",
            self.adapter_source,
        )
        self.assertIn(
            "context.rig.rotation_euler[2] = math.radians(",
            self.adapter_source,
        )
        self.assertIn(
            '"left_right_up_rendered_independently": True',
            self.adapter_source,
        )
        self.assertIn(
            '"approved_down_rgba_unchanged_during_directional_render": True',
            self.adapter_source,
        )
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_death_03_split_offset_rotates_with_the_rig(self) -> None:
        self.assertIn("_rotated_upper_body_offset", self.adapter_source)
        self.assertIn(
            "context.config.directions[direction]",
            self.adapter_source,
        )
        self.assertIn("cosine * local_x - sine * local_y", self.adapter_source)
        self.assertIn("sine * local_x + cosine * local_y", self.adapter_source)
        self.assertIn("_GORE_UPPER_BODY_BONES", self.adapter_source)
        self.assertIn("_assert_split_components", self.adapter_source)
        self.assertIn(
            "_projection_aware_upper_body_offset",
            self.adapter_source,
        )
        self.assertIn(
            '"left": 2.90',
            self.adapter_source,
        )
        self.assertIn(
            '"right": 2.60',
            self.adapter_source,
        )
        self.assertIn(
            '"up": 0.80',
            self.adapter_source,
        )
        self.assertIn(
            '"left": 5.00',
            self.adapter_source,
        )
        self.assertIn(
            '"right": 5.00',
            self.adapter_source,
        )
        self.assertIn(
            '"up": 4.50',
            self.adapter_source,
        )
        self.assertIn(
            "SPLIT_SCREEN_UP_REFERENCE_FRAME = 6",
            self.adapter_source,
        )
        self.assertIn("ground_screen_up", self.adapter_source)
        self.assertIn("_apply_up_split_tumble", self.adapter_source)
        self.assertIn('"degrees": 40.0', self.adapter_source)
        self.assertIn('"degrees": 32.0', self.adapter_source)
        self.assertIn("Matrix.Rotation", self.adapter_source)
        self.assertIn(
            '"death_03_two_major_components_per_direction": True',
            self.adapter_source,
        )

    def test_renderer_requires_72_new_and_96_total_frames(self) -> None:
        self.assertEqual(
            len(self.profile.variants)
            * len(self.profile.review_directions)
            * len(self.profile.frame_order),
            72,
        )
        self.assertEqual(
            len(self.profile.variants)
            * len(self.profile.directions)
            * len(self.profile.frame_order),
            96,
        )
        self.assertIn("expected_count = (", self.adapter_source)
        self.assertIn("_assert_binary_rgba_canvas", self.adapter_source)
        self.assertIn("_assert_no_boundary_touch", self.adapter_source)
        self.assertIn("_assert_direction_contract", self.adapter_source)
        self.assertIn("_normalize_direction_artifacts", self.adapter_source)
        self.assertIn(
            '"runtime_anchor_compensation_x_pixels"',
            self.adapter_source,
        )
        self.assertIn(
            '"shared_cycle_motion_envelope"',
            self.adapter_source,
        )
        self.assertIn(
            '"corpse_hold_matches_final_per_direction": True',
            self.adapter_source,
        )
        self.assertIn('"runtime_connected": False', self.adapter_source)

    def test_contact_sheet_is_variant_then_direction(self) -> None:
        self.assertIn(
            "for profile in _profiles(character_id)\n"
            "        for direction in directional.directions",
            self.adapter_source,
        )
        self.assertIn(
            "row_y = (len(rows) - 1 - row_index) * tile_height",
            self.adapter_source,
        )
        self.assertIn(
            'CONTACT_SHEET_NAME = "human_warrior_m01_death_directional_cycles_v01.png"',
            self.adapter_source,
        )

    def test_stage_files_exist(self) -> None:
        for path in (
            PROFILE_PATH,
            BUILDER_PATH,
            ADAPTER_PATH,
            DOC_PATH,
            WORKFLOW_PATH,
        ):
            self.assertTrue(path.is_file(), path)


if __name__ == "__main__":
    unittest.main()
