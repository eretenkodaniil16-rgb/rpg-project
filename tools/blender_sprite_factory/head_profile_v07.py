from __future__ import annotations

from dataclasses import dataclass

from head_profile import BoxPart, EllipsoidPart, HeadProfile, NosePart
from head_profile_v04 import DetailedBoxPart, DetailedEllipsoidPart, MeshDensity
from head_profile_v06 import HUMAN_WARRIOR_M01_HEAD_V06


@dataclass(frozen=True)
class HeadDetailProfileV07:
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
        if self.revision != "v07" or self.proxy_revision != "v10":
            raise ValueError("Detailed head profile must match head v07 / proxy v10")
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
        names = [
            item.part.name
            for item in self.face_skin_masses + self.hair_detail_masses + self.face_dark_details
        ]
        if len(names) != len(set(names)):
            raise ValueError("Detailed head part names must be unique")
        if "hair_front_crown_bridge" not in names:
            raise ValueError("Front crown bridge is required for stable rear projection")
        if not {"hair_sideburn_left", "hair_sideburn_right"}.issubset(names):
            raise ValueError("Sideburn locks are required to frame the exposed face")


HUMAN_WARRIOR_M01_HEAD_V07 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v07",
    proxy_revision="v10",
    head_base=HUMAN_WARRIOR_M01_HEAD_V06.head_base,
    jaw=HUMAN_WARRIOR_M01_HEAD_V06.jaw,
    ears=HUMAN_WARRIOR_M01_HEAD_V06.ears,
    nose=NosePart((0.0, -0.480, 4.175), 0.035, 0.014, 0.118),
    hair_cap=EllipsoidPart("hair_cap", (0.0, 0.070, 4.665), (0.460, 0.355, 0.290)),
    hair_back_masses=HUMAN_WARRIOR_M01_HEAD_V06.hair_back_masses,
    hair_front_locks=(
        EllipsoidPart("hair_crown_front_left", (0.165, -0.205, 4.760), (0.155, 0.140, 0.170)),
        EllipsoidPart("hair_crown_front_center", (0.0, -0.245, 4.795), (0.170, 0.150, 0.180)),
        EllipsoidPart("hair_crown_front_right", (-0.165, -0.205, 4.760), (0.155, 0.140, 0.170)),
        EllipsoidPart("hair_temple_front_left", (0.225, -0.335, 4.465), (0.145, 0.120, 0.210)),
        EllipsoidPart("hair_forelock_characteristic", (-0.040, -0.385, 4.525), (0.120, 0.095, 0.195)),
        EllipsoidPart("hair_temple_front_right", (-0.225, -0.335, 4.465), (0.145, 0.120, 0.210)),
    ),
    hair_side_locks=(
        EllipsoidPart("hair_lock_side_left", (0.385, -0.070, 4.335), (0.120, 0.170, 0.335)),
        EllipsoidPart("hair_lock_side_right", (-0.385, -0.070, 4.335), (0.120, 0.170, 0.335)),
    ),
    brows=(
        BoxPart("face_brow_left", (0.140, -0.520, 4.355), (0.098, 0.025, 0.021), -6.0),
        BoxPart("face_brow_right", (-0.140, -0.520, 4.355), (0.098, 0.025, 0.021), 6.0),
    ),
    eyes=HUMAN_WARRIOR_M01_HEAD_V06.eyes,
    mouth=HUMAN_WARRIOR_M01_HEAD_V06.mouth,
)


