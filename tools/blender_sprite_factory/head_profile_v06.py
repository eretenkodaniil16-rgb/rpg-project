from __future__ import annotations

from dataclasses import dataclass

from head_profile import BoxPart, EllipsoidPart, HeadProfile, NosePart
from head_profile_v04 import DetailedBoxPart, DetailedEllipsoidPart, MeshDensity
from head_profile_v05 import HUMAN_WARRIOR_M01_HEAD_V05


@dataclass(frozen=True)
class HeadDetailProfileV06:
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
        if self.revision != "v06" or self.proxy_revision != "v09":
            raise ValueError("Detailed head profile must match head v06 / proxy v09")
        densities = (
            self.cranium_density,
            self.jaw_density,
            self.ear_density,
            self.hair_cap_density,
            self.hair_primary_density,
            self.hair_secondary_density,
            self.hair_tertiary_density,
        )
        for density in densities:
            density.assert_valid()
        if not (
            self.hair_primary_density.segments
            > self.hair_secondary_density.segments
            > self.hair_tertiary_density.segments
        ):
            raise ValueError("Hair density tiers must descend from primary to tertiary")
        if self.nose_vertices < 8:
            raise ValueError("Detailed adult nose needs at least 8 vertices")
        names = [item.part.name for item in self.face_skin_masses + self.hair_detail_masses + self.face_dark_details]
        if len(names) != len(set(names)):
            raise ValueError("Detailed head part names must be unique")
        if len(self.hair_detail_masses) < 16:
            raise ValueError("Hairline, crown, back and nape need separate connected masses")


HUMAN_WARRIOR_M01_HEAD_V06 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v06",
    proxy_revision="v09",
    head_base=HUMAN_WARRIOR_M01_HEAD_V05.head_base,
    jaw=HUMAN_WARRIOR_M01_HEAD_V05.jaw,
    ears=HUMAN_WARRIOR_M01_HEAD_V05.ears,
    nose=NosePart((0.0, -0.482, 4.175), 0.036, 0.014, 0.120),
    hair_cap=EllipsoidPart("hair_cap", (0.0, 0.075, 4.665), (0.460, 0.355, 0.290)),
    hair_back_masses=(
        EllipsoidPart("hair_back_shell", (0.0, 0.205, 4.500), (0.350, 0.220, 0.305)),
        EllipsoidPart("hair_crown_back_center", (0.0, 0.015, 4.865), (0.180, 0.155, 0.205)),
        EllipsoidPart("hair_crown_back_left", (0.180, 0.035, 4.820), (0.155, 0.140, 0.190)),
        EllipsoidPart("hair_crown_back_right", (-0.180, 0.035, 4.820), (0.155, 0.140, 0.190)),
        EllipsoidPart("hair_back_wave_left", (0.285, 0.185, 4.435), (0.145, 0.160, 0.295)),
        EllipsoidPart("hair_back_wave_right", (-0.285, 0.185, 4.435), (0.145, 0.160, 0.295)),
        EllipsoidPart("hair_nape_left", (0.180, 0.205, 4.175), (0.120, 0.140, 0.220)),
        EllipsoidPart("hair_nape_center", (0.0, 0.225, 4.125), (0.125, 0.130, 0.205)),
        EllipsoidPart("hair_nape_right", (-0.180, 0.205, 4.175), (0.120, 0.140, 0.220)),
    ),
    hair_front_locks=(
        EllipsoidPart("hair_crown_front_left", (0.165, -0.190, 4.750), (0.155, 0.135, 0.165)),
        EllipsoidPart("hair_crown_front_center", (0.0, -0.225, 4.780), (0.165, 0.145, 0.170)),
        EllipsoidPart("hair_crown_front_right", (-0.165, -0.190, 4.750), (0.155, 0.135, 0.165)),
        EllipsoidPart("hair_temple_front_left", (0.225, -0.320, 4.485), (0.140, 0.115, 0.195)),
        EllipsoidPart("hair_forelock_characteristic", (-0.040, -0.365, 4.535), (0.120, 0.095, 0.190)),
        EllipsoidPart("hair_temple_front_right", (-0.225, -0.320, 4.485), (0.140, 0.115, 0.195)),
    ),
    hair_side_locks=(
        EllipsoidPart("hair_lock_side_left", (0.390, -0.055, 4.340), (0.120, 0.165, 0.335)),
        EllipsoidPart("hair_lock_side_right", (-0.390, -0.055, 4.340), (0.120, 0.165, 0.335)),
    ),
    brows=(
        BoxPart("face_brow_left", (0.140, -0.520, 4.360), (0.100, 0.026, 0.022), -6.0),
        BoxPart("face_brow_right", (-0.140, -0.520, 4.360), (0.100, 0.026, 0.022), 6.0),
    ),
    eyes=(
        BoxPart("face_eye_left", (0.140, -0.540, 4.175), (0.042, 0.020, 0.020)),
        BoxPart("face_eye_right", (-0.140, -0.540, 4.175), (0.042, 0.020, 0.020)),
    ),
    mouth=BoxPart("face_mouth", (0.0, -0.507, 3.975), (0.066, 0.019, 0.020)),
)


