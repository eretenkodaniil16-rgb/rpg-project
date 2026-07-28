from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v14.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v14.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_extends_v13_and_replaces_mesh_data(self) -> None:
        self.assertIn(
            "previous_builder.apply_side_back_silhouette_pass(context)",
            self.builder_source,
        )
        self.assertIn("obj.data = mesh", self.builder_source)
        self.assertIn("six_ring_pointed_profile_replacing_uv_ellipsoid", self.builder_source)
        self.assertIn("len(obj.data.vertices) != 38", self.builder_source)
        self.assertIn("len(obj.data.polygons) != 42", self.builder_source)

    def test_pass_keeps_names_materials_and_positive_transforms(self) -> None:
        self.assertIn("previous_materials = tuple(obj.data.materials)", self.builder_source)
        self.assertIn("obj[factory.MATERIAL_PROPERTY] = \"hair\"", self.builder_source)
        self.assertIn("ACTIVE_HAIR_PART_NAMES.difference(actual_names)", self.builder_source)
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)
        self.assertNotIn("mirror", self.builder_source.lower())

    def test_adapter_advances_only_head_builder_and_manifest(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v13(context)", self.adapter_source)
        self.assertIn("apply_major_profile_lock_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v14", self.adapter_source)
        self.assertIn('"proxy_revision": "v16"', self.adapter_source)
        self.assertIn("replace_eight_uv_ellipsoids_with_six_ring_pointed_profile_meshes", self.adapter_source)
        self.assertIn('"new_hair_part_count": 0', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
