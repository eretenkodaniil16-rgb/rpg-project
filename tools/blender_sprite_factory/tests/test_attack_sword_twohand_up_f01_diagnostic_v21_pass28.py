from __future__ import annotations

import ast
import unittest
from pathlib import Path


class AttackSwordTwohandUpF01DiagnosticV21Pass28Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.adapter_name = (
            "blender_sprite_factory_attack_sword_twohand_up_"
            "f01_diagnostic_v21_pass28.py"
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

    def test_diagnostic_is_single_frame_and_uses_integrated_actions(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("TARGET_FRAME = 1", self.adapter_source)
        self.assertIn(
            "create_attack_sword_directional_cycle_actions_v21_pass26",
            self.adapter_source,
        )
        self.assertIn("_render_frame_v21_pass27", self.adapter_source)
        self.assertIn(
            "_depth_search_visible_blade_head_clearance",
            self.adapter_source,
        )
        self.assertIn("diagnostic_only", self.adapter_source)
        self.assertIn("twohand_up_action_data_changed", self.adapter_source)
        self.assertNotIn("vertex.co =", self.adapter_source)
        self.assertNotIn("root.location", self.adapter_source)
        self.assertNotIn("obj.scale", self.adapter_source)

    def test_workflow_runs_focused_diagnostic_before_full_integration(self) -> None:
        self.assertIn(self.adapter_name, self.workflow_source)
        self.assertIn("twohand up f01", self.workflow_source.lower())
        self.assertIn(
            "blender_sprite_factory_attack_sword_directional_cycle_v21_pass28.py",
            self.workflow_source,
        )
        self.assertIn("full directional cycle", self.workflow_source)


if __name__ == "__main__":
    unittest.main()
