from __future__ import annotations

from dataclasses import dataclass

from head_profile import EllipsoidPart, HeadProfile
from head_profile_v04 import DetailedEllipsoidPart, MeshDensity
from head_profile_v07 import (
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V07,
    HUMAN_WARRIOR_M01_HEAD_V07,
)


@dataclass(frozen=True)
class HeadDetailProfileV08:
    character_id: str
    revision: str
    proxy_revision: str
    cranium_density: MeshDensity
    jaw_density: MeshDensity
    ear_density: MeshDensity
    hair_cap_density: MeshDensity
    hair_primary_density: MeshDensity
    hair_secondary_density: MeshDensity
    hair_tertiary_density: MeshDensity
    nose_vertices: int
    face_skin_masses: tuple
    hair_detail_masses: tuple[DetailedEllipsoidPart, ...]
    face_dark_details: tuple

    def assert_valid(self) -> None:
        if self.character_id != "human_warrior_m01":
            raise ValueError("Detailed head profile belongs to another character")
        if self.revision != "v08" or self.proxy_revision != "v11":
            raise ValueError("Detailed head profile must match head v08 / proxy v11")
        for density in (
            self.cranium_density,
            self.jaw_density,
            self.ear_density,
            self.hair_cap_density,
            self.hair_primary_density,
            self.hair_secondary_density,
            self.hair_tertiary_density,
        ):
            density.assert_valid()
        if not (
            self.hair_primary_density.segments
            > self.hair_secondary_density.segments
            > self.hair_tertiary_density.segments
        ):
            raise ValueError("Hair density tiers must descend from primary to tertiary")
        if self.nose_vertices < 8:
            raise ValueError("Detailed adult nose needs at least 8 vertices")

        detail_names = [item.part.name for item in self.hair_detail_masses]
        if len(detail_names) != len(set(detail_names)):
            raise ValueError("Detailed hair part names must be unique")
        required_detail_names = {
            "hair_forelock_root",
            "hair_forelock_tip",
            "hair_temple_curl_left",
            "hair_temple_curl_right",
            "hair_back_texture_left",
            "hair_back_texture_right",
        }
        if not required_detail_names.issubset(detail_names):
            raise ValueError("Reference hair needs forelock, temple and back texture accents")
        forbidden_fragment_names = {
            "hair_wave_top_left",
            "hair_wave_top_center",
            "hair_wave_top_right",
            "hair_sideburn_left",
            "hair_sideburn_right",
            "hair_back_crest_center",
            "hair_back_crest_left",
            "hair_back_crest_right",
        }
        if forbidden_fragment_names.intersection(detail_names):
            raise ValueError("Proxy v11 must not restore the fragmented proxy v10 hair bumps")


