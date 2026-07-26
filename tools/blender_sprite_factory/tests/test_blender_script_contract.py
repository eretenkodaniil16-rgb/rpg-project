from __future__ import annotations

import ast
import unittest
from pathlib import Path


class BlenderScriptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.script = cls.tool_root / "blender_sprite_factory.py"
        cls.source = cls.script.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_script_is_valid_python_without_importing_bpy(self) -> None:
        self.assertGreater(sum(1 for _ in ast.walk(self.tree)), 1000)

    def test_blender_52_slotted_actions_are_used(self) -> None:
        self.assertIn('action.slots.new(id_type="OBJECT"', self.source)
        self.assertIn('strip.channelbag(slot, ensure=True)', self.source)
        self.assertIn('point.interpolation = "CONSTANT"', self.source)

    def test_parts_are_bone_parented_and_materials_are_replaceable(self) -> None:
        self.assertIn('obj.parent_type = "BONE"', self.source)
        self.assertIn('texture.interpolation = "Closest"', self.source)
        self.assertIn('obj[MODULE_PROPERTY] = module_id', self.source)

    def test_render_contract_enforces_real_turns_and_binary_alpha(self) -> None:
        self.assertIn('context.rig.rotation_euler[2]', self.source)
        self.assertIn('fixed_scale=down_calibration.scale', self.source)
        self.assertIn('fixed_center_x=down_calibration.source_center_x', self.source)
        self.assertIn('if alpha < 0.5:', self.source)
        self.assertIn('output_pixels[destination_index + 3] = 1.0', self.source)
        self.assertNotIn("scale.x = -1", self.source)
        self.assertNotIn("scale[0] = -1", self.source)

    def test_windows_powershell_launcher_is_ascii_safe(self) -> None:
        launcher = self.tool_root / "run_blender_sprite_pilot.ps1"
        self.assertTrue(
            launcher.read_bytes().isascii(),
            "Windows PowerShell 5.1 requires this launcher to remain ASCII-only",
        )


if __name__ == "__main__":
    unittest.main()
