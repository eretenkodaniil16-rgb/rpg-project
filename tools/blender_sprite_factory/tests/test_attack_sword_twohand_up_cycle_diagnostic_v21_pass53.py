from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordTwohandUpCycleDiagnosticV21Pass53Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass53.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass53.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass53_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.adapter_source)

    def test_pass53_locks_boundary_safe_f08_settle_candidate(self) -> None:
        self.assertIn('TARGET_FRAME = 8', self.correction_source)
        self.assertIn('F08_SOURCE_POSE_LABEL = "selected_f07_arm_pose"', self.correction_source)
        self.assertIn('F08_ARM_BLEND = 1.00', self.correction_source)
        self.assertIn('F08_DEPTH_BRANCH = "source"', self.correction_source)
        self.assertIn('F08_WEAPON_OFFSET_DEGREES = 48.0', self.correction_source)
        self.assertIn('F08_REQUESTED_SCREEN_PROJECTION = 0.90', self.correction_source)
        self.assertIn('SOURCE_REVIEW_VARIANT = 5', self.correction_source)
        self.assertIn('F08_EDGE_COUNTS', self.correction_source)

    def test_pass53_reconstructs_selected_f07_and_preserves_assets(self) -> None:
        self.assertIn('selected_f07_rotations = pass34_adapter._candidate_pose', self.adapter_source)
        self.assertIn('pass52_adapter._render_candidate', self.adapter_source)
        self.assertIn('REQUIRE_ZERO_EDGE_ALPHA', self.adapter_source)
        self.assertIn('twohand_up_action_data_changed', self.adapter_source)
        self.assertIn('root_translation_used', self.adapter_source)
        self.assertIn('weapon_geometry_changed', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)
        self.assertNotIn('scale = -', self.adapter_source)

    def test_pass53_records_complete_strict_cycle(self) -> None:
        self.assertIn('all_eight_frames_selected', self.adapter_source)
        self.assertIn('all_eight_frames_zero_edge_alpha', self.adapter_source)
        self.assertIn('frame_metrics["f08"]', self.adapter_source)
        self.assertIn('SELECTED_F08_SCENE_KEY', self.adapter_source)
        self.assertIn('_restore_pass51_contract', self.adapter_source)

    def test_workflow_uses_pass53_and_retains_pass52(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass53.py',
            self.workflow_source,
        )
        self.assertIn('strict selected full cycle', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_f08_review_v21_pass52.py',
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
