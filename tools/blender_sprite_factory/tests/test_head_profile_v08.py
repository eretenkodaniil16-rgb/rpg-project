from __future__ import annotations

import ast
import unittest
from pathlib import Path

from head_profile_v07 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V07,
    HUMAN_WARRIOR_M01_HEAD_V07,
)
from head_profile_v08 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V08,
    HUMAN_WARRIOR_M01_HEAD_V08,
    load_head_detail_profile_v08,
    load_head_profile_v08,
)


class ReferenceHairProfileV08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile_v08("human_warrior_m01")
        cls.detail = load_head_detail_profile_v08("human_warrior_m01")

    def test_revision_creates_proxy_v11_without_replacing_v07(self) -> None:
        self.assertEqual(self.profile.revision, "v08")
        self.assertEqual(self.profile.proxy_revision, "v11")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V07.revision, "v07")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V07.proxy_revision, "v10")
        self.profile.assert_valid()
        self.detail.assert_valid()

    def test_head_face_and_density_contract_are_locked_to_v07(self) -> None:
        for field_name in (
            "head_base",
            "jaw",
            "ears",
            "nose",
            "brows",
            "eyes",
            "mouth",
        ):
            self.assertEqual(
                getattr(self.profile, field_name),
                getattr(HUMAN_WARRIOR_M01_HEAD_V07, field_name),
            )
        self.assertEqual(
            self.detail.face_skin_masses,
            HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.face_skin_masses,
        )
        self.assertEqual(
            self.detail.face_dark_details,
            HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.face_dark_details,
        )
        for density_name in (
            "cranium_density",
            "jaw_density",
            "ear_density",
            "hair_cap_density",
            "hair_primary_density",
            "hair_secondary_density",
            "hair_tertiary_density",
        ):
            self.assertEqual(
                getattr(self.detail, density_name),
                getattr(HUMAN_WARRIOR_M01_HEAD_DETAIL_V07, density_name),
            )

    def test_hair_is_consolidated_into_five_reference_zones(self) -> None:
        profile_names = {
            part.name
            for part in (
                self.profile.hair_back_masses
                + self.profile.hair_front_locks
                + self.profile.hair_side_locks
            )
        }
        self.assertTrue(
            {
                "hair_front_rotation_bridge",
                "hair_front_crown_mass",
                "hair_front_hairline_left",
                "hair_front_hairline_right",
                "hair_forelock_characteristic",
                "hair_side_mass_left",
                "hair_side_mass_right",
                "hair_back_shell",
                "hair_back_crown_bridge",
                "hair_nape_center",
            }.issubset(profile_names)
        )
        detail_names = {item.part.name for item in self.detail.hair_detail_masses}
        self.assertTrue(
            {
                "hair_forelock_root",
                "hair_forelock_tip",
                "hair_temple_curl_left",
                "hair_temple_curl_right",
                "hair_back_texture_left",
                "hair_back_texture_right",
            }.issubset(detail_names)
        )

    def test_proxy_v10_bumps_and_sideburns_are_not_carried_forward(self) -> None:
        all_names = {
            self.profile.hair_cap.name,
            *[part.name for part in self.profile.hair_back_masses],
            *[part.name for part in self.profile.hair_front_locks],
            *[part.name for part in self.profile.hair_side_locks],
            *[item.part.name for item in self.detail.hair_detail_masses],
        }
        self.assertTrue(
            {
                "hair_wave_top_left",
                "hair_wave_top_center",
                "hair_wave_top_right",
                "hair_sideburn_left",
                "hair_sideburn_right",
                "hair_back_crest_center",
                "hair_back_crest_left",
                "hair_back_crest_right",
            }.isdisjoint(all_names)
        )

    def test_hair_part_count_is_reduced_without_shrinking_the_head(self) -> None:
        previous_count = (
            1
            + len(HUMAN_WARRIOR_M01_HEAD_V07.hair_back_masses)
            + len(HUMAN_WARRIOR_M01_HEAD_V07.hair_front_locks)
            + len(HUMAN_WARRIOR_M01_HEAD_V07.hair_side_locks)
            + len(HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.hair_detail_masses)
        )
        current_count = (
            1
            + len(self.profile.hair_back_masses)
            + len(self.profile.hair_front_locks)
            + len(self.profile.hair_side_locks)
            + len(self.detail.hair_detail_masses)
        )
        self.assertLess(current_count, previous_count)
        self.assertGreaterEqual(current_count, 16)
        self.assertLessEqual(current_count, 24)
        self.assertEqual(self.profile.head_base, HUMAN_WARRIOR_M01_HEAD_V07.head_base)

    def test_side_hair_is_shorter_and_front_bridge_preserves_up_height(self) -> None:
        current_side_bottom = min(
            part.location[2] - part.scale[2] for part in self.profile.hair_side_locks
        )
        previous_side_bottom = min(
            part.location[2] - part.scale[2]
            for part in HUMAN_WARRIOR_M01_HEAD_V07.hair_side_locks
        )
        self.assertGreater(current_side_bottom, previous_side_bottom)
        rotation_bridge = next(
            part
            for part in self.profile.hair_front_locks
            if part.name == "hair_front_rotation_bridge"
        )
        self.assertLess(rotation_bridge.location[1], -0.30)
        self.assertGreaterEqual(rotation_bridge.location[2] + rotation_bridge.scale[2], 5.06)
        forelock = next(
            part
            for part in self.profile.hair_front_locks
            if part.name == "hair_forelock_characteristic"
        )
        self.assertLess(forelock.location[0], 0.0)
        self.assertGreater(forelock.scale[2], 0.20)

    def test_reference_hair_uses_real_asymmetric_rotations_without_mirroring(self) -> None:
        rotations = dict(self.detail.hair_rotations_degrees)
        self.assertEqual(rotations["hair_cap"][0], 18.0)
        self.assertGreater(rotations["hair_front_rotation_bridge"][0], 20.0)
        self.assertGreater(rotations["hair_forelock_characteristic"][1], 0.0)
        self.assertNotEqual(
            rotations["hair_back_sweep_left"][2],
            -rotations["hair_back_sweep_right"][2],
        )

    def test_historical_v08_adapter_remains_reproducible_while_launchers_advance(self) -> None:
        tool_root = Path(__file__).resolve().parents[1]
        adapter = tool_root / "blender_sprite_factory_head_v08.py"
        source = adapter.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("factory.load_head_profile = load_head_profile_v08", source)
        self.assertIn("factory._build_head_and_hair = _build_head_and_hair_v08", source)
        self.assertIn('"approved_reference_consolidated_five_zone"', source)
        self.assertIn("_apply_reference_hair_palette(context)", source)
        self.assertIn("_apply_reference_hair_rotations(context)", source)
        self.assertIn('"approved_reference_constant_color_ramp"', source)
        self.assertNotIn("scale.x = -1", source)
        self.assertNotIn("scale[0] = -1", source)
        launcher = (tool_root / "run_blender_sprite_pilot.ps1").read_text(
            encoding="ascii"
        )
        workflow = (
            tool_root.parents[1]
            / ".github"
            / "workflows"
            / "validate-blender-sprite-factory.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("blender_sprite_factory_head_v15.py", launcher)
        self.assertIn("render-proxy-v18", workflow)
        self.assertIn("blender_sprite_factory_head_v15.py", workflow)
        self.assertIn("human_warrior_m01_proxy_v18_", workflow)

    def test_unknown_character_cannot_use_v08_identity(self) -> None:
        with self.assertRaisesRegex(KeyError, "No detailed head profile"):
            load_head_profile_v08("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
