from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordTwohandUpF07ReviewV21Pass50Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass50.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_f07_review_v21_pass50.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass50_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.adapter_source)

    def test_pass50_targets_f07_and_preserves_neighbor_continuity(self) -> None:
        self.assertIn('TARGET_FRAME = 7', self.correction_source)
        self.assertIn('PREVIOUS_REFERENCE_FRAME = 6', self.correction_source)
        self.assertIn('NEXT_REFERENCE_FRAME = 8', self.correction_source)
        self.assertIn('continuity_from_f06_rms_degrees', self.adapter_source)
        self.assertIn('continuity_to_f08_rms_degrees', self.adapter_source)
        self.assertIn('_arm_rms_degrees', self.adapter_source)

    def test_pass50_is_diagnostic_only_and_keeps_final_boundary_contract(self) -> None:
        self.assertIn('diagnostic_only', self.adapter_source)
        self.assertIn('manual_selection_required', self.adapter_source)
        self.assertIn('accepted_by_final_boundary_contract', self.adapter_source)
        self.assertIn('REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE', self.adapter_source)
        self.assertIn('twohand_up_action_data_changed', self.adapter_source)
        self.assertIn('root_translation_used', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)
        self.assertNotIn('scale = -', self.adapter_source)

    def test_pass50_reviews_diverse_arm_projection_candidates(self) -> None:
        self.assertIn('SOURCE_FRAME_CANDIDATES = (8, 6, 5, 4)', self.correction_source)
        self.assertIn('ARM_BLEND_CANDIDATES', self.correction_source)
        self.assertIn('SCREEN_PROJECTION_CANDIDATES', self.correction_source)
        self.assertIn('DEPTH_BRANCH_CANDIDATES', self.correction_source)
        self.assertIn('_select_review_candidates', self.adapter_source)
        self.assertIn('REVIEW_VARIANT_COUNT = 6', self.correction_source)

    def test_workflow_uses_pass50_and_retains_pass49(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_f07_review_v21_pass50.py',
            self.workflow_source,
        )
        self.assertIn('f07 continuity review', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass49.py',
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
