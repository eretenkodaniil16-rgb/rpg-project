from __future__ import annotations

import ast
import unittest
from pathlib import Path

from attack_sword_down_cycle_correction_v20_pass04 import (
    ANGLE_CANDIDATES_DEGREES,
    CORRECTION_PASS,
    KNOWN_FAILED_ARTIFACT_ID,
    KNOWN_FAILED_ARTIFACT_SHA256,
    KNOWN_FAILED_OFFSET_MAX_DEGREES,
    KNOWN_FAILED_OFFSET_MIN_DEGREES,
    KNOWN_FAILED_RUN_ID,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_CONTAINMENT_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)


class AttackSwordDownCycleV20Pass04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_source = (
            cls.tool_root
            / "blender_sprite_factory_attack_sword_down_cycle_v20_pass04.py"
        ).read_text(encoding="utf-8")

    def test_identity_and_bounded_extension(self) -> None:
        self.assertEqual(CORRECTION_PASS, "v20_pass04")
        self.assertEqual(
            ONEHAND_CONTAINMENT_REVISION,
            "export_space_positive_extension_v20_pass04",
        )
        self.assertEqual(TARGET_ANIMATION_ID, "attack_sword_01_onehand_down_v20")
        self.assertEqual(TARGET_FRAME, 6)
        self.assertEqual(ANGLE_CANDIDATES_DEGREES[0], 42.0)
        self.assertEqual(ANGLE_CANDIDATES_DEGREES[-1], 60.0)
        self.assertEqual(len(ANGLE_CANDIDATES_DEGREES), 10)
        self.assertEqual(tuple(sorted(set(ANGLE_CANDIDATES_DEGREES))), ANGLE_CANDIDATES_DEGREES)
        self.assertTrue(all(value > KNOWN_FAILED_OFFSET_MAX_DEGREES for value in ANGLE_CANDIDATES_DEGREES))
        self.assertEqual(MIN_HEAD_CLEARANCE_PIXELS, 4.0)
        self.assertTrue(REQUIRE_ZERO_EDGE_ALPHA)

    def test_failed_pass03_is_traceable(self) -> None:
        self.assertEqual(KNOWN_FAILED_RUN_ID, 30720688002)
        self.assertEqual(KNOWN_FAILED_ARTIFACT_ID, 8824976123)
        self.assertEqual(KNOWN_FAILED_OFFSET_MIN_DEGREES, -40.0)
        self.assertEqual(KNOWN_FAILED_OFFSET_MAX_DEGREES, 40.0)
        self.assertEqual(len(KNOWN_FAILED_ARTIFACT_SHA256), 64)

    def test_adapter_reuses_exact_export_validation(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn(
            "import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as previous_adapter",
            self.adapter_source,
        )
        self.assertIn(
            "previous_adapter._candidate_offsets = _candidate_offsets_v20_pass04",
            self.adapter_source,
        )
        self.assertIn("return ANGLE_CANDIDATES_DEGREES", self.adapter_source)
        self.assertIn(
            "previous_adapter._write_manifest_v20_pass03 = _write_manifest_v20_pass04",
            self.adapter_source,
        )
        self.assertIn('"export_space_validated": True', self.adapter_source)

    def test_adapter_preserves_locked_art_contract(self) -> None:
        self.assertIn('"body_pose_changed": False', self.adapter_source)
        self.assertIn('"approved_v19_anchor_frames_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_changed": False', self.adapter_source)
        self.assertIn('"weapon_geometry_deformed": False', self.adapter_source)
        self.assertIn('"materials_changed": False', self.adapter_source)
        self.assertIn('"manual_full_cycle_review_required": True', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
