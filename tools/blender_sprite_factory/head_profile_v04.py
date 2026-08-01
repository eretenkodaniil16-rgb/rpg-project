from __future__ import annotations

from dataclasses import dataclass

from head_profile import (
    BoxPart,
    EllipsoidPart,
    HeadProfile,
    HUMAN_WARRIOR_M01_HEAD_V03,
    NosePart,
)


@dataclass(frozen=True)
class MeshDensity:
    segments: int
    rings: int

    def assert_valid(self) -> None:
        if self.segments < 8:
            raise ValueError("Ellipsoid mesh needs at least 8 segments")
        if self.rings < 5:
            raise ValueError("Ellipsoid mesh needs at least 5 rings")
        if self.rings >= self.segments:
            raise ValueError("Ellipsoid rings must stay below segment count")


@dataclass(frozen=True)
class DetailedEllipsoidPart:
    part: EllipsoidPart
    material_slot: str
    density: MeshDensity


@dataclass(frozen=True)
class DetailedBoxPart:
    part: BoxPart
    material_slot: str
    bevel: float = 0.0


@dataclass(frozen=True)
class HeadDetailProfile:
    character_id: str
    revision: str
    proxy_revision: str
    cranium_density: MeshDensity
    jaw_density: MeshDensity
    ear_density: MeshDensity
    hair_cap_density: MeshDensity
    hair_main_density: MeshDensity
    hair_lock_density: MeshDensity
    nose_vertices: int
    face_skin_masses: tuple[DetailedEllipsoidPart, ...]
    hair_detail_masses: tuple[DetailedEllipsoidPart, ...]
    face_dark_details: tuple[DetailedBoxPart, ...]

    def assert_valid(self) -> None:
        if self.character_id != "human_warrior_m01":
            raise ValueError("Detailed head profile belongs to another character")
        if self.revision != "v04" or self.proxy_revision != "v07":
            raise ValueError("Detailed head profile must match head v04 / proxy v07")
        for density in (
            self.cranium_density,
            self.jaw_density,
            self.ear_density,
            self.hair_cap_density,
            self.hair_main_density,
            self.hair_lock_density,
        ):
            density.assert_valid()
        if self.nose_vertices < 6:
            raise ValueError("Detailed adult nose needs at least 6 vertices")
        if len(self.face_skin_masses) < 7:
            raise ValueError("Face must have separate brow, cheek, bridge and chin masses")
        if len(self.hair_detail_masses) < 10:
            raise ValueError("Medium wavy hair needs separate secondary locks")
        if len(self.face_dark_details) < 5:
            raise ValueError("Eyes and mouth need separate secondary dark details")
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