HUMAN_WARRIOR_M01_HEAD_DETAIL_V06 = HeadDetailProfileV06(
    character_id="human_warrior_m01",
    revision="v06",
    proxy_revision="v09",
    cranium_density=MeshDensity(24, 14),
    jaw_density=MeshDensity(20, 12),
    ear_density=MeshDensity(14, 9),
    hair_cap_density=MeshDensity(24, 14),
    hair_primary_density=MeshDensity(20, 12),
    hair_secondary_density=MeshDensity(16, 10),
    hair_tertiary_density=MeshDensity(12, 8),
    nose_vertices=10,
    face_skin_masses=(
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_left", (0.145, -0.395, 4.385), (0.130, 0.050, 0.050)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_right", (-0.145, -0.395, 4.385), (0.130, 0.050, 0.050)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_nose_bridge", (0.0, -0.398, 4.280), (0.052, 0.050, 0.145)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheekbone_left", (0.190, -0.315, 4.105), (0.110, 0.055, 0.085)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheekbone_right", (-0.190, -0.315, 4.105), (0.110, 0.055, 0.085)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_jaw_plane_left", (0.135, -0.265, 4.005), (0.095, 0.050, 0.085)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_jaw_plane_right", (-0.135, -0.265, 4.005), (0.095, 0.050, 0.085)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_philtrum", (0.0, -0.405, 4.040), (0.040, 0.030, 0.050)), "skin", MeshDensity(12, 7)),
        DetailedEllipsoidPart(EllipsoidPart("face_chin", (0.0, -0.285, 3.915), (0.145, 0.075, 0.080)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_lower_lip_plane", (0.0, -0.390, 3.965), (0.075, 0.034, 0.028)), "skin", MeshDensity(12, 7)),
    ),
    hair_detail_masses=(
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_left", (0.210, -0.005, 4.825), (0.095, 0.085, 0.095)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_center", (0.015, -0.030, 4.850), (0.105, 0.090, 0.105)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_right", (-0.205, 0.000, 4.825), (0.095, 0.085, 0.095)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_hairline_left", (0.205, -0.405, 4.430), (0.100, 0.060, 0.155)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_hairline_center", (0.0, -0.405, 4.455), (0.120, 0.055, 0.120)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_hairline_right", (-0.205, -0.405, 4.430), (0.100, 0.060, 0.155)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_root", (-0.025, -0.330, 4.605), (0.090, 0.065, 0.105)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_tip", (-0.045, -0.425, 4.450), (0.058, 0.048, 0.090)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_left", (0.330, -0.175, 4.430), (0.075, 0.090, 0.135)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_right", (-0.330, -0.175, 4.430), (0.075, 0.090, 0.135)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_side_wave_left", (0.395, 0.020, 4.220), (0.068, 0.090, 0.140)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_side_wave_right", (-0.395, 0.020, 4.220), (0.068, 0.090, 0.140)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_center", (0.0, 0.015, 4.900), (0.130, 0.105, 0.165)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_left", (0.155, 0.035, 4.855), (0.105, 0.095, 0.140)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_right", (-0.155, 0.035, 4.855), (0.105, 0.095, 0.140)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_left", (0.225, 0.285, 4.520), (0.085, 0.080, 0.140)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_right", (-0.225, 0.285, 4.520), (0.085, 0.080, 0.140)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_left", (0.125, 0.285, 4.050), (0.062, 0.070, 0.120)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_center", (0.0, 0.300, 4.015), (0.062, 0.068, 0.110)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_right", (-0.125, 0.285, 4.050), (0.062, 0.070, 0.120)), "hair", MeshDensity(12, 8)),
    ),
    face_dark_details=(
        DetailedBoxPart(BoxPart("face_upper_lid_left", (0.140, -0.552, 4.195), (0.076, 0.015, 0.014), -2.5), "hair"),
        DetailedBoxPart(BoxPart("face_upper_lid_right", (-0.140, -0.552, 4.195), (0.076, 0.015, 0.014), 2.5), "hair"),
        DetailedBoxPart(BoxPart("face_nostril_left", (0.024, -0.548, 4.120), (0.020, 0.013, 0.013)), "hair"),
        DetailedBoxPart(BoxPart("face_nostril_right", (-0.024, -0.548, 4.120), (0.020, 0.013, 0.013)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_left", (0.047, -0.520, 3.980), (0.024, 0.015, 0.016)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_right", (-0.047, -0.520, 3.980), (0.024, 0.015, 0.016)), "hair"),
        DetailedBoxPart(BoxPart("face_lower_lip_shadow", (0.0, -0.512, 3.945), (0.052, 0.015, 0.014)), "hair"),
    ),
)


def load_head_profile_v06(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V06.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V06.assert_valid()
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V06


def load_head_detail_profile_v06(character_id: str) -> HeadDetailProfileV06:
    if character_id != HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V06.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_DETAIL_V06
