from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordTwohandUpCycleDiagnosticV21Pass51Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass51.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY
            / "blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass51.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass51_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.adapter_source)

    def test_pass51_locks_selected_f07_review_candidate(self) -> None:
        self.assertIn('TARGET_FRAME = 7', self.correction_source)
        self.assertIn('F07_SOURCE_FRAME = 6', self.correction_source)
        self.assertIn('F07_ARM_BLEND = 0.20', self.correction_source)
        self.assertIn('F07_DEPTH_BRANCH = "source"', self.correction_source)
        self.assertIn('F07_WEAPON_OFFSET_DEGREES = 60.0', self.correction_source)
        self.assertIn('F07_REQUESTED_SCREEN_PROJECTION = 0.90', self.correction_source)
        self.assertIn('SOURCE_REVIEW_VARIANT = 1', self.correction_source)

    def test_pass51_uses_temporary_camera_shift_and_restores_it(self) -> None:
        self.assertIn('F07_CAMERA_SHIFT_X_CANDIDATES', self.correction_source)
        self.assertIn('camera.data.shift_x = float(shift_x)', self.adapter_source)
        self.assertIn('camera.data.shift_x = original_shift_x', self.adapter_source)
        self.assertIn('REQUIRE_ZERO_EDGE_ALPHA', self.adapter_source)
        self.assertIn('camera_shift_persistent_change', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)
        self.assertNotIn('scale = -', self.adapter_source)

    def test_pass51_records_selected_f07_without_action_or_geometry_changes(self) -> None:
        self.assertIn('SELECTED_F07_SCENE_KEY', self.adapter_source)
        self.assertIn('selected_f07', self.adapter_source)
        self.assertIn('_write_manifest_v21_pass51', self.adapter_source)
        self.assertIn('twohand_up_action_data_changed', self.adapter_source)
        self.assertIn('root_translation_used', self.adapter_source)
        self.assertIn('weapon_geometry_changed', self.adapter_source)
        self.assertIn('_restore_pass49_contract', self.adapter_source)

    def test_workflow_uses_pass51_and_retains_pass50(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass51.py',
            self.workflow_source,
        )
        self.assertIn('selected f07 full cycle', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_f07_review_v21_pass50.py',
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
