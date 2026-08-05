from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_directional_cycle_correction_v21_pass34 import (
    ARM_BLEND_CANDIDATES,
    CORRECTED_F01_ARM_BLEND,
    CORRECTED_F01_SOURCE_FRAME,
    CORRECTION_PASS,
    MAX_ABS_WEAPON_OFFSET_DEGREES,
    NEXT_REFERENCE_FRAME,
    REVIEW_VARIANT_COUNT,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    SOURCE_POSE_CODES,
    SOURCE_POSE_LABELS,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION,
)


class AttackSwordTwohandUpF02ReviewV21Pass34Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f02_review_v21_pass34.py"
        )
        cls.adapter_source = (
            cls.tool_root / cls.adapter_name
        ).read_text(encoding="utf-8")
        cls.workflow_source = (
            cls.tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-human-warrior-attack-directional-v21.yml"
        ).read_text(encoding="utf-8")

    def test_continuity_review_contract(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v21_pass34")
        self.assertEqual(
            TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION,
            "twohand_up_f02_corrected_f01_to_f03_continuity_review_v21_pass34",
        )
        self.assertEqual(TARGET_ACTION_ID, "attack_sword_01_twohand_up_v21")
        self.assertEqual(TARGET_GRIP_ID, "twohand_center_high")
        self.assertEqual(TARGET_DIRECTION, "up")
        self.assertEqual(TARGET_FRAME, 2)
        self.assertEqual(NEXT_REFERENCE_FRAME, 3)
        self.assertEqual(CORRECTED_F01_SOURCE_FRAME, 5)
        self.assertEqual(CORRECTED_F01_ARM_BLEND, 0.60)
        self.assertEqual(SOURCE_POSE_CODES[0], 101)
        self.assertEqual(SOURCE_POSE_LABELS[101], "corrected_f01")
        self.assertEqual(min(ARM_BLEND_CANDIDATES), 0.10)
        self.assertEqual(max(ARM_BLEND_CANDIDATES), 1.00)
        self.assertEqual(MAX_ABS_WEAPON_OFFSET_DEGREES, 48.0)
        self.assertEqual(REVIEW_VARIANT_COUNT, 6)
        self.assertEqual(SOURCE_FAILED_RUN_ID, 30854097806)
        self.assertEqual(SOURCE_FAILED_ARTIFACT_ID, 8871808585)

    def test_adapter_uses_corrected_f01_and_original_f03_continuity(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("_blended_rotations", self.adapter_source)
        self.assertIn("_arm_rms_degrees", self.adapter_source)
        self.assertIn("continuity_from_corrected_f01_rms_degrees", self.adapter_source)
        self.assertIn("continuity_to_original_f03_rms_degrees", self.adapter_source)
        self.assertIn("pass29_adapter.TARGET_FRAME = TARGET_FRAME", self.adapter_source)
        self.assertIn("_render_corrected_f01_reference", self.adapter_source)
        self.assertIn("_render_original_f03_reference", self.adapter_source)
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertNotIn("point.co[1] =", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)
        self.assertNotIn("hide_render = True", self.adapter_source)

    def test_workflow_uses_pass34_and_keeps_full_entrypoint(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("twohand up f02", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
