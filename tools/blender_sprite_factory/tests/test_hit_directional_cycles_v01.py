from __future__ import annotations

import ast
import unittest
from pathlib import Path

from combat_idle_directional_profile_v11 import DIRECTION_ORDER
from hit_directional_cycles_profile_v01 import (
    REVIEW_DIRECTION_ORDER,
    load_hit_directional_cycles_profile_v01,
)
from hit_down_cycle_profile_v01 import load_hit_down_cycle_profile_v01
from hit_down_twohand_cycle_profile_v01 import (
    load_hit_down_twohand_cycle_profile_v01,
)


class HitDirectionalCyclesV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.profile = load_hit_directional_cycles_profile_v01(
            "human_warrior_m01"
        )
        cls.onehand = load_hit_down_cycle_profile_v01("human_warrior_m01")
        cls.twohand = load_hit_down_twohand_cycle_profile_v01(
            "human_warrior_m01"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_hit_directional_v01.py"
        ).read_text(encoding="utf-8")

    def test_profile_identity_and_scope(self) -> None:
        self.assertEqual(
            self.profile.revision,
            "hit_directional_cycles_v01_from_approved_down",
        )
        self.assertEqual(self.profile.directions, DIRECTION_ORDER)
        self.assertEqual(self.profile.review_directions, REVIEW_DIRECTION_ORDER)
        self.assertEqual(self.profile.review_directions, ("left", "right", "up"))
        self.assertEqual(self.profile.frame_order, (1, 2, 3, 4, 5, 6))
        self.assertEqual(
            self.profile.phase_order,
            (
                "impact",
                "recoil_peak",
                "release_mid",
                "recovery",
                "settle",
                "guard",
            ),
        )
        self.assertEqual(self.profile.fps, 15)
        self.assertAlmostEqual(self.profile.duration_seconds, 0.4)
        self.assertFalse(self.profile.loop)
        self.assertEqual(
            self.profile.directional_stance_source_revision,
            "combat_idle_directional_cycles_v14",
        )
        self.assertEqual(
            self.profile.directional_weapon_source_revision,
            "combat_idle_directional_weapon_v12",
        )

    def test_cycle_sources_are_the_approved_down_profiles(self) -> None:
        cycles = {cycle.cycle_id: cycle for cycle in self.profile.cycles}
        self.assertEqual(tuple(cycles), ("onehand_ready", "twohand_center_high"))
        onehand = cycles["onehand_ready"]
        twohand = cycles["twohand_center_high"]
        self.assertEqual(onehand.animation_id, self.onehand.animation_id)
        self.assertEqual(onehand.source_profile_revision, self.onehand.revision)
        self.assertEqual(onehand.weapon_cycle_id, "onehand_ready")
        self.assertEqual(twohand.animation_id, self.twohand.animation_id)
        self.assertEqual(twohand.source_profile_revision, self.twohand.revision)
        self.assertEqual(twohand.weapon_cycle_id, "twohand_center_high")

    def test_adapter_reuses_down_renderer_and_local_actions(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "artifacts = down_adapter.render_hit_down_cycle_v01(context, run_dir)",
            self.adapter_source,
        )
        self.assertIn(
            "create_hit_down_cycle_actions_v01",
            self.adapter_source,
        )
        self.assertIn(
            "for direction in directional.review_directions:",
            self.adapter_source,
        )
        self.assertIn(
            "weapon_adapter._set_v12_weapon(profile.weapon_cycle_id, direction)",
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
            '"approved_down_renderer_reused": True',
            self.adapter_source,
        )
        self.assertNotIn("scale.x = -1", self.adapter_source)
        self.assertNotIn("scale[0] = -1", self.adapter_source)

    def test_adapter_requires_48_frames_and_clean_boundaries(self) -> None:
        self.assertIn(
            "len(directional.cycles)\n        * len(directional.directions)",
            self.adapter_source,
        )
        self.assertIn("_assert_no_boundary_touch", self.adapter_source)
        self.assertIn("baseline_y", self.adapter_source)
        self.assertIn('"baseline_y_91_required": True', self.adapter_source)
        self.assertIn('"mirroring_used": False', self.adapter_source)
        self.assertIn('"negative_scale_used": False', self.adapter_source)
        self.assertIn('"runtime_connected": False', self.adapter_source)

    def test_contact_sheet_order_is_grip_then_direction(self) -> None:
        self.assertIn(
            "for cycle in directional.cycles\n        for direction in directional.directions",
            self.adapter_source,
        )
        self.assertIn(
            "row_y = (len(rows) - 1 - row_index) * tile_height",
            self.adapter_source,
        )
        self.assertIn(
            'CONTACT_SHEET_NAME = "human_warrior_m01_hit_01_directional_grips_v01.png"',
            self.adapter_source,
        )


if __name__ == "__main__":
    unittest.main()
