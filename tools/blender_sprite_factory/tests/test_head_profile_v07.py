from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile_v06 import HUMAN_WARRIOR_M01_HEAD_DETAIL_V06, HUMAN_WARRIOR_M01_HEAD_V06
from head_profile_v07 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V07,
    HUMAN_WARRIOR_M01_HEAD_V07,
    load_head_detail_profile_v07,
    load_head_profile_v07,
)


class DetailedHeadProfileV07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile_v07("human_warrior_m01")
        cls.detail = load_head_detail_profile_v07("human_warrior_m01")

    def test_revision_creates_proxy_v10_without_replacing_v06(self) -> None:
        self.assertEqual(self.profile.revision, "v07")
        self.assertEqual(self.profile.proxy_revision, "v10")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V06.revision, "v06")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V06.proxy_revision, "v09")
        self.profile.assert_valid()
        self.detail.assert_valid()

    def test_cranium_jaw_and_selective_density_remain_locked(self) -> None:
        self.assertEqual(self.profile.head_base, HUMAN_WARRIOR_M01_HEAD_V06.head_base)
        self.assertEqual(self.profile.jaw, HUMAN_WARRIOR_M01_HEAD_V06.jaw)
        self.assertEqual(self.detail.cranium_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.cranium_density)
        self.assertEqual(self.detail.hair_primary_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.hair_primary_density)
        self.assertEqual(self.detail.hair_secondary_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.hair_secondary_density)
        self.assertEqual(self.detail.hair_tertiary_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.hair_tertiary_density)

    def test_front_crown_bridge_restores_rotated_height_without_rescaling_head(self) -> None:
        bridge = next(item.part for item in self.detail.hair_detail_masses if item.part.name == "hair_front_crown_bridge")
        previous_front_top = max(part.location[2] + part.scale[2] for part in HUMAN_WARRIOR_M01_HEAD_V06.hair_front_locks)
        self.assertLess(bridge.location[1], -0.30)
        self.assertGreater(bridge.location[2] + bridge.scale[2], previous_front_top + 0.10)
        self.assertLessEqual(bridge.scale[0], 0.28)

    def test_lower_hairline_and_sideburns_narrow_exposed_face(self) -> None:
        details = {item.part.name: item.part for item in self.detail.hair_detail_masses}
        eye_top = max(part.location[2] + part.dimensions[2] * 0.5 for part in self.profile.eyes)
        for name in ("hair_hairline_left", "hair_hairline_center", "hair_hairline_right"):
            self.assertGreaterEqual(details[name].location[2] - details[name].scale[2], eye_top)
        self.assertIn("hair_sideburn_left", details)
        self.assertIn("hair_sideburn_right", details)
        self.assertGreater(details["hair_sideburn_left"].location[0], 0.0)
        self.assertLess(details["hair_sideburn_right"].location[0], 0.0)

    def test_face_skin_masses_are_smaller_than_v06(self) -> None:
        current = {item.part.name: item.part for item in self.detail.face_skin_masses}
        previous = {item.part.name: item.part for item in HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.face_skin_masses}
        for name in ("face_cheekbone_left", "face_cheekbone_right", "face_chin"):
            self.assertLess(current[name].scale[0], previous[name].scale[0])

    def test_historical_adapter_remains_reproducible(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        adapter = tool_root / "blender_sprite_factory_head_v07.py"
        source = adapter.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("factory.load_head_profile = load_head_profile_v07", source)
        self.assertIn("factory._build_head_and_hair = _build_head_and_hair_v07", source)
        self.assertNotIn("scale.x = -1", source)
        self.assertNotIn("scale[0] = -1", source)

    def test_unknown_character_cannot_use_v07_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No detailed head profile"):
            load_head_profile_v07("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
