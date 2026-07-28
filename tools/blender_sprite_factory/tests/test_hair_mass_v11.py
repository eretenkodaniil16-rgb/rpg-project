from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v11.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v11.py"
        ).read_text(encoding="utf-8")

    def test_builder_reuses_dark_v10_pass_and_changes_only_hair_geometry(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn("previous_builder.apply_dark_reference_hair_pass(context)", self.builder_source)
        self.assertIn("_apply_profile_vertices(crown, _CROWN_PROFILE)", self.builder_source)
        self.assertIn("_apply_profile_vertices(forelock, _FORELOCK_PROFILE)", self.builder_source)
        self.assertIn("load_hair_palette_v10", self.builder_source)

    def test_crown_and_forelock_keep_one_mesh_each(self) -> None:
        self.assertIn('"hair_reference_crown_mesh"', (
            self.tool_root / "hair_crown_profile_v11.py"
        ).read_text(encoding="utf-8"))
        self.assertIn('"hair_reference_forelock_mesh"', (
            self.tool_root / "hair_forelock_profile_v11.py"
        ).read_text(encoding="utf-8"))
        self.assertIn("ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES", self.builder_source)
        self.assertIn('"new_hair_part_count": 0', self.adapter_source)

    def test_long_separator_mesh_is_replaced_by_localized_depressions(self) -> None:
        self.assertIn("_replace_local_separator_mesh(context)", self.builder_source)
        self.assertIn('"localized_interlock_depressions"', self.builder_source)
        self.assertIn("len(_LOCK_PROFILE.grooves)", self.builder_source)
        self.assertIn('"six_short_local_depressions_supporting_physical_shape"', self.adapter_source)

    def test_tonal_groups_are_contiguous_instead_of_alternating_stripes(self) -> None:
        self.assertIn("_retone_crown(crown)", self.builder_source)
        self.assertIn("_retone_forelock(forelock)", self.builder_source)
        self.assertIn('"broad_contiguous_masses_without_radial_stripes"', self.builder_source)
        self.assertIn('"reuse_dark_v10_ramp_with_contiguous_tonal_masses"', self.adapter_source)

    def test_positive_transform_contract_remains(self) -> None:
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_records_v11_v14_physical_shape_contract(self) -> None:
        ast.parse(self.adapter_source)
        self.assertIn("load_head_profile_v11", self.adapter_source)
        self.assertIn("load_hair_crown_profile_v11", self.adapter_source)
        self.assertIn("load_hair_forelock_profile_v11", self.adapter_source)
        self.assertIn("load_hair_lock_profile_v11", self.adapter_source)
        self.assertIn(
            '"approved_reference_physical_large_waves_and_single_forelock"',
            self.adapter_source,
        )


if __name__ == "__main__":
    unittest.main()
