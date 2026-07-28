from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v16.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v16.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_extends_proxy_v18_and_replaces_only_crown_data(self) -> None:
        self.assertIn(
            "previous_builder.apply_major_lock_exposure_pass(context)",
            self.builder_source,
        )
        self.assertIn("mesh.from_pydata(vertices, [], faces)", self.builder_source)
        self.assertIn("crown.data = mesh", self.builder_source)
        self.assertIn('"vertices": 82', self.builder_source)
        self.assertIn('"faces": 96', self.builder_source)

    def test_redundant_back_overlays_are_removed_without_mirroring(self) -> None:
        self.assertIn("_remove_redundant_back_overlays", self.builder_source)
        self.assertIn("factory.bpy.data.objects.remove(obj, do_unlink=True)", self.builder_source)
        self.assertIn("REMOVED_BACK_OVERLAY_NAMES.intersection(actual_names)", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_side_and_nape_profile_locks_keep_established_topology(self) -> None:
        self.assertIn("RETAINED_PROFILE_LOCK_NAMES", self.builder_source)
        self.assertIn("len(obj.data.vertices) != 38", self.builder_source)
        self.assertIn("len(obj.data.polygons) != 42", self.builder_source)
        self.assertIn("if any(value <= 0.0 for value in obj.scale)", self.builder_source)

    def test_adapter_locks_unrelated_character_systems(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v15(context)", self.adapter_source)
        self.assertIn("apply_integrated_crown_back_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v16", self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"palette_changed": False', self.adapter_source)
        self.assertIn('"separator_geometry_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)
        self.assertIn('"net_hair_part_change": -len(REMOVED_BACK_OVERLAY_NAMES)', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
