from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordTwohandUpCycleDiagnosticV21Pass49Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass49.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass49.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass49_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.adapter_source)

    def test_pass49_targets_only_f06_local_export_framing(self) -> None:
        self.assertIn('TARGET_FRAME = 6', self.correction_source)
        self.assertIn('F06_FIXED_WEAPON_OFFSET_DEGREES = 30.0', self.correction_source)
        self.assertIn('F06_CAMERA_SHIFT_X_CANDIDATES', self.correction_source)
        self.assertIn('_targeted_f06_candidate_offsets', self.adapter_source)
        self.assertIn('camera.data.shift_x = original_shift_x', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)
        self.assertNotIn('scale = -', self.adapter_source)

    def test_pass49_records_and_restores_selected_f06(self) -> None:
        self.assertIn('SELECTED_F06_SCENE_KEY', self.adapter_source)
        self.assertIn('selected_f06', self.adapter_source)
        self.assertIn('_write_manifest_v21_pass49', self.adapter_source)
        self.assertIn('_restore_pass48_contract', self.adapter_source)
        self.assertIn(
            'pass02_adapter._candidate_offsets = ORIGINAL_PASS02_CANDIDATE_OFFSETS',
            self.adapter_source,
        )

    def test_workflow_uses_pass49_and_retains_pass48(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass49.py',
            self.workflow_source,
        )
        self.assertIn('f06 local overscan', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass48.py',
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
