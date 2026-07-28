from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v13.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v13.py"
        ).read_text(encoding="utf-8")

    def test_builder_is_hair_only_and_reuses_proxy_v15(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("previous_builder.apply_scalp_coverage_pass(context)", self.builder_source)
        self.assertIn("_apply_crown_side_back_vertices(crown)", self.builder_source)
        self.assertIn("_apply_existing_mass_transforms()", self.builder_source)
        self.assertNotIn("factory._register(context", self.builder_source)

    def test_existing_masses_receive_positive_asymmetric_transforms(self) -> None:
        self.assertIn("obj.scale = tuple(", self.builder_source)
        self.assertIn("math.radians(transform.rotation_delta_degrees[index])", self.builder_source)
        self.assertIn(
            "world_matrix.translation += factory.Vector(transform.world_offset)",
            self.builder_source,
        )
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)
        self.assertNotIn("mirror", self.builder_source.lower())

    def test_adapter_records_v13_v16_side_back_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("load_head_profile_v13", self.adapter_source)
        self.assertIn("load_hair_crown_profile_v13", self.adapter_source)
        self.assertIn("load_hair_side_back_profile_v13", self.adapter_source)
        self.assertIn(
            '"approved_reference_wavy_side_and_rear_medium_hair_silhouette"',
            self.adapter_source,
        )
        self.assertIn('"new_hair_part_count": 0', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
