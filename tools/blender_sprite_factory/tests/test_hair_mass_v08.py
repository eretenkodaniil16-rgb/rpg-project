from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile_v08 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V08,
    HUMAN_WARRIOR_M01_HEAD_V08,
)


EXPECTED_SOURCE_HAIR_NAMES = {
    "hair_back_shell",
    "hair_back_sweep_left",
    "hair_back_sweep_right",
    "hair_front_hairline_left",
    "hair_front_hairline_right",
    "hair_side_mass_left",
    "hair_side_mass_right",
    "hair_nape_left",
    "hair_nape_center",
    "hair_nape_right",
}
EXPECTED_ACTIVE_HAIR_NAMES = {
    *EXPECTED_SOURCE_HAIR_NAMES,
    "hair_reference_crown_mesh",
    "hair_reference_forelock_mesh",
}


def _frozenset_strings_from_assignment(source: str, assignment_name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == assignment_name
            for target in node.targets
        ):
            continue
        call = node.value
        if not isinstance(call, ast.Call) or not call.args:
            break
        set_node = call.args[0]
        if not isinstance(set_node, ast.Set):
            break
        return {
            element.value
            for element in set_node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        }
    raise AssertionError(f"{assignment_name} was not found")


class HairMassBuilderV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_path = cls.tool_root / "hair_mass_builder_v08.py"
        cls.builder_source = cls.builder_path.read_text(encoding="utf-8")
        cls.source_names = _frozenset_strings_from_assignment(
            cls.builder_source,
            "SOURCE_HAIR_PART_NAMES",
        )

    def test_source_set_matches_consolidated_reference_contract(self) -> None:
        self.assertEqual(self.source_names, EXPECTED_SOURCE_HAIR_NAMES)
        self.assertEqual(len(self.source_names), 10)
        self.assertIn('"hair_reference_crown_mesh"', self.builder_source)
        self.assertIn('"hair_reference_forelock_mesh"', self.builder_source)
        self.assertEqual(len(EXPECTED_ACTIVE_HAIR_NAMES), 12)

    def test_every_source_name_exists_in_head_v08_data(self) -> None:
        profile_names = {
            HUMAN_WARRIOR_M01_HEAD_V08.hair_cap.name,
            *[part.name for part in HUMAN_WARRIOR_M01_HEAD_V08.hair_back_masses],
            *[part.name for part in HUMAN_WARRIOR_M01_HEAD_V08.hair_front_locks],
            *[part.name for part in HUMAN_WARRIOR_M01_HEAD_V08.hair_side_locks],
            *[
                item.part.name
                for item in HUMAN_WARRIOR_M01_HEAD_DETAIL_V08.hair_detail_masses
            ],
        }
        self.assertTrue(self.source_names.issubset(profile_names))

    def test_smooth_top_and_three_part_forelock_are_replaced_by_two_profile_meshes(self) -> None:
        self.assertTrue(
            {
                "hair_cap",
                "hair_back_crown_bridge",
                "hair_front_rotation_bridge",
                "hair_front_crown_mass",
                "hair_forelock_characteristic",
                "hair_forelock_root",
                "hair_forelock_tip",
            }.isdisjoint(self.source_names)
        )
        self.assertIn("_build_reference_profile_meshes(context)", self.builder_source)
        self.assertIn("_build_slice_profile_mesh(", self.builder_source)
        self.assertIn("load_hair_crown_profile_v08()", self.builder_source)
        self.assertIn("load_hair_forelock_profile_v08()", self.builder_source)
        self.assertIn("mesh.from_pydata(vertices, [], faces)", self.builder_source)
        self.assertIn('"top_crown"', self.builder_source)
        self.assertIn('"front_forelock"', self.builder_source)

    def test_profile_caps_are_triangulated_into_large_palette_facets(self) -> None:
        self.assertIn("REFERENCE_HAIR_FACET_COLORS", self.builder_source)
        self.assertIn("CROWN_FRONT_FACET_PATTERN", self.builder_source)
        self.assertIn("CROWN_BACK_FACET_PATTERN", self.builder_source)
        self.assertIn("FORELOCK_FRONT_FACET_PATTERN", self.builder_source)
        self.assertIn("front_center_index = len(vertices)", self.builder_source)
        self.assertIn("back_center_index = len(vertices)", self.builder_source)
        self.assertIn("polygon.material_index = material_index", self.builder_source)
        self.assertIn('material["material_slot_id"] = "hair"', self.builder_source)
        self.assertIn('obj["hair_facet_material_count"]', self.builder_source)

    def test_small_decorative_accents_remain_inactive(self) -> None:
        self.assertTrue(
            {
                "hair_temple_curl_left",
                "hair_temple_curl_right",
                "hair_back_texture_left",
                "hair_back_texture_right",
            }.isdisjoint(self.source_names)
        )

    def test_builder_changes_only_hair_and_keeps_positive_real_transforms(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn('obj.get(factory.MODULE_PROPERTY) != "hair"', self.builder_source)
        self.assertIn("consolidate_reference_hair_masses", self.builder_source)
        self.assertIn("material.use_backface_culling = False", self.builder_source)
        self.assertIn("HAIR_ROTATION_OVERRIDES_DEGREES", self.builder_source)
        self.assertIn("HAIR_SCALE_MULTIPLIERS", self.builder_source)
        self.assertIn("HAIR_WORLD_OFFSETS", self.builder_source)
        self.assertIn("world_matrix.translation += factory.Vector(offset)", self.builder_source)
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_records_actual_transforms_facets_profiles_and_inactive_sweep(self) -> None:
        adapter = self.tool_root / "blender_sprite_factory_head_v08.py"
        source = adapter.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIsInstance(tree, ast.Module)
        self.assertIn("consolidate_reference_hair_masses(context)", source)
        self.assertIn(
            '"approved_reference_single_crown_and_forelock_meshes_with_large_palette_facets"',
            source,
        )
        self.assertIn('"hair_crown_profile"', source)
        self.assertIn('"hair_forelock_profile"', source)
        self.assertIn('"inactive_after_occlusion_diagnostic"', source)
        self.assertIn('"hair_mass_builder"', source)
        self.assertIn("REFERENCE_HAIR_FACET_COLORS", source)
        self.assertIn('"facet_colors"', source)
        self.assertIn('"approved_reference_large_emission_facets"', source)
        self.assertIn("HAIR_ROTATION_OVERRIDES_DEGREES", source)
        self.assertIn('"actual_rotations_degrees"', source)
        self.assertIn('"positive_scale_multipliers"', source)
        self.assertIn('"world_offsets"', source)


if __name__ == "__main__":
    unittest.main()