HUMAN_WARRIOR_M01_HEAD_V04 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v04",
    proxy_revision="v07",
    head_base=EllipsoidPart(
        "head_base",
        HUMAN_WARRIOR_M01_HEAD_V03.head_base.location,
        HUMAN_WARRIOR_M01_HEAD_V03.head_base.scale,
    ),
    jaw=EllipsoidPart(
        "head_jaw",
        (0.0, -0.20, 4.04),
        (0.355, 0.285, 0.33),
    ),
    ears=(
        EllipsoidPart(
            "head_ear_left",
            (0.425, -0.025, 4.27),
            (0.078, 0.068, 0.122),
        ),
        EllipsoidPart(
            "head_ear_right",
            (-0.425, -0.025, 4.27),
            (0.078, 0.068, 0.122),
        ),
    ),
    nose=NosePart(
        location=(0.0, -0.485, 4.18),
        radius_bottom=0.040,
        radius_top=0.016,
        depth=0.13,
    ),
    hair_cap=EllipsoidPart(
        "hair_cap",
        (0.0, 0.08, 4.67),
        (0.47, 0.37, 0.30),
    ),
    hair_back_masses=(
        EllipsoidPart(
            "hair_back_shell",
            (0.0, 0.20, 4.49),
            (0.36, 0.22, 0.31),
        ),
        EllipsoidPart(
            "hair_crown_back_center",
            (0.0, 0.08, 4.80),
            (0.19, 0.17, 0.20),
        ),
        EllipsoidPart(
            "hair_crown_back_left",
            (0.19, 0.10, 4.75),
            (0.16, 0.15, 0.18),
        ),
        EllipsoidPart(
            "hair_crown_back_right",
            (-0.19, 0.10, 4.75),
            (0.16, 0.15, 0.18),
        ),
        EllipsoidPart(
            "hair_back_wave_left",
            (0.30, 0.18, 4.43),
            (0.16, 0.17, 0.31),
        ),
        EllipsoidPart(
            "hair_back_wave_right",
            (-0.30, 0.18, 4.43),
            (0.16, 0.17, 0.31),
        ),
        EllipsoidPart(
            "hair_nape_left",
            (0.20, 0.20, 4.17),
            (0.13, 0.15, 0.22),
        ),
        EllipsoidPart(
            "hair_nape_center",
            (0.0, 0.22, 4.13),
            (0.13, 0.14, 0.20),
        ),
        EllipsoidPart(
            "hair_nape_right",
            (-0.20, 0.20, 4.17),
            (0.13, 0.15, 0.22),
        ),
    ),
    hair_front_locks=(
        EllipsoidPart(
            "hair_crown_front_left",
            (0.18, -0.21, 4.76),
            (0.17, 0.14, 0.17),
        ),
        EllipsoidPart(
            "hair_crown_front_center",
            (0.0, -0.25, 4.79),
            (0.18, 0.15, 0.18),
        ),
        EllipsoidPart(
            "hair_crown_front_right",
            (-0.18, -0.21, 4.76),
            (0.17, 0.14, 0.17),
        ),
        EllipsoidPart(
            "hair_temple_front_left",
            (0.25, -0.31, 4.52),
            (0.14, 0.11, 0.18),
        ),
        EllipsoidPart(
            "hair_forelock_characteristic",
            (-0.045, -0.37, 4.55),
            (0.13, 0.10, 0.20),
        ),
        EllipsoidPart(
            "hair_temple_front_right",
            (-0.25, -0.31, 4.52),
            (0.14, 0.11, 0.18),
        ),
    ),
    hair_side_locks=(
        EllipsoidPart(
            "hair_lock_side_left",
            (0.41, 0.00, 4.34),
            (0.12, 0.15, 0.34),
        ),
        EllipsoidPart(
            "hair_lock_side_right",
            (-0.41, 0.00, 4.34),
            (0.12, 0.15, 0.34),
        ),
    ),
    brows=(
        BoxPart(
            "face_brow_left",
            (0.13, -0.515, 4.35),
            (0.115, 0.030, 0.028),
            rotation_y_degrees=-7.0,
        ),
        BoxPart(
            "face_brow_right",
            (-0.13, -0.515, 4.35),
            (0.115, 0.030, 0.028),
            rotation_y_degrees=7.0,
        ),
    ),
    eyes=(
        BoxPart(
            "face_eye_left",
            (0.13, -0.535, 4.18),
            (0.047, 0.024, 0.026),
        ),
        BoxPart(
            "face_eye_right",
            (-0.13, -0.535, 4.18),
            (0.047, 0.024, 0.026),
        ),
    ),
    mouth=BoxPart(
        "face_mouth",
        (0.0, -0.510, 3.98),
        (0.075, 0.023, 0.024),
    ),
)


