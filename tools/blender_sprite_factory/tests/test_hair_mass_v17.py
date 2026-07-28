from __future__ import annotations

import ast
import unittest
from pathlib import Path


class HairMassBuilderV17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.builder_source = (cls.tool_root / "hair_mass_builder_v17.py").read_text(
            encoding="utf-8"
        )
        cls.adapter_source = (
            cls.tool_root / "blender_sprite_factory_head_v17.py"
        ).read_text(encoding="utf-8")

    def test_builder_and_adapter_parse(self) -> None:
        ast.parse(self.builder_source)
        ast.parse(self.adapter_source)

    def test_builder_extends_integrated_proxy_without_reintroducing_overlays(self) -> None:
        self.assertIn(
            "previous_builder.apply_integrated_crown_back_pass(context)",
            self.builder_source,
        )
        self.assertIn("REMOVED_BACK_OVERLAY_NAMES.intersection", self.builder_source)
        self.assertNotIn("hair_back_shell\" =", self.builder_source)
        self.assertNotIn("scale.x = -1", self.builder_source)
        self.assertNotIn("scale[0] = -1", self.builder_source)

    def test_geometry_uses_smooth_controls_and_expected_topology(self) -> None:
        self.assertIn('"vertices": 226', self.builder_source)
        self.assertIn('"faces": 256', self.builder_source)
        self.assertIn('"slices": 7', self.builder_source)
        self.assertIn('"control_points_per_slice": 16', self.builder_source)
        self.assertIn('"sampled_points_per_slice": 32', self.builder_source)
        self.assertIn("seven_gradual_slices_with_chaikin", self.builder_source)

    def test_tones_use_spatial_diagonal_regions_not_depth_bands(self) -> None:
        self.assertIn("_organic_material_index", self.builder_source)
        self.assertIn("diagonal_field", self.builder_source)
        self.assertIn("large_organic_diagonal_regions_without_depth_bands", self.builder_source)
        self.assertNotIn("def _panel_material_index(depth_segment", self.builder_source)

    def test_adapter_locks_unrelated_character_systems(self) -> None:
        self.assertIn("previous_adapter._build_head_and_hair_v16(context)", self.adapter_source)
        self.assertIn("apply_organic_crown_back_pass(context)", self.adapter_source)
        self.assertIn("factory.load_head_profile = load_head_profile_v17", self.adapter_source)
        self.assertIn('"forced_angularity": False', self.adapter_source)
        self.assertIn('"forelock_changed": False', self.adapter_source)
        self.assertIn('"palette_changed": False', self.adapter_source)
        self.assertIn('"animation_keys_changed": False', self.adapter_source)


if __name__ == "__main__":
    unittest.main()
