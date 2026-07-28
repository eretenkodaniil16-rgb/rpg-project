from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile_v05 import HUMAN_WARRIOR_M01_HEAD_DETAIL_V05, HUMAN_WARRIOR_M01_HEAD_V05
from head_profile_v06 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V06,
    HUMAN_WARRIOR_M01_HEAD_V06,
    load_head_detail_profile_v06,
    load_head_profile_v06,
)


class DetailedHeadProfileV06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile_v06("human_warrior_m01")
        cls.detail = load_head_detail_profile_v06("human_warrior_m01")

    def test_revision_creates_proxy_v09_without_replacing_v05(self) -> None:
        self.assertEqual(self.profile.revision, "v06")
        self.assertEqual(self.profile.proxy_revision, "v09")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V05.revision, "v05")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V05.proxy_revision, "v08")
        self.profile.assert_valid()
        self.detail.assert_valid()

    def test_cranium_jaw_and_density_contract_remain_locked(self) -> None:
        self.assertEqual(self.profile.head_base, HUMAN_WARRIOR_M01_HEAD_V05.head_base)
        self.assertEqual(self.profile.jaw, HUMAN_WARRIOR_M01_HEAD_V05.jaw)
        self.assertEqual(self.detail.cranium_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.cranium_density)
        self.assertEqual(self.detail.hair_primary_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.hair_primary_density)
        self.assertEqual(self.detail.hair_secondary_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.hair_secondary_density)
        self.assertEqual(self.detail.hair_tertiary_density, HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.hair_tertiary_density)

    def test_rear_crown_moves_toward_rotation_axis_instead_of_scaling_body(self) -> None:
        current = next(part for part in self.profile.hair_back_masses if part.name == "hair_crown_back_center")
        previous = next(part for part in HUMAN_WARRIOR_M01_HEAD_V05.hair_back_masses if part.name == "hair_crown_back_center")
        self.assertLess(abs(current.location[1]), abs(previous.location[1]))
        self.assertGreaterEqual(current.location[2] + current.scale[2], previous.location[2] + previous.scale[2] - 0.02)
        crest = next(item.part for item in self.detail.hair_detail_masses if item.part.name == "hair_back_crest_center")
        previous_crest = next(item.part for item in HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.hair_detail_masses if item.part.name == "hair_back_crest_center")
        self.assertLess(abs(crest.location[1]), abs(previous_crest.location[1]))

    def test_hairline_frames_face_without_covering_eye_line(self) -> None:
        names = {item.part.name for item in self.detail.hair_detail_masses}
        self.assertTrue({"hair_hairline_left", "hair_hairline_center", "hair_hairline_right"}.issubset(names))
        eye_top = max(part.location[2] + part.dimensions[2] * 0.5 for part in self.profile.eyes)
        for item in self.detail.hair_detail_masses:
            if item.part.name.startswith("hair_hairline_"):
                self.assertGreaterEqual(item.part.location[2] - item.part.scale[2], eye_top)

    def test_face_skin_masses_are_recessed_and_smaller_than_v05(self) -> None:
        current = {item.part.name: item.part for item in self.detail.face_skin_masses}
        previous = {item.part.name: item.part for item in HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.face_skin_masses}
        for name in ("face_cheekbone_left", "face_cheekbone_right", "face_chin"):
            self.assertLess(current[name].scale[0], previous[name].scale[0])
            self.assertGreater(current[name].location[1], previous[name].location[1])

    def test_top_waves_are_embedded_instead_of_forming_isolated_peaks(self) -> None:
        current = {item.part.name: item.part for item in self.detail.hair_detail_masses}
        previous = {item.part.name: item.part for item in HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.hair_detail_masses}
        for name in ("hair_wave_top_left", "hair_wave_top_center", "hair_wave_top_right"):
            self.assertLess(current[name].location[2], previous[name].location[2])
        cap_top = self.profile.hair_cap.location[2] + self.profile.hair_cap.scale[2]
        self.assertLessEqual(current["hair_wave_top_center"].location[2] + current["hair_wave_top_center"].scale[2], cap_top + 0.01)

    def test_adapter_and_launchers_activate_proxy_v09(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        adapter = tool_root / "blender_sprite_factory_head_v06.py"
        source = adapter.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("factory.load_head_profile = load_head_profile_v06", source)
        launcher = (tool_root / "run_blender_sprite_pilot.ps1").read_text(encoding="ascii")
        workflow = (tool_root.parents[1] / ".github" / "workflows" / "validate-blender-sprite-factory.yml").read_text(encoding="utf-8")
        self.assertIn("blender_sprite_factory_head_v06.py", launcher)
        self.assertIn("render-proxy-v09", workflow)
        self.assertIn("human_warrior_m01_proxy_v09_", workflow)

    def test_unknown_character_cannot_use_v06_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No detailed head profile"):
            load_head_profile_v06("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