HUMAN_WARRIOR_M01_HEAD_V08 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v08",
    proxy_revision="v11",
    head_base=HUMAN_WARRIOR_M01_HEAD_V07.head_base,
    jaw=HUMAN_WARRIOR_M01_HEAD_V07.jaw,
    ears=HUMAN_WARRIOR_M01_HEAD_V07.ears,
    nose=HUMAN_WARRIOR_M01_HEAD_V07.nose,
    hair_cap=EllipsoidPart(
        "hair_cap",
        (0.0, 0.055, 4.665),
        (0.485, 0.385, 0.300),
    ),
    hair_back_masses=(
        EllipsoidPart(
            "hair_back_shell",
            (0.0, 0.180, 4.490),
            (0.405, 0.240, 0.310),
        ),
        EllipsoidPart(
            "hair_back_crown_bridge",
            (0.0, 0.075, 4.805),
            (0.335, 0.180, 0.205),
        ),
        EllipsoidPart(
            "hair_back_sweep_left",
            (0.235, 0.120, 4.485),
            (0.205, 0.175, 0.270),
        ),
        EllipsoidPart(
            "hair_back_sweep_right",
            (-0.235, 0.120, 4.485),
            (0.205, 0.175, 0.270),
        ),
        EllipsoidPart(
            "hair_nape_left",
            (0.165, 0.185, 4.205),
            (0.150, 0.145, 0.195),
        ),
        EllipsoidPart(
            "hair_nape_center",
            (0.0, 0.205, 4.165),
            (0.155, 0.145, 0.185),
        ),
        EllipsoidPart(
            "hair_nape_right",
            (-0.165, 0.185, 4.205),
            (0.150, 0.145, 0.195),
        ),
    ),
    hair_front_locks=(
        EllipsoidPart(
            "hair_front_crown_mass",
            (0.0, -0.180, 4.755),
            (0.370, 0.180, 0.205),
        ),
        EllipsoidPart(
            "hair_front_hairline_left",
            (0.180, -0.345, 4.505),
            (0.180, 0.110, 0.200),
        ),
        EllipsoidPart(
            "hair_forelock_characteristic",
            (-0.060, -0.405, 4.505),
            (0.100, 0.075, 0.190),
        ),
        EllipsoidPart(
            "hair_front_hairline_right",
            (-0.180, -0.345, 4.505),
            (0.180, 0.110, 0.200),
        ),
    ),
    hair_side_locks=(
        EllipsoidPart(
            "hair_side_mass_left",
            (0.400, -0.015, 4.395),
            (0.135, 0.180, 0.260),
        ),
        EllipsoidPart(
            "hair_side_mass_right",
            (-0.400, -0.015, 4.395),
            (0.135, 0.180, 0.260),
        ),
    ),
    brows=HUMAN_WARRIOR_M01_HEAD_V07.brows,
    eyes=HUMAN_WARRIOR_M01_HEAD_V07.eyes,
    mouth=HUMAN_WARRIOR_M01_HEAD_V07.mouth,
)


HUMAN_WARRIOR_M01_HEAD_DETAIL_V08 = HeadDetailProfileV08(
    character_id="human_warrior_m01",
    revision="v08",
    proxy_revision="v11",
    cranium_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.cranium_density,
    jaw_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.jaw_density,
    ear_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.ear_density,
    hair_cap_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.hair_cap_density,
    hair_primary_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.hair_primary_density,
    hair_secondary_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.hair_secondary_density,
    hair_tertiary_density=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.hair_tertiary_density,
    nose_vertices=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.nose_vertices,
    face_skin_masses=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.face_skin_masses,
    hair_detail_masses=(
        DetailedEllipsoidPart(
            EllipsoidPart(
                "hair_forelock_root",
                (-0.040, -0.335, 4.610),
                (0.090, 0.060, 0.105),
            ),
            "hair",
            MeshDensity(16, 10),
        ),
        DetailedEllipsoidPart(
            EllipsoidPart(
                "hair_forelock_tip",
                (-0.065, -0.455, 4.425),
                (0.055, 0.045, 0.085),
            ),
            "hair",
            MeshDensity(12, 8),
        ),
        DetailedEllipsoidPart(
            EllipsoidPart(
                "hair_temple_curl_left",
                (0.315, -0.175, 4.430),
                (0.080, 0.090, 0.130),
            ),
            "hair",
            MeshDensity(12, 8),
        ),
        DetailedEllipsoidPart(
            EllipsoidPart(
                "hair_temple_curl_right",
                (-0.315, -0.175, 4.430),
                (0.080, 0.090, 0.130),
            ),
            "hair",
            MeshDensity(12, 8),
        ),
        DetailedEllipsoidPart(
            EllipsoidPart(
                "hair_back_texture_left",
                (0.205, 0.285, 4.500),
                (0.085, 0.075, 0.125),
            ),
            "hair",
            MeshDensity(12, 8),
        ),
        DetailedEllipsoidPart(
            EllipsoidPart(
                "hair_back_texture_right",
                (-0.205, 0.285, 4.500),
                (0.085, 0.075, 0.125),
            ),
            "hair",
            MeshDensity(12, 8),
        ),
    ),
    face_dark_details=HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.face_dark_details,
)


def load_head_profile_v08(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V08.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V08.assert_valid()
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V08


def load_head_detail_profile_v08(character_id: str) -> HeadDetailProfileV08:
    if character_id != HUMAN_WARRIOR_M01_HEAD_DETAIL_V08.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_DETAIL_V08
