from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile_v08 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V08,
    HUMAN_WARRIOR_M01_HEAD_V08,
)


EXPECTED_ACTIVE_HAIR_NAMES = {
    "hair_cap",
    "hair_back_shell",
    "hair_front_rotation_bridge",
    "hair_front_crown_mass",
    "hair_front_hairline_left",
    "hair_front_hairline_right",
    "hair_forelock_characteristic",
    "hair_side_mass_left",
    "hair_side_mass_right",
    "hair_nape_left",
    "hair_nape_center",
    "hair_nape_right",
    "hair_forelock_root",
    "hair_forelock_tip",
}


def _active_names_from_builder(source: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "ACTIVE_HAIR_PART_NAMES"
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
    raise AssertionError("ACTIVE_HAIR_PART_NAMES was not found")


class HairMassBuilderV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_path = cls.tool_root / "hair_mass_builder_v08.py"
        cls.builder_source = cls.builder_path.read_text(encoding="utf-8")
        cls.active_names = _active_names_from_builder(cls.builder_source)

    def test_active_set_matches_consolidated_reference_contract(self) -> None:
        self.assertEqual(self.active_names, EXPECTED_ACTIVE_HAIR_NAMES)
        self.assertEqual(len(self.active_names), 14)

    def test_every_active_name_exists_in_head_v08_data(self) -> None:
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
        self.assertTrue(self.active_names.issubset(profile_names))

    def test_fragmented_or_decorative_parts_are_inactive(self) -> None:
        self.assertTrue(
            {
                "hair_back_crown_bridge",
                "hair_back_sweep_left",
                "hair_back_sweep_right",
                "hair_temple_curl_left",
                "hair_temple_curl_right",
                "hair_back_texture_left",
                "hair_back_texture_right",
            }.isdisjoint(self.active_names)
        )

    def test_builder_changes_only_hair_and_keeps_real_rotations(self) -> None:
        ast.parse(self.builder_source)
        self.assertIn('obj.get(factory.MODULE_PROPERTY) != "hair"', self.builder_source)
        self.assertIn("consolidate_reference_hair_masses", self.builder_source)
        self.assertIn("material.use_backface_culling = False", self.builder_source)
        self.assertIn("obj.rotation_euler", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_adapter_activates_mass_builder_and_records_failed_sweep(self) -> None:
        adapter = self.tool_root / "blender_sprite_factory_head_v08.py"
        source = adapter.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIsInstance(tree, ast.Module)
        self.assertIn("consolidate_reference_hair_masses(context)", source)
        self.assertIn('"approved_reference_consolidated_five_zone_masses"', source)
        self.assertIn('"inactive_after_occlusion_diagnostic"', source)
        self.assertIn('"hair_mass_builder"', source)


if __name__ == "__main__":
    unittest.main()
