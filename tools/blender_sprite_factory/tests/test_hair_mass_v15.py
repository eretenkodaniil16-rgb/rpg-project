from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v15.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v15.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_extends_proxy_v17_without_rebuilding_meshes(self) -> None:
        self.assertIn(
            "previous_builder.apply_major_profile_lock_pass(context)",
            self.builder_source,
        )
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertIn("len(obj.data.vertices) != 38", self.builder_source)
        self.assertIn("len(obj.data.polygons) != 42", self.builder_source)

    def test_exposure_pass_preserves_positive_physical_transforms(self) -> None:
        self.assertIn("obj.get(\"hair_physical_side\")", self.builder_source)
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertIn("world_matrix.translation += factory.Vector", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_locks_unrelated_character_systems(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v14(context)", self.adapter_source)
        self.assertIn("apply_major_lock_exposure_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v15", self.adapter_source)
        self.assertIn('"crown_changed": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"palette_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)
        self.assertIn('"new_hair_part_count": 0', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
