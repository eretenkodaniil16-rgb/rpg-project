from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v20.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v20.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_dense_pass_branches_from_proxy_v21_not_rejected_v22(self) -> None:
        self.assertIn("completed proxy v21 scene", self.builder_source)
        self.assertIn("not rejected proxy v22", self.builder_source)
        self.assertNotIn("hair_mass_builder_v19 as previous_builder", self.builder_source)
        self.assertIn("blender_sprite_factory_head_v18 as previous_adapter", self.adapter_source)
        self.assertNotIn("blender_sprite_factory_head_v19 as previous_adapter", self.adapter_source)

    def test_dense_pass_preserves_width_topology_and_identity(self) -> None:
        self.assertIn("must not change hair object identities", self.builder_source)
        self.assertIn("len(crown.data.vertices) != 226", self.builder_source)
        self.assertIn("len(crown.data.polygons) != 256", self.builder_source)
        self.assertIn("preserve_full_hair_density_without_bald_taper", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_records_rejected_candidate_and_locked_systems(self) -> None:
        self.assertIn('"rejected_candidate"', self.adapter_source)
        self.assertIn('"used_as_build_parent": False', self.adapter_source)
        self.assertIn('"rear_taper_allowed": False', self.adapter_source)
        self.assertIn('"visible_density_reduction_allowed": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v20", self.adapter_source)


if __name__ == "__main__":
    unittest.main()
