from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "tools" / "blender_sprite_factory"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-human-warrior-attack-directional-v21.yml"


class AttackSwordDirectionalCycleV21Pass54Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.correction_source = (
            FACTORY / "attack_sword_directional_cycle_correction_v21_pass54.py"
        ).read_text(encoding="utf-8")
        self.builder_source = (
            FACTORY / "attack_sword_directional_cycle_builder_v21_pass54.py"
        ).read_text(encoding="utf-8")
        self.adapter_source = (
            FACTORY / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass54.py"
        ).read_text(encoding="utf-8")
        self.workflow_source = WORKFLOW.read_text(encoding="utf-8")

    def test_pass54_sources_parse(self) -> None:
        ast.parse(self.correction_source)
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_pass54_integrates_selected_arm_frames_into_action(self) -> None:
        self.assertIn('ACTION_CHANGED_FRAMES = (1, 2, 3, 7, 8)', self.correction_source)
        self.assertIn('ACTION_BONE_DELTAS_DEGREES_BY_FRAME', self.correction_source)
        self.assertIn('create_attack_sword_directional_cycle_actions_v21_pass26', self.builder_source)
        self.assertIn('_fcurve', self.builder_source)
        self.assertIn('_point', self.builder_source)
        self.assertIn('directional_twohand_up_action_data_changed', self.builder_source)
        self.assertIn('twohand_up_changed"] = True', self.builder_source)

    def test_pass54_preserves_rigid_weapon_and_export_framing_scope(self) -> None:
        self.assertIn('PROJECTED_WEAPON_PROFILE_BY_FRAME', self.correction_source)
        self.assertIn('ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME', self.correction_source)
        self.assertIn('CAMERA_SHIFT_X_BY_FRAME', self.correction_source)
        self.assertIn('CAMERA_SHIFT_Y_BY_FRAME', self.correction_source)
        self.assertIn('camera.data.shift_x = original_shift_x', self.adapter_source)
        self.assertIn('camera.data.shift_y = original_shift_y', self.adapter_source)
        self.assertIn('pass06_adapter._restore_weapon', self.adapter_source)
        self.assertIn('REQUIRE_ZERO_EDGE_ALPHA', self.adapter_source)
        self.assertNotIn('location +=', self.adapter_source)
        self.assertNotIn('scale = -', self.adapter_source)

    def test_pass54_extends_latest_full_directional_pipeline(self) -> None:
        self.assertIn('pass28_adapter.main()', self.adapter_source)
        self.assertIn('ORIGINAL_PASS28_RENDER', self.adapter_source)
        self.assertIn('ORIGINAL_PASS28_WRITE_MANIFEST', self.adapter_source)
        self.assertIn('create_attack_sword_directional_cycle_actions_v21_pass54', self.adapter_source)
        self.assertIn('_validate_directional_clearance_v21_pass54', self.adapter_source)
        self.assertIn('_restore_pass54_contract', self.adapter_source)

    def test_pass54_manifest_locks_64_frame_integrated_contract(self) -> None:
        self.assertIn('action_data_changed', self.adapter_source)
        self.assertIn('rigid_weapon_transform_used', self.adapter_source)
        self.assertIn('temporary_camera_overscan_used', self.adapter_source)
        self.assertIn('camera_shift_persistent_change', self.adapter_source)
        self.assertIn('approved_down_v20_changed', self.adapter_source)
        self.assertIn('manual_directional_review_required', self.adapter_source)

    def test_workflow_uses_pass54_and_retains_pass53(self) -> None:
        lowered = self.workflow_source.lower()
        self.assertIn(
            'blender_sprite_factory_attack_sword_directional_cycle_v21_pass54.py',
            self.workflow_source,
        )
        self.assertIn('integrated 64 frame cycle', lowered)
        self.assertIn(
            'blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass53.py',
            self.workflow_source,
        )


if __name__ == "__main__":
    unittest.main()
