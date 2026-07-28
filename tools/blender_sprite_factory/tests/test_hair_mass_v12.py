from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v12.py").read_text(encoding="utf-8")
        cls.adapter_source = (cls.tool_root / "blender_sprite_factory_head_v12.py").read_text(encoding="utf-8")

    def test_builder_reuses_v14_and_changes_only_existing_crown_vertices(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("previous_builder.apply_physical_lock_shape_pass(context)", self.builder_source)
        self.assertIn("_apply_crown_coverage_vertices(crown)", self.builder_source)
        self.assertIn('factory.bpy.data.objects.get(_CROWN_PROFILE.mesh_name)', self.builder_source)
        self.assertNotIn("bpy.data.objects.new", self.builder_source)
        self.assertNotIn("_FORELOCK_PROFILE", self.builder_source)
        self.assertNotIn("_LOCK_PROFILE", self.builder_source)

    def test_coverage_contract_preserves_palette_and_part_count(self) -> None:
        self.assertIn('"raise_internal_wave_valleys_without_changing_outer_silhouette"', self.builder_source)
        self.assertIn('"hair_coverage_adjusted_indices"', self.builder_source)
        self.assertIn("ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES", self.builder_source)
        self.assertIn("material.get(\"hair_palette_revision\") != _PALETTE.revision", self.builder_source)

    def test_positive_transform_and_no_mirroring_contract_remain(self) -> None:
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)
        self.assertNotIn("mirror", self.builder_source.lower())

    def test_adapter_records_v12_v15_scalp_coverage_hotfix(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("load_head_profile_v12", self.adapter_source)
        self.assertIn("load_hair_crown_profile_v12", self.adapter_source)
        self.assertIn("apply_scalp_coverage_pass", self.adapter_source)
        self.assertIn('"approved_reference_physical_waves_with_closed_scalp_coverage"', self.adapter_source)
        self.assertIn('"new_hair_part_count": 0', self.adapter_source)
        self.assertIn('"palette_changed": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"separator_geometry_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