HUMAN_WARRIOR_M01_HEAD_DETAIL_V04 = HeadDetailProfile(
    character_id="human_warrior_m01",
    revision="v04",
    proxy_revision="v07",
    cranium_density=MeshDensity(20, 12),
    jaw_density=MeshDensity(18, 10),
    ear_density=MeshDensity(12, 8),
    hair_cap_density=MeshDensity(20, 12),
    hair_main_density=MeshDensity(16, 10),
    hair_lock_density=MeshDensity(12, 7),
    nose_vertices=8,
    face_skin_masses=(
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_left", (0.15, -0.425, 4.37), (0.18, 0.070, 0.075)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_brow_ridge_right", (-0.15, -0.425, 4.37), (0.18, 0.070, 0.075)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_nose_bridge", (0.0, -0.405, 4.28), (0.070, 0.070, 0.17)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheek_left", (0.20, -0.365, 4.08), (0.17, 0.085, 0.13)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_cheek_right", (-0.20, -0.365, 4.08), (0.17, 0.085, 0.13)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_chin", (0.0, -0.315, 3.88), (0.20, 0.105, 0.11)), "skin", MeshDensity(14, 8)),
        DetailedEllipsoidPart(EllipsoidPart("face_lower_lip_plane", (0.0, -0.405, 3.95), (0.105, 0.050, 0.040)), "skin", MeshDensity(12, 7)),
    ),
    hair_detail_masses=(
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_left", (0.23, -0.02, 4.87), (0.10, 0.09, 0.10)), "hair", MeshDensity(12, 7)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_center", (0.02, -0.06, 4.90), (0.11, 0.09, 0.11)), "hair", MeshDensity(12, 7)),
        DetailedEllipsoidPart(EllipsoidPart("hair_wave_top_right", (-0.22, -0.01, 4.86), (0.10, 0.09, 0.10)), "hair", MeshDensity(12, 7)),
        DetailedEllipsoidPart(EllipsoidPart("hair_forelock_tip", (-0.05, -0.45, 4.46), (0.075, 0.060, 0.12)), "hair", MeshDensity(10, 6)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_left", (0.36, -0.17, 4.44), (0.085, 0.10, 0.14)), "hair", MeshDensity(10, 6)),
        DetailedEllipsoidPart(EllipsoidPart("hair_temple_curl_right", (-0.36, -0.17, 4.44), (0.085, 0.10, 0.14)), "hair", MeshDensity(10, 6)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_left", (0.24, 0.32, 4.52), (0.10, 0.09, 0.15)), "hair", MeshDensity(10, 6)),
        DetailedEllipsoidPart(EllipsoidPart("hair_back_ripple_right", (-0.24, 0.32, 4.52), (0.10, 0.09, 0.15)), "hair", MeshDensity(10, 6)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_left", (0.14, 0.29, 4.03), (0.075, 0.08, 0.13)), "hair", MeshDensity(10, 6)),
        DetailedEllipsoidPart(EllipsoidPart("hair_nape_tip_right", (-0.14, 0.29, 4.03), (0.075, 0.08, 0.13)), "hair", MeshDensity(10, 6)),
    ),
    face_dark_details=(
        DetailedBoxPart(BoxPart("face_upper_lid_left", (0.13, -0.548, 4.205), (0.090, 0.018, 0.018), rotation_y_degrees=-3.0), "hair"),
        DetailedBoxPart(BoxPart("face_upper_lid_right", (-0.13, -0.548, 4.205), (0.090, 0.018, 0.018), rotation_y_degrees=3.0), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_left", (0.055, -0.525, 3.985), (0.032, 0.018, 0.020)), "hair"),
        DetailedBoxPart(BoxPart("face_mouth_corner_right", (-0.055, -0.525, 3.985), (0.032, 0.018, 0.020)), "hair"),
        DetailedBoxPart(BoxPart("face_lower_lip_shadow", (0.0, -0.520, 3.940), (0.065, 0.018, 0.018)), "hair"),
    ),
)


def load_head_profile_v04(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V04.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V04.assert_valid()
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V04.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V04


def load_head_detail_profile_v04(character_id: str) -> HeadDetailProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_DETAIL_V04.character_id:
        raise KeyError(f"No detailed head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_DETAIL_V04.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_DETAIL_V04
