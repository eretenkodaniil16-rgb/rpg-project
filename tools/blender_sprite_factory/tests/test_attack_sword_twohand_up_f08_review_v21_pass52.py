from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordTwohandUpF08ReviewV21Pass52Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass52.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_f08_review_v21_pass52.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass52_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.adapter_source)

    def test_pass52_targets_settle_and_guard_reference(self) -> None:
        self.assertIn('TARGET_FRAME = 8', self.correction_source)
        self.assertIn('PREVIOUS_REFERENCE_FRAME = 7', self.correction_source)
        self.assertIn('GUARD_REFERENCE_FRAME = 1', self.correction_source)
        self.assertIn('continuity_from_selected_f07_rms_degrees', self.adapter_source)
        self.assertIn('deviation_from_guard_rms_degrees', self.adapter_source)
        self.assertIn('SELECTED_F07_ARM_BLEND = 0.20', self.correction_source)

    def test_pass52_reconstructs_selected_f07_without_action_changes(self) -> None:
        self.assertIn('selected_f07_rotations = pass34_adapter._candidate_pose', self.adapter_source)
        self.assertIn('selected_f07_arm_pose', self.correction_source)
        self.assertIn('twohand_up_action_data_changed', self.adapter_source)
        self.assertIn('root_translation_used', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)
        self.assertNotIn('scale = -', self.adapter_source)

    def test_pass52_is_diagnostic_and_preserves_final_boundary_contract(self) -> None:
        self.assertIn('diagnostic_only', self.adapter_source)
        self.assertIn('manual_selection_required', self.adapter_source)
        self.assertIn('accepted_by_final_boundary_contract', self.adapter_source)
        self.assertIn('REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE', self.adapter_source)
        self.assertIn('REVIEW_VARIANT_COUNT = 6', self.correction_source)

    def test_workflow_uses_pass52_and_retains_pass51(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_f08_review_v21_pass52.py',
            self.workflow_source,
        )
        self.assertIn('f08 settle review', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass51.py',
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
