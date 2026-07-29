from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV21Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v21.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v21.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_requires_completed_proxy_v23_state(self) -> None:
        self.assertIn("_assert_proxy_v23_state", self.builder_source)
        self.assertIn("completed proxy v23 scene", self.builder_source)
        self.assertIn('crown.get("hair_proxy_revision") != "v23"', self.builder_source)
        self.assertIn("len(crown.data.vertices) != 226", self.builder_source)
        self.assertIn("len(crown.data.polygons) != 256", self.builder_source)

    def test_builder_refines_existing_scene_without_rebuilding_proxy_v23(self) -> None:
        self.assertNotIn(
            "previous_builder.apply_dense_crown_restoration_pass(context)",
            self.builder_source,
        )
        self.assertIn("previous_adapter._build_head_and_hair_v20(context)", self.adapter_source)
        self.assertIn("_apply_side_nape_transforms", self.builder_source)
        self.assertIn("crown_coordinates_before", self.builder_source)
        self.assertIn("must not modify the accepted proxy v23 crown mesh", self.builder_source)
        self.assertNotIn("mesh.from_pydata", self.builder_source)
        self.assertNotIn("bpy.data.meshes.new", self.builder_source)

    def test_density_and_topology_guards_are_explicit(self) -> None:
        self.assertIn("reduced a retained hair mass", self.builder_source)
        self.assertIn("reduced visible side/nape volume", self.builder_source)
        self.assertIn("len(obj.data.vertices) != 38", self.builder_source)
        self.assertIn("len(obj.data.polygons) != 42", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_locks_unrelated_geometry_and_animation(self) -> None:
        self.assertIn("apply_side_nape_volume_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v21", self.adapter_source)
        self.assertIn('"crown_geometry_changed": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)
        self.assertIn('"visible_density_reduction_allowed": False', self.adapter_source)
        self.assertIn('"long_hanging_locks_allowed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
