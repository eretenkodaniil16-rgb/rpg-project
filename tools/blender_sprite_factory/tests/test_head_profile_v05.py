from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile_v04 import HUMAN_WARRIOR_M01_HEAD_DETAIL_V04, HUMAN_WARRIOR_M01_HEAD_V04
from head_profile_v05 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V05,
    HUMAN_WARRIOR_M01_HEAD_V05,
    load_head_detail_profile_v05,
    load_head_profile_v05,
)


class DetailedHeadProfileV05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile_v05("human_warrior_m01")
        cls.detail = load_head_detail_profile_v05("human_warrior_m01")

    def test_revision_creates_proxy_v08_without_replacing_v04(self) -> None:
        self.assertEqual(self.profile.revision, "v05")
        self.assertEqual(self.profile.proxy_revision, "v08")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V04.revision, "v04")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V04.proxy_revision, "v07")
        HUMAN_WARRIOR_M01_HEAD_V05.assert_valid()
        HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.assert_valid()

    def test_cranium_size_and_position_remain_locked(self) -> None:
        self.assertEqual(self.profile.head_base.scale, HUMAN_WARRIOR_M01_HEAD_V04.head_base.scale)
        self.assertEqual(self.profile.head_base.location, HUMAN_WARRIOR_M01_HEAD_V04.head_base.location)

    def test_jaw_is_narrower_shorter_and_higher_than_v04(self) -> None:
        self.assertLess(self.profile.jaw.scale[0], HUMAN_WARRIOR_M01_HEAD_V04.jaw.scale[0])
        self.assertLess(self.profile.jaw.scale[2], HUMAN_WARRIOR_M01_HEAD_V04.jaw.scale[2])
        self.assertGreater(self.profile.jaw.location[2], HUMAN_WARRIOR_M01_HEAD_V04.jaw.location[2])

    def test_mesh_density_uses_three_selective_hair_tiers(self) -> None:
        self.assertEqual((self.detail.cranium_density.segments, self.detail.cranium_density.rings), (24, 14))
        self.assertEqual((self.detail.jaw_density.segments, self.detail.jaw_density.rings), (20, 12))
        self.assertEqual((self.detail.hair_cap_density.segments, self.detail.hair_cap_density.rings), (24, 14))
        self.assertEqual((self.detail.hair_primary_density.segments, self.detail.hair_primary_density.rings), (20, 12))
        self.assertEqual((self.detail.hair_secondary_density.segments, self.detail.hair_secondary_density.rings), (16, 10))
        self.assertEqual((self.detail.hair_tertiary_density.segments, self.detail.hair_tertiary_density.rings), (12, 8))
        self.assertEqual(self.detail.nose_vertices, 10)
        self.assertGreater(self.detail.cranium_density.segments, HUMAN_WARRIOR_M01_HEAD_DETAIL_V04.cranium_density.segments)

    def test_face_features_are_repositioned_for_separate_pixel_rows(self) -> None:
        brow_bottom = min(part.location[2] - part.dimensions[2] * 0.5 for part in self.profile.brows)
        eye_top = max(part.location[2] + part.dimensions[2] * 0.5 for part in self.profile.eyes)
        eye_bottom = min(part.location[2] - part.dimensions[2] * 0.5 for part in self.profile.eyes)
        mouth_top = self.profile.mouth.location[2] + self.profile.mouth.dimensions[2] * 0.5
        self.assertGreaterEqual(brow_bottom - eye_top, 0.18)
        self.assertGreaterEqual(eye_bottom - mouth_top, 0.18)
        self.assertGreater(abs(self.profile.eyes[0].location[0]), abs(HUMAN_WARRIOR_M01_HEAD_V04.eyes[0].location[0]))
        self.assertLess(self.profile.mouth.dimensions[0], HUMAN_WARRIOR_M01_HEAD_V04.mouth.dimensions[0])

    def test_face_is_tapered_by_separate_cheek_jaw_and_chin_masses(self) -> None:
        skin_names = {item.part.name for item in self.detail.face_skin_masses}
        self.assertTrue(
            {
                "face_cheekbone_left",
                "face_cheekbone_right",
                "face_jaw_plane_left",
                "face_jaw_plane_right",
                "face_philtrum",
                "face_chin",
            }.issubset(skin_names)
        )
        cheek_left = next(item.part for item in self.detail.face_skin_masses if item.part.name == "face_cheekbone_left")
        self.assertLess(cheek_left.scale[0], 0.15)

    def test_back_crown_and_nape_restore_rear_height(self) -> None:
        profile_back_top = max(part.location[2] + part.scale[2] for part in self.profile.hair_back_masses)
        previous_back_top = max(part.location[2] + part.scale[2] for part in HUMAN_WARRIOR_M01_HEAD_V04.hair_back_masses)
        detail_back_top = max(
            item.part.location[2] + item.part.scale[2]
            for item in self.detail.hair_detail_masses
            if "back_crest" in item.part.name
        )
        self.assertGreater(profile_back_top, previous_back_top)
        self.assertGreater(detail_back_top, profile_back_top)
        detail_names = {item.part.name for item in self.detail.hair_detail_masses}
        self.assertIn("hair_nape_tip_center", detail_names)
        self.assertIn("hair_forelock_root", detail_names)
        self.assertIn("hair_forelock_tip", detail_names)

    def test_active_adapter_records_v05_profile_and_all_density_tiers(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        adapter = tool_root / "blender_sprite_factory_head_v05.py"
        source = adapter.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("factory.load_head_profile = load_head_profile_v05", source)
        self.assertIn("factory._build_head_and_hair = _build_head_and_hair_v05", source)
        self.assertIn('"hair_primary_segments"', source)
        self.assertIn('"hair_secondary_segments"', source)
        self.assertIn('"hair_tertiary_segments"', source)
        self.assertNotIn("scale.x = -1", source)
        self.assertNotIn("scale[0] = -1", source)

    def test_launchers_and_ci_activate_proxy_v08_adapter(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        launcher = (tool_root / "run_blender_sprite_pilot.ps1").read_text(encoding="ascii")
        workflow = (tool_root.parents[1] / ".github" / "workflows" / "validate-blender-sprite-factory.yml").read_text(encoding="utf-8")
        self.assertIn("blender_sprite_factory_head_v05.py", launcher)
        self.assertIn("render-proxy-v08", workflow)
        self.assertIn("blender_sprite_factory_head_v05.py", workflow)
        self.assertIn("human_warrior_m01_proxy_v08_", workflow)

    def test_unknown_character_cannot_use_v05_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No detailed head profile"):
            load_head_profile_v05("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
