from __future__ import annotations

from dataclasses import dataclass

from head_profile import BoxPart, EllipsoidPart, HeadProfile, NosePart
from head_profile_v04 import (
    DetailedBoxPart,
    DetailedEllipsoidPart,
    HUMAN_WARRIOR_M01_HEAD_V04,
    MeshDensity,
)


@dataclass(frozen=True)
class HeadDetailProfileV05:
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
    face_skin_masses: tuple[DetailedEllipsoidPart, ...]
    hair_detail_masses: tuple[DetailedEllipsoidPart, ...]
    face_dark_details: tuple[DetailedBoxPart, ...]

    def assert_valid(self) -> None:
        if self.character_id != "human_warrior_m01":
            raise ValueError("Detailed head profile belongs to another character")
        if self.revision != "v05" or self.proxy_revision != "v08":
            raise ValueError("Detailed head profile must match head v05 / proxy v08")
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
        if len(self.face_skin_masses) < 9:
            raise ValueError("Face needs separate brow, cheek, jaw, philtrum and chin masses")
        if len(self.hair_detail_masses) < 14:
            raise ValueError("Medium wavy hair needs connected crown, temple, back and nape details")
        if len(self.face_dark_details) < 7:
            raise ValueError("Eyes, nostrils and mouth need separate dark details")

        names = [
            item.part.name
            for item in (
                self.face_skin_masses
                + self.hair_detail_masses
                + self.face_dark_details
            )
        ]
        if len(names) != len(set(names)):
            raise ValueError("Detailed head part names must be unique")
        for item in self.face_skin_masses + self.hair_detail_masses:
            if min(item.part.scale) <= 0.0:
                raise ValueError(f"Invalid ellipsoid scale: {item.part.name}")
        for item in self.face_dark_details:
            if min(item.part.dimensions) <= 0.0:
                raise ValueError(f"Invalid box dimensions: {item.part.name}")


HUMAN_WARRIOR_M01_HEAD_V05 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v05",
    proxy_revision="v08",
    head_base=EllipsoidPart(
        "head_base",
        HUMAN_WARRIOR_M01_HEAD_V04.head_base.location,
        HUMAN_WARRIOR_M01_HEAD_V04.head_base.scale,
    ),
    jaw=EllipsoidPart(
        "head_jaw",
        (0.0, -0.185, 4.075),
        (0.345, 0.272, 0.305),
    ),
    ears=(
        EllipsoidPart("head_ear_left", (0.420, -0.020, 4.275), (0.074, 0.064, 0.116)),
        EllipsoidPart("head_ear_right", (-0.420, -0.020, 4.275), (0.074, 0.064, 0.116)),
    ),
    nose=NosePart(
        location=(0.0, -0.485, 4.175),
        radius_bottom=0.038,
        radius_top=0.014,
        depth=0.125,
    ),
    hair_cap=EllipsoidPart("hair_cap", (0.0, 0.095, 4.675), (0.455, 0.350, 0.285)),
    hair_back_masses=(
        EllipsoidPart("hair_back_shell", (0.0, 0.235, 4.505), (0.345, 0.225, 0.300)),
        EllipsoidPart("hair_crown_back_center", (0.0, 0.155, 4.865), (0.175, 0.165, 0.215)),
        EllipsoidPart("hair_crown_back_left", (0.185, 0.145, 4.825), (0.155, 0.145, 0.195)),
        EllipsoidPart("hair_crown_back_right", (-0.185, 0.145, 4.825), (0.155, 0.145, 0.195)),
        EllipsoidPart("hair_back_wave_left", (0.285, 0.215, 4.440), (0.145, 0.165, 0.300)),
        EllipsoidPart("hair_back_wave_right", (-0.285, 0.215, 4.440), (0.145, 0.165, 0.300)),
        EllipsoidPart("hair_nape_left", (0.185, 0.230, 4.185), (0.120, 0.145, 0.225)),
        EllipsoidPart("hair_nape_center", (0.0, 0.255, 4.135), (0.125, 0.135, 0.215)),
        EllipsoidPart("hair_nape_right", (-0.185, 0.230, 4.185), (0.120, 0.145, 0.225)),
    ),
    hair_front_locks=(
        EllipsoidPart("hair_crown_front_left", (0.170, -0.185, 4.755), (0.155, 0.135, 0.165)),
        EllipsoidPart("hair_crown_front_center", (0.0, -0.220, 4.790), (0.165, 0.145, 0.175)),
        EllipsoidPart("hair_crown_front_right", (-0.170, -0.185, 4.755), (0.155, 0.135, 0.165)),
        EllipsoidPart("hair_temple_front_left", (0.235, -0.285, 4.515), (0.125, 0.105, 0.170)),
        EllipsoidPart("hair_forelock_characteristic", (-0.040, -0.340, 4.565), (0.115, 0.090, 0.175)),
        EllipsoidPart("hair_temple_front_right", (-0.235, -0.285, 4.515), (0.125, 0.105, 0.170)),
    ),
    hair_side_locks=(
        EllipsoidPart("hair_lock_side_left", (0.400, 0.015, 4.345), (0.110, 0.145, 0.330)),
        EllipsoidPart("hair_lock_side_right", (-0.400, 0.015, 4.345), (0.110, 0.145, 0.330)),
    ),
    brows=(
        BoxPart("face_brow_left", (0.145, -0.520, 4.375), (0.105, 0.027, 0.023), rotation_y_degrees=-6.5),
        BoxPart("face_brow_right", (-0.145, -0.520, 4.375), (0.105, 0.027, 0.023), rotation_y_degrees=6.5),
    ),
    eyes=(
        BoxPart("face_eye_left", (0.145, -0.542, 4.170), (0.043, 0.020, 0.021)),
        BoxPart("face_eye_right", (-0.145, -0.542, 4.170), (0.043, 0.020, 0.021)),
    ),
    mouth=BoxPart("face_mouth", (0.0, -0.510, 3.965), (0.068, 0.020, 0.021)),
)


