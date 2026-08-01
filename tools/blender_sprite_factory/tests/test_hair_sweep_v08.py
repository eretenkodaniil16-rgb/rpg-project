from __future__ import annotations

import ast
import math
import unittest
from pathlib import Path

from hair_sweep_profile_v08 import load_hair_sweep_profile_v08
from head_profile_v07 import HUMAN_WARRIOR_M01_HEAD_V07


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
        self.assertEqual(shell.segments, 24)
        self.assertGreaterEqual(len(shell.rings), 7)
        self.assertEqual(nape.segments, 18)
        self.assertEqual(forelock.segments, 12)
        self.assertGreater(shell.rings[3].radius_x, shell.rings[-1].radius_x)
        self.assertGreater(shell.rings[0].center_y, shell.rings[4].center_y)
        self.assertLess(forelock.location[0], 0.0)
        self.assertLess(forelock.location[1], -0.45)

    def test_crown_opening_narrows_upward_without_covering_lower_face(self) -> None:
        shell = self.profile.meshes[0]
        spans = [
            shell.ring_arc(ring)[1] - shell.ring_arc(ring)[0]
            for ring in shell.rings
        ]
        self.assertEqual(spans, sorted(spans))
        self.assertLessEqual(spans[0], 240.0)
        self.assertGreaterEqual(spans[-1], 350.0)
        self.assertFalse(shell.closed_around)

    def test_upper_crown_projects_ahead_of_locked_cranium(self) -> None:
        shell = self.profile.meshes[0]
        head = HUMAN_WARRIOR_M01_HEAD_V07.head_base
        for ring in shell.rings[3:5]:
            global_z = shell.location[2] + ring.z
            normalized_z = (global_z - head.location[2]) / head.scale[2]
            self.assertLess(abs(normalized_z), 1.0)
            head_front_y = head.location[1] - head.scale[1] * math.sqrt(
                1.0 - normalized_z * normalized_z
            )
            arc_start, arc_end = shell.ring_arc(ring)
            sampled_y = []
            for point_index in range(shell.segments + 1):
                angle = math.radians(
                    arc_start
                    + (arc_end - arc_start) * point_index / shell.segments
                )
                wave = 1.0 + shell.wave_amplitude * math.cos(
                    shell.wave_frequency * angle + math.radians(ring.phase_degrees)
                )
                sampled_y.append(
                    ring.center_y + ring.radius_y * math.sin(angle) * wave
                )
            self.assertLess(min(sampled_y), head_front_y - 0.04)

    def test_forelock_stays_above_eyes_and_is_long_enough_to_read(self) -> None:
        forelock = self.profile.meshes[2]
        eye_top = max(
            eye.location[2] + eye.dimensions[2] * 0.5
            for eye in HUMAN_WARRIOR_M01_HEAD_V07.eyes
        )
        forelock_bottom = forelock.location[2] + forelock.rings[0].z
        forelock_top = forelock.location[2] + forelock.rings[-1].z
        self.assertGreater(forelock_bottom, eye_top)
        self.assertGreater(forelock_top - forelock_bottom, 0.45)

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
        self.assertIn("_ring_arc(part, ring)", source)
        self.assertIn("if part.closed_around:", source)
        self.assertIn("mesh.validate(", source)
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