HUMAN_WARRIOR_M01_HEAD_DETAIL_V07 = HeadDetailProfileV07(
    character_id="human_warrior_m01",
    revision="v07",
    proxy_revision="v10",
    cranium_density=MeshDensity(24, 14),
    jaw_density=MeshDensity(20, 12),
    ear_density=MeshDensity(14, 9),
    hair_cap_density=MeshDensity(24, 14),
    hair_primary_density=MeshDensity(20, 12),
    hair_secondary_density=MeshDensity(16, 10),
    hair_tertiary_density=MeshDensity(12, 8),
    nose_vertices=10,
    face_skin_masses=(
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_left", (0.145, -0.390, 4.380), (0.120, 0.046, 0.046)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_right", (-0.145, -0.390, 4.380), (0.120, 0.046, 0.046)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_nose_bridge", (0.0, -0.395, 4.280), (0.048, 0.046, 0.140)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheekbone_left", (0.185, -0.305, 4.105), (0.100, 0.050, 0.078)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheekbone_right", (-0.185, -0.305, 4.105), (0.100, 0.050, 0.078)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_jaw_plane_left", (0.130, -0.260, 4.005), (0.088, 0.046, 0.080)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_jaw_plane_right", (-0.130, -0.260, 4.005), (0.088, 0.046, 0.080)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_philtrum", (0.0, -0.402, 4.040), (0.038, 0.028, 0.048)), "skin", MeshDensity(12, 7)),
        DetailedEllipsoidPart(EllipsoidPart("face_chin", (0.0, -0.280, 3.915), (0.138, 0.070, 0.076)), "skin", MeshDensity(16, 9)),
        DetailedEllipsoidPart(EllipsoidPart("face_lower_lip_plane", (0.0, -0.388, 3.965), (0.070, 0.032, 0.027)), "skin", MeshDensity(12, 7)),
    ),
    hair_detail_masses=(
        DetailedEllipsoidPart(EllipsoidPart("hair_front_crown_bridge", (0.0, -0.365, 4.830), (0.270, 0.130, 0.240)), "hair", MeshDensity(20, 12)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_left", (0.205, -0.020, 4.820), (0.092, 0.083, 0.092)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_center", (0.010, -0.045, 4.845), (0.102, 0.088, 0.102)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_right", (-0.200, -0.015, 4.820), (0.092, 0.083, 0.092)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_hairline_left", (0.190, -0.420, 4.405), (0.110, 0.060, 0.185)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_hairline_center", (0.0, -0.425, 4.440), (0.115, 0.055, 0.145)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_hairline_right", (-0.190, -0.420, 4.405), (0.110, 0.060, 0.185)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_root", (-0.025, -0.345, 4.595), (0.088, 0.063, 0.102)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_tip", (-0.045, -0.435, 4.445), (0.056, 0.046, 0.088)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_left", (0.325, -0.190, 4.420), (0.075, 0.090, 0.135)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_right", (-0.325, -0.190, 4.420), (0.075, 0.090, 0.135)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_sideburn_left", (0.300, -0.365, 4.165), (0.070, 0.060, 0.180)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_sideburn_right", (-0.300, -0.365, 4.165), (0.070, 0.060, 0.180)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_side_wave_left", (0.390, 0.010, 4.215), (0.066, 0.088, 0.138)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_side_wave_right", (-0.390, 0.010, 4.215), (0.066, 0.088, 0.138)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_center", (0.0, 0.010, 4.895), (0.125, 0.100, 0.160)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_left", (0.150, 0.030, 4.850), (0.102, 0.092, 0.135)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_crest_right", (-0.150, 0.030, 4.850), (0.102, 0.092, 0.135)), "hair", MeshDensity(16, 10)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_left", (0.220, 0.275, 4.515), (0.083, 0.078, 0.138)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_right", (-0.220, 0.275, 4.515), (0.083, 0.078, 0.138)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_left", (0.122, 0.278, 4.048), (0.060, 0.068, 0.118)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_center", (0.0, 0.292, 4.012), (0.060, 0.066, 0.108)), "hair", MeshDensity(12, 8)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_right", (-0.122, 0.278, 4.048), (0.060, 0.068, 0.118)), "hair", MeshDensity(12, 8)),
    ),
    face_dark_details=(
        DetailedBoxPart(BoxPart("face_upper_lid_left", (0.140, -0.552, 4.195), (0.074, 0.015, 0.014), -2.5), "hair"),
        DetailedBoxPart(BoxPart("face_upper_lid_right", (-0.140, -0.552, 4.195), (0.074, 0.015, 0.014), 2.5), "hair"),
        DetailedBoxPart(BoxPart("face_nostril_left", (0.023, -0.547, 4.120), (0.019, 0.013, 0.013)), "hair"),
        DetailedBoxPart(BoxPart("face_nostril_right", (-0.023, -0.547, 4.120), (0.019, 0.013, 0.013)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_left", (0.046, -0.519, 3.980), (0.023, 0.015, 0.016)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_right", (-0.046, -0.519, 3.980), (0.023, 0.015, 0.016)), "hair"),
        DetailedBoxPart(BoxPart("face_lower_lip_shadow", (0.0, -0.511, 3.945), (0.050, 0.015, 0.014)), "hair"),
    ),
)


def load_head_profile_v07(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V07.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V07.assert_valid()
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V07


def load_head_detail_profile_v07(character_id: str) -> HeadDetailProfileV07:
    if character_id != HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V07.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_DETAIL_V07