HUMAN_WARRIOR_M01_HEAD_DETAIL_V05 = HeadDetailProfileV05(
    character_id="human_warrior_m01",
    revision="v05",
    proxy_revision="v08",
    cranium_density=MeshDensity(24, 14),
    jaw_density=MeshDensity(20, 12),
    ear_density=MeshDensity(14, 9),
    hair_cap_density=MeshDensity(24, 14),
    hair_primary_density=MeshDensity(20, 12),
    hair_secondary_density=MeshDensity(16, 10),
    hair_tertiary_density=MeshDensity(12, 8),
    nose_vertices=10,
    face_skin_masses=(
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_left", (0.155, -0.410, 4.395), (0.155, 0.060, 0.060)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_right", (-0.155, -0.410, 4.395), (0.155, 0.060, 0.060)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_nose_bridge", (0.0, -0.405, 4.285), (0.060, 0.058, 0.155)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheekbone_left", (0.205, -0.340, 4.115), (0.135, 0.070, 0.105)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheekbone_right", (-0.205, -0.340, 4.115), (0.135, 0.070, 0.105)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_jaw_plane_left", (0.145, -0.285, 3.995), (0.120, 0.065, 0.105)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_jaw_plane_right", (-0.145, -0.285, 3.995), (0.120, 0.065, 0.105)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_philtrum", (0.0, -0.420, 4.035), (0.050, 0.038, 0.060)), "skin", MeshDensity(12, 7)),
        DetailedEllipsoidPart(EllipsoidPart("face_chin", (0.0, -0.300, 3.905), (0.165, 0.090, 0.095)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_lower_lip_plane", (0.0, -0.402, 3.955), (0.090, 0.042, 0.034)), "skin", MeshDensity(12, 7)),
    ),
    hair_detail_masses=(
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_left", (0.215, -0.005, 4.875), (0.095, 0.085, 0.095)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_center", (0.015, -0.035, 4.910), (0.105, 0.090, 0.105)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_right", (-0.205, 0.000, 4.875), (0.095, 0.085, 0.095)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_root", (-0.025, -0.300, 4.630), (0.095, 0.070, 0.110)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_tip", (-0.045, -0.410, 4.455), (0.060, 0.050, 0.095)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_left", (0.335, -0.145, 4.445), (0.075, 0.090, 0.135)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_right", (-0.335, -0.145, 4.445), (0.075, 0.090, 0.135)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_side_wave_left", (0.405, 0.070, 4.230), (0.070, 0.095, 0.145)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_side_wave_right", (-0.405, 0.070, 4.230), (0.070, 0.095, 0.145)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_center", (0.0, 0.300, 4.940), (0.125, 0.110, 0.150)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_left", (0.155, 0.265, 4.850), (0.105, 0.100, 0.135)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_right", (-0.155, 0.265, 4.850), (0.105, 0.100, 0.135)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_left", (0.230, 0.340, 4.535), (0.090, 0.085, 0.145)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_right", (-0.230, 0.340, 4.535), (0.090, 0.085, 0.145)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_left", (0.130, 0.315, 4.055), (0.065, 0.075, 0.125)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_center", (0.0, 0.340, 4.015), (0.065, 0.070, 0.115)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_right", (-0.130, 0.315, 4.055), (0.065, 0.075, 0.125)), "hair", MeshDensity(12, 8)),
    ),
    face_dark_details=(
        DetailedBoxPart(BoxPart("face_upper_lid_left", (0.145, -0.554, 4.195), (0.080, 0.016, 0.015), rotation_y_degrees=-2.5), "hair"),
        DetailedBoxPart(BoxPart("face_upper_lid_right", (-0.145, -0.554, 4.195), (0.080, 0.016, 0.015), rotation_y_degrees=2.5), "hair"),
        DetailedBoxPart(BoxPart("face_nostril_left", (0.025, -0.553, 4.120), (0.022, 0.014, 0.014)), "hair"),
        DetailedBoxPart(BoxPart("face_nostril_right", (-0.025, -0.553, 4.120), (0.022, 0.014, 0.014)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_left", (0.050, -0.523, 3.974), (0.026, 0.016, 0.017)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_right", (-0.050, -0.523, 3.974), (0.026, 0.016, 0.017)), "hair"),
        DetailedBoxPart(BoxPart("face_lower_lip_shadow", (0.0, -0.515, 3.936), (0.056, 0.016, 0.015)), "hair"),
    ),
)


def load_head_profile_v05(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V05.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V05.assert_valid()
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V05


def load_head_detail_profile_v05(character_id: str) -> HeadDetailProfileV05:
    if character_id != HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V05.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_DETAIL_V05
