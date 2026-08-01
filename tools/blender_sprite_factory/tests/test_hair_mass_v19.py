from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v19.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v19.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_refines_one_completed_proxy_v21_scene(self) -> None:
        self.assertIn("_assert_previous_tone_state", self.builder_source)
        self.assertIn("completed proxy v21 scene", self.builder_source)
        self.assertIn('crown.get("hair_proxy_revision") != "v21"', self.builder_source)
        self.assertIn("len(crown.data.vertices) != 226", self.builder_source)
        self.assertIn("len(crown.data.polygons) != 256", self.builder_source)

    def test_volume_pass_rebuilds_only_the_integrated_crown(self) -> None:
        self.assertIn("_build_organic_geometry(profile)", self.builder_source)
        self.assertIn("mesh.from_pydata", self.builder_source)
        self.assertIn("current_names != previous_names", self.builder_source)
        self.assertIn("RETAINED_PROFILE_LOCK_NAMES", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_locks_face_palette_tones_and_animation(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v18(context)", self.adapter_source)
        self.assertIn("apply_centered_volume_taper_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v19", self.adapter_source)
        self.assertIn('"forced_angularity": False', self.adapter_source)
        self.assertIn('"monolithic_cap_allowed": False', self.adapter_source)
        self.assertIn('"tone_regions_changed": False', self.adapter_source)
        self.assertIn('"geometry_changed": True', self.adapter_source)
        self.assertIn('"topology_changed": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
