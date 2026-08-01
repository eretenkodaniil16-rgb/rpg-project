from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile import HUMAN_WARRIOR_M01_HEAD_V03
from head_profile_v04 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V04,
    HUMAN_WARRIOR_M01_HEAD_V04,
    load_head_detail_profile_v04,
    load_head_profile_v04,
)


class DetailedHeadProfileV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile_v04("human_warrior_m01")
        cls.detail = load_head_detail_profile_v04("human_warrior_m01")

    def test_revision_creates_proxy_v07_without_replacing_v03(self) -> None:
        self.assertEqual(self.profile.revision, "v04")
        self.assertEqual(self.profile.proxy_revision, "v07")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V03.revision, "v03")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V03.proxy_revision, "v06")
        HUMAN_WARRIOR_M01_HEAD_V04.assert_valid()
        HUMAN_WARRIOR_M01_HEAD_DETAIL_V04.assert_valid()

    def test_cranium_scale_and_location_remain_locked(self) -> None:
        self.assertEqual(
            self.profile.head_base.scale,
            HUMAN_WARRIOR_M01_HEAD_V03.head_base.scale,
        )
        self.assertEqual(
            self.profile.head_base.location,
            HUMAN_WARRIOR_M01_HEAD_V03.head_base.location,
        )

    def test_mesh_density_is_increased_only_for_head_production(self) -> None:
        self.assertGreaterEqual(self.detail.cranium_density.segments, 20)
        self.assertGreaterEqual(self.detail.cranium_density.rings, 12)
        self.assertGreaterEqual(self.detail.jaw_density.segments, 18)
        self.assertGreaterEqual(self.detail.hair_cap_density.segments, 20)
        self.assertGreaterEqual(self.detail.nose_vertices, 8)

    def test_face_is_split_into_anatomical_masses_and_dark_details(self) -> None:
        skin_names = {item.part.name for item in self.detail.face_skin_masses}
        dark_names = {item.part.name for item in self.detail.face_dark_details}
        self.assertTrue(
            {
                "face_brow_ridge_left",
                "face_brow_ridge_right",
                "face_nose_bridge",
                "face_cheek_left",
                "face_cheek_right",
                "face_chin",
                "face_lower_lip_plane",
            }.issubset(skin_names)
        )
        self.assertTrue(
            {
                "face_upper_lid_left",
                "face_upper_lid_right",
                "face_mouth_corner_left",
                "face_mouth_corner_right",
                "face_lower_lip_shadow",
            }.issubset(dark_names)
        )

    def test_hair_uses_separate_crown_forelock_temples_back_and_nape_parts(self) -> None:
        profile_names = {
            part.name
            for part in (
                self.profile.hair_back_masses
                + self.profile.hair_front_locks
                + self.profile.hair_side_locks
            )
        }
        detail_names = {item.part.name for item in self.detail.hair_detail_masses}
        self.assertIn("hair_forelock_characteristic", profile_names)
        self.assertIn("hair_nape_center", profile_names)
        self.assertIn("hair_wave_top_center", detail_names)
        self.assertIn("hair_forelock_tip", detail_names)
        self.assertIn("hair_temple_curl_left", detail_names)
        self.assertIn("hair_temple_curl_right", detail_names)
        self.assertIn("hair_back_ripple_left", detail_names)
        self.assertIn("hair_back_ripple_right", detail_names)
        self.assertIn("hair_nape_tip_left", detail_names)
        self.assertIn("hair_nape_tip_right", detail_names)

    def test_active_adapter_records_profile_hashes_and_geometry_counts(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        adapter = tool_root / "blender_sprite_factory_head_v04.py"
        source = adapter.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('factory.load_head_profile = load_head_profile_v04', source)
        self.assertIn('factory._build_head_and_hair = _build_head_and_hair_v04', source)
        self.assertIn('"head_geometry"', source)
        self.assertIn('"head_builder_adapter"', source)
        self.assertNotIn("scale.x = -1", source)
        self.assertNotIn("scale[0] = -1", source)

    def test_unknown_character_cannot_use_detailed_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No detailed head profile"):
            load_head_profile_v04("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
