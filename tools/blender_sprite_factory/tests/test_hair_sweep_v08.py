from __future__ import annotations

import ast
import unittest
from pathlib import Path

from hair_sweep_profile_v08 import load_hair_sweep_profile_v08


class HairSweepProfileV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_hair_sweep_profile_v08()

    def test_profile_matches_head_v08_proxy_v11(self) -> None:
        self.assertEqual(self.profile.revision, "v08")
        self.assertEqual(self.profile.proxy_revision, "v11")
        self.profile.assert_valid()

    def test_reference_hair_uses_three_coherent_sweep_meshes(self) -> None:
        self.assertEqual(
            [part.name for part in self.profile.meshes],
            ["hair_reference_shell", "hair_reference_nape", "hair_reference_forelock"],
        )
        shell, nape, forelock = self.profile.meshes
        self.assertEqual(shell.segments, 20)
        self.assertGreaterEqual(len(shell.rings), 7)
        self.assertEqual(nape.segments, 16)
        self.assertEqual(forelock.segments, 10)
        self.assertGreater(shell.rings[3].radius_x, shell.rings[-1].radius_x)
        self.assertGreater(shell.rings[1].center_y, shell.rings[3].center_y)
        self.assertLess(forelock.location[0], 0.0)
        self.assertLess(forelock.location[1], -0.4)

    def test_accents_are_asymmetric_without_mirroring(self) -> None:
        rotations = dict(self.profile.accent_rotations_degrees)
        self.assertLess(rotations["hair_front_hairline_left"][1], 0.0)
        self.assertGreater(rotations["hair_front_hairline_right"][1], 0.0)
        self.assertNotEqual(
            rotations["hair_side_mass_left"][2],
            -rotations["hair_side_mass_right"][2],
        )

    def test_builder_replaces_only_hair_with_profile_meshes(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        builder = tool_root / "hair_sweep_builder_v08.py"
        source = builder.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('obj.get(factory.MODULE_PROPERTY) == "hair"', source)
        self.assertIn("mesh.from_pydata(vertices, [], faces)", source)
        self.assertIn("replace_hair_with_reference_sweeps", source)
        self.assertIn('factory._register(', source)
        self.assertNotIn("scale.x = -1", source)
        self.assertNotIn("scale[0] = -1", source)

    def test_adapter_records_sweep_profile_and_builder_hashes(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        adapter = tool_root / "blender_sprite_factory_head_v08.py"
        source = adapter.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("replace_hair_with_reference_sweeps(context)", source)
        self.assertIn('"hair_sweep_profile"', source)
        self.assertIn('"hair_sweep_builder"', source)
        self.assertIn('"approved_reference_profile_sweep_meshes"', source)
        self.assertIn('"approved_reference_emission_color_ramp"', source)


if __name__ == "__main__":
    unittest.main()
