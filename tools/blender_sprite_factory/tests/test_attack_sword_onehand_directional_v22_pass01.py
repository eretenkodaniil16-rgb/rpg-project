from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from attack_sword_onehand_directional_correction_v22_pass01 import (
    BONE_DELTAS_DEGREES_BY_DIRECTION,
    FRAME_WEIGHTS,
    PRESERVE_DOWN_PIXELS,
    PRESERVE_ONEHAND_UP_V21,
    PRESERVE_SOURCE_FCURVE_TIMING,
    PRESERVE_TWOHAND_BASELINE,
    SOURCE_MASTER_ACTION_ID,
    TARGET_ACTION_ID_BY_DIRECTION,
    TARGET_DIRECTIONS,
    TARGET_FRAMES,
)


class AttackSwordOnehandDirectionalV22Pass01Tests(unittest.TestCase):
    def test_source_and_targets_are_stable(self) -> None:
        self.assertEqual(
            SOURCE_MASTER_ACTION_ID,
            "attack_sword_01_onehand_down_v20",
        )
        self.assertEqual(TARGET_DIRECTIONS, ("left", "right", "up"))
        self.assertEqual(
            tuple(TARGET_ACTION_ID_BY_DIRECTION),
            TARGET_DIRECTIONS,
        )
        self.assertEqual(len(set(TARGET_ACTION_ID_BY_DIRECTION.values())), 3)

    def test_corrections_are_local_and_extremely_small(self) -> None:
        self.assertEqual(TARGET_FRAMES, (4, 5, 6))
        self.assertEqual(tuple(FRAME_WEIGHTS), TARGET_FRAMES)
        for direction in TARGET_DIRECTIONS:
            self.assertEqual(
                set(BONE_DELTAS_DEGREES_BY_DIRECTION[direction]),
                {"upper_arm.R", "forearm.R", "hand.R"},
            )
            for values in BONE_DELTAS_DEGREES_BY_DIRECTION[direction].values():
                self.assertEqual(len(values), 3)
                self.assertLessEqual(max(abs(value) for value in values), 2.0)

    def test_up_action_is_preserved_without_local_deltas(self) -> None:
        self.assertTrue(PRESERVE_ONEHAND_UP_V21)
        for values in BONE_DELTAS_DEGREES_BY_DIRECTION["up"].values():
            self.assertEqual(values, (0.0, 0.0, 0.0))

    def test_preservation_contract_is_explicit(self) -> None:
        self.assertTrue(PRESERVE_SOURCE_FCURVE_TIMING)
        self.assertTrue(PRESERVE_DOWN_PIXELS)
        self.assertTrue(PRESERVE_TWOHAND_BASELINE)

    def test_builder_and_adapter_parse(self) -> None:
        paths = (
            SCRIPT_DIR
            / "attack_sword_onehand_directional_builder_v22_pass01.py",
            SCRIPT_DIR
            / "blender_sprite_factory_attack_sword_onehand_directional_v22_pass01.py",
        )
        for path in paths:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_builder_extends_existing_directional_action(self) -> None:
        builder_path = (
            SCRIPT_DIR
            / "attack_sword_onehand_directional_builder_v22_pass01.py"
        )
        source = builder_path.read_text(encoding="utf-8")
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass54(context)",
            source,
        )
        self.assertNotIn(".copy()", source)
        self.assertNotIn("scale = -", source)
        self.assertIn("directional_copy_of_approved_local_motion", source)
        self.assertIn("onehand_directional_up_source_preserved", source)


if __name__ == "__main__":
    unittest.main()
