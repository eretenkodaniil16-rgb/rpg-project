from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v10.py").read_text(encoding="utf-8")
        cls.adapter_source = (cls.tool_root / "blender_sprite_factory_head_v10.py").read_text(encoding="utf-8")

    def test_builder_is_hair_only_and_reuses_proxy_v12_geometry(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("previous_builder.refine_reference_hair_locks(context)", self.builder_source)
        self.assertIn("_apply_dark_palette_to_existing_hair(materials)", self.builder_source)
        self.assertIn("_replace_lock_separator_mesh(context, materials[\"separator\"])", self.builder_source)
        self.assertIn('factory._register(context, obj, "hair", "head")', self.builder_source)

    def test_palette_uses_srgb_to_linear_emission_for_exact_dark_quantization(self) -> None:
        self.assertIn("_srgb_channel_to_linear", self.builder_source)
        self.assertIn("_hex_rgb_linear", self.builder_source)
        self.assertIn('emission.inputs["Strength"].default_value = 1.0', self.builder_source)
        self.assertIn('material["hair_palette_revision"]', self.builder_source)
        self.assertIn('"#060102"', (self.tool_root / "hair_palette_v10.py").read_text(encoding="utf-8"))
        self.assertIn('"#3C2411"', (self.tool_root / "hair_palette_v10.py").read_text(encoding="utf-8"))

    def test_all_consolidated_hair_parts_receive_explicit_dark_roles(self) -> None:
        self.assertIn("_SOURCE_HAIR_MATERIAL_ROLES", self.builder_source)
        self.assertIn("set(_SOURCE_HAIR_MATERIAL_ROLES) != set(SOURCE_HAIR_PART_NAMES)", self.builder_source)
        self.assertIn("_replace_profile_materials(crown, materials)", self.builder_source)
        self.assertIn("_replace_profile_materials(forelock, materials)", self.builder_source)
        self.assertIn("factory._assign_material(obj, materials[role])", self.builder_source)

    def test_curved_separator_replaces_v09_mesh_without_adding_hair_parts(self) -> None:
        self.assertIn("factory.bpy.data.objects.remove(old, do_unlink=True)", self.builder_source)
        self.assertIn("HairLockGrooveV10", self.builder_source)
        self.assertIn("len(groove.points_uv) - 1", self.builder_source)
        self.assertIn("ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES", self.builder_source)

    def test_positive_transform_and_no_mirroring_contract_remain(self) -> None:
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)
        self.assertNotIn("mirror", self.builder_source.lower())

    def test_adapter_records_v10_v13_dark_hair_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("load_head_profile_v10", self.adapter_source)
        self.assertIn("load_hair_lock_profile_v10", self.adapter_source)
        self.assertIn("load_hair_palette_v10", self.adapter_source)
        self.assertIn(
            '"approved_reference_dark_hair_with_curved_large_lock_grooves"',
            self.adapter_source,
        )
        self.assertIn('"quantization_exact_srgb_to_linear_emission_with_restrained_highlight"', self.adapter_source)
        self.assertIn('"skin_contrast_contract"', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
