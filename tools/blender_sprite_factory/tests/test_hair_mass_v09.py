from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v09.py").read_text(encoding="utf-8")
        cls.adapter_source = (cls.tool_root / "blender_sprite_factory_head_v09.py").read_text(encoding="utf-8")

    def test_builder_is_hair_only_and_reuses_v08_crown_forelock(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("previous_builder.consolidate_reference_hair_masses(context)", self.builder_source)
        self.assertIn('factory._register(context, obj, "hair", "head")', self.builder_source)
        self.assertIn('"hair_reference_crown_mesh"', self.builder_source)
        self.assertIn('"hair_reference_forelock_mesh"', self.builder_source)
        self.assertIn("load_hair_lock_profile_v09", self.builder_source)

    def test_builder_adds_one_mesh_for_eight_large_grooves(self) -> None:
        self.assertIn("_build_lock_separator_mesh(context)", self.builder_source)
        self.assertIn("_ribbon_vertices(groove)", self.builder_source)
        self.assertIn('obj["hair_lock_groove_count"]', self.builder_source)
        self.assertIn('obj["hair_shape_zone"] = "large_lock_separators"', self.builder_source)
        self.assertIn("len(_LOCK_PROFILE.grooves)", self.builder_source)
        self.assertIn("ACTIVE_HAIR_PART_NAMES = frozenset", self.builder_source)

    def test_facet_stripes_are_retoned_into_broad_masses(self) -> None:
        self.assertIn("_retone_profile_meshes()", self.builder_source)
        self.assertIn('"broad_masses_with_dark_separators"', self.builder_source)
        self.assertIn('"single_readable_forelock"', self.builder_source)
        self.assertIn("polygon.material_index = 2", self.builder_source)

    def test_positive_transform_contract_remains(self) -> None:
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_records_v09_v12_profiles_and_lock_strategy(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("load_head_profile_v09", self.adapter_source)
        self.assertIn("load_hair_lock_profile_v09", self.adapter_source)
        self.assertIn('"revision": "v08"', self.adapter_source)
        self.assertIn('"proxy_revision": "v11"', self.adapter_source)
        self.assertIn(
            '"approved_reference_large_lock_grooves_over_single_crown_and_forelock"',
            self.adapter_source,
        )
        self.assertIn('"lock_separator_mesh"', self.adapter_source)
        self.assertIn('"broad_mid_tones_with_dark_geometric_separators"', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
