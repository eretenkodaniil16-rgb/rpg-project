from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v18.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v18.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_refines_one_completed_proxy_v20_scene(self) -> None:
        self.assertIn("_assert_previous_organic_state", self.builder_source)
        self.assertIn("completed proxy v20 scene", self.builder_source)
        self.assertNotIn("previous_builder.apply_organic_crown_back_pass", self.builder_source)
        self.assertIn("len(crown.data.vertices) != 226", self.builder_source)
        self.assertIn("len(crown.data.polygons) != 256", self.builder_source)

    def test_tone_pass_preserves_geometry_and_object_identity(self) -> None:
        self.assertIn("current_names != previous_names", self.builder_source)
        self.assertIn("sum(tone_counts.values())", self.builder_source)
        self.assertIn("counts[\"base\"] <= counts[\"mid\"]", self.builder_source)
        self.assertIn("4 <= counts[\"highlight\"] <= 24", self.builder_source)
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_locks_geometry_face_and_animation(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v17(context)", self.adapter_source)
        self.assertIn("apply_localized_organic_tone_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v18", self.adapter_source)
        self.assertIn('"forced_angularity": False', self.adapter_source)
        self.assertIn('"geometry_changed": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
