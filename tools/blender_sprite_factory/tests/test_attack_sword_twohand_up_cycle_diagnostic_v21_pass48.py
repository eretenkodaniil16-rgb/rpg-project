from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordTwohandUpCycleDiagnosticV21Pass48Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass48.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass48.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass48_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.adapter_source)

    def test_pass48_targets_only_f04_export_framing(self) -> None:
        self.assertIn('TARGET_FRAME = 4', self.correction_source)
        self.assertIn('F04_FIXED_WEAPON_OFFSET_DEGREES = 32.0', self.correction_source)
        self.assertIn('F04_CAMERA_SHIFT_X_CANDIDATES', self.correction_source)
        self.assertIn('-0.120', self.correction_source)
        self.assertIn('pass02_adapter._candidate_offsets', self.adapter_source)
        self.assertIn('_targeted_f04_candidate_offsets', self.adapter_source)
        self.assertIn('root_translation_used', (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass47.py"
        ).read_text(encoding="utf-8"))

    def test_pass48_preserves_model_and_restores_patches(self) -> None:
        self.assertIn('ORIGINAL_PASS47_BASE_RENDER', self.adapter_source)
        self.assertIn('_restore_pass47_contract', self.adapter_source)
        self.assertIn(
            'pass02_adapter._candidate_offsets = ORIGINAL_PASS02_CANDIDATE_OFFSETS',
            self.adapter_source,
        )
        self.assertNotIn('scale = -', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)

    def test_workflow_uses_pass48_and_retains_pass47(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass48.py',
            self.workflow_source,
        )
        self.assertIn('f04 targeted extended overscan', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass47.py',
            self.workflow_source,
        )
        self.assertIn('f01 f02 f03 selected full cycle', lowered)


if __name__ == "__main__":
    unittest.main()
