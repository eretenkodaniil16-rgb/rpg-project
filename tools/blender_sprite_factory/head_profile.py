from __future__ import annotations

import re
from dataclasses import dataclass


Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class EllipsoidPart:
    name: str
    location: Vector3
    scale: Vector3


@dataclass(frozen=True)
class BoxPart:
    name: str
    location: Vector3
    dimensions: Vector3
    rotation_y_degrees: float = 0.0


@dataclass(frozen=True)
class NosePart:
    location: Vector3
    radius_bottom: float
    radius_top: float
    depth: float


@dataclass(frozen=True)
class HeadProfile:
    character_id: str
    revision: str
    proxy_revision: str
    head_base: EllipsoidPart
    jaw: EllipsoidPart
    ears: tuple[EllipsoidPart, EllipsoidPart]
    nose: NosePart
    hair_cap: EllipsoidPart
    hair_back_masses: tuple[EllipsoidPart, ...]
    hair_front_locks: tuple[EllipsoidPart, ...]
    hair_side_locks: tuple[EllipsoidPart, EllipsoidPart]
    brows: tuple[BoxPart, BoxPart]
    eyes: tuple[BoxPart, BoxPart]
    mouth: BoxPart

    def assert_valid(self) -> None:
        if self.character_id != "human_warrior_m01":
            raise ValueError("Head profile belongs to another character")
        if not re.fullmatch(r"v[0-9]{2}", self.revision):
            raise ValueError("Head revision must use the vNN format")
        if not re.fullmatch(r"v[0-9]{2}", self.proxy_revision):
            raise ValueError("Proxy revision must use the vNN format")
        if self.head_base.scale[0] <= self.jaw.scale[0]:
            raise ValueError("Adult head must taper from cranium to jaw")
        if self.hair_cap.location[1] <= self.head_base.location[1]:
            raise ValueError("Hair cap must sit behind the exposed face plane")
        if not self.hair_back_masses:
            raise ValueError("Medium-length hair needs a separate back mass")
        if max(part.location[1] for part in self.hair_back_masses) <= 0.15:
            raise ValueError("Back hair must remain physically behind the head")

        eye_top = max(
            part.location[2] + part.dimensions[2] * 0.5
            for part in self.eyes
        )
        front_hairline = min(
            part.location[2] - part.scale[2]
            for part in self.hair_front_locks
        )
        if front_hairline < eye_top:
            raise ValueError("Front hair must not cover the readable eye line")

        left_brow, right_brow = self.brows
        if not left_brow.location[0] > 0.0 > right_brow.location[0]:
            raise ValueError("Brows must stay on their physical face sides")
        if not (
            left_brow.rotation_y_degrees < 0.0
            < right_brow.rotation_y_degrees
        ):
            raise ValueError("Brows must form the approved stern expression")

        left_eye, right_eye = self.eyes
        if not left_eye.location[0] > 0.0 > right_eye.location[0]:
            raise ValueError("Eyes must stay on their physical face sides")
        if abs(left_eye.location[0] + right_eye.location[0]) > 0.001:
            raise ValueError("Eye spacing must stay centered")
        if self.mouth.location[2] >= min(part.location[2] for part in self.eyes):
            raise ValueError("Mouth must remain below the eyes")


HUMAN_WARRIOR_M01_HEAD_V01 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v01",
    proxy_revision="v04",
    head_base=EllipsoidPart(
        "head_base",
        (0.0, -0.07, 4.30),
        (0.46, 0.37, 0.58),
    ),
    jaw=EllipsoidPart(
        "head_jaw",
        (0.0, -0.18, 4.08),
        (0.35, 0.29, 0.30),
    ),
    ears=(
        EllipsoidPart(
            "head_ear_left",
            (0.43, -0.02, 4.27),
            (0.09, 0.08, 0.14),
        ),
        EllipsoidPart(
            "head_ear_right",
            (-0.43, -0.02, 4.27),
            (0.09, 0.08, 0.14),
        ),
    ),
    nose=NosePart(
        location=(0.0, -0.48, 4.25),
        radius_bottom=0.085,
        radius_top=0.035,
        depth=0.23,
    ),
    hair_cap=EllipsoidPart(
        "hair_cap",
        (0.0, 0.08, 4.66),
        (0.51, 0.42, 0.36),
    ),
    hair_back_masses=(
        EllipsoidPart(
            "hair_back_mass",
            (0.0, 0.27, 4.38),
            (0.47, 0.24, 0.46),
        ),
        EllipsoidPart(
            "hair_back_left",
            (0.35, 0.20, 4.30),
            (0.15, 0.18, 0.39),
        ),
        EllipsoidPart(
            "hair_back_right",
            (-0.35, 0.20, 4.30),
            (0.15, 0.18, 0.39),
        ),
    ),
    hair_front_locks=(
        EllipsoidPart(
            "hair_lock_crown_front",
            (0.05, -0.31, 4.83),
            (0.18, 0.13, 0.22),
        ),
        EllipsoidPart(
            "hair_lock_front_left",
            (0.18, -0.34, 4.56),
            (0.14, 0.10, 0.17),
        ),
        EllipsoidPart(
            "hair_lock_front_center",
            (-0.02, -0.38, 4.59),
            (0.12, 0.09, 0.20),
        ),
        EllipsoidPart(
            "hair_lock_front_right",
            (-0.20, -0.33, 4.55),
            (0.15, 0.10, 0.16),
        ),
    ),
    hair_side_locks=(
        EllipsoidPart(
            "hair_lock_side_left",
            (0.42, -0.01, 4.32),
            (0.12, 0.16, 0.36),
        ),
        EllipsoidPart(
            "hair_lock_side_right",
            (-0.42, -0.01, 4.33),
            (0.12, 0.16, 0.35),
        ),
    ),
    brows=(
        BoxPart(
            "face_brow_left",
            (0.13, -0.45, 4.41),
            (0.20, 0.04, 0.05),
            rotation_y_degrees=-12.0,
        ),
        BoxPart(
            "face_brow_right",
            (-0.13, -0.45, 4.41),
            (0.20, 0.04, 0.05),
            rotation_y_degrees=12.0,
        ),
    ),
    eyes=(
        BoxPart(
            "face_eye_left",
            (0.13, -0.455, 4.32),
            (0.065, 0.035, 0.045),
        ),
        BoxPart(
            "face_eye_right",
            (-0.13, -0.455, 4.32),
            (0.065, 0.035, 0.045),
        ),
    ),
    mouth=BoxPart(
        "face_mouth",
        (0.0, -0.465, 4.09),
        (0.16, 0.035, 0.035),
    ),
)


HUMAN_WARRIOR_M01_HEAD_V02 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v02",
    proxy_revision="v05",
    head_base=EllipsoidPart(
        "head_base",
        (0.0, -0.08, 4.30),
        (0.46, 0.37, 0.58),
    ),
    jaw=EllipsoidPart(
        "head_jaw",
        (0.0, -0.20, 4.06),
        (0.38, 0.30, 0.33),
    ),
    ears=(
        EllipsoidPart(
            "head_ear_left",
            (0.44, -0.03, 4.27),
            (0.09, 0.08, 0.14),
        ),
        EllipsoidPart(
            "head_ear_right",
            (-0.44, -0.03, 4.27),
            (0.09, 0.08, 0.14),
        ),
    ),
    nose=NosePart(
        location=(0.0, -0.51, 4.25),
        radius_bottom=0.09,
        radius_top=0.04,
        depth=0.25,
    ),
    hair_cap=EllipsoidPart(
        "hair_cap",
        (0.0, 0.08, 4.68),
        (0.51, 0.42, 0.34),
    ),
    hair_back_masses=(
        EllipsoidPart(
            "hair_back_mass",
            (0.0, 0.30, 4.40),
            (0.48, 0.24, 0.43),
        ),
        EllipsoidPart(
            "hair_lock_crown_back",
            (-0.05, 0.58, 4.83),
            (0.18, 0.14, 0.22),
        ),
        EllipsoidPart(
            "hair_back_left",
            (0.36, 0.22, 4.30),
            (0.15, 0.18, 0.39),
        ),
        EllipsoidPart(
            "hair_back_right",
            (-0.36, 0.22, 4.30),
            (0.15, 0.18, 0.39),
        ),
    ),
    hair_front_locks=(
        EllipsoidPart(
            "hair_lock_crown_front",
            (0.05, -0.58, 4.83),
            (0.18, 0.14, 0.22),
        ),
        EllipsoidPart(
            "hair_lock_front_left",
            (0.19, -0.40, 4.61),
            (0.14, 0.10, 0.16),
        ),
        EllipsoidPart(
            "hair_lock_front_center",
            (-0.01, -0.43, 4.63),
            (0.11, 0.09, 0.16),
        ),
        EllipsoidPart(
            "hair_lock_front_right",
            (-0.20, -0.39, 4.60),
            (0.15, 0.10, 0.16),
        ),
    ),
    hair_side_locks=(
        EllipsoidPart(
            "hair_lock_side_left",
            (0.43, -0.01, 4.32),
            (0.12, 0.16, 0.36),
        ),
        EllipsoidPart(
            "hair_lock_side_right",
            (-0.43, -0.01, 4.33),
            (0.12, 0.16, 0.35),
        ),
    ),
    brows=(
        BoxPart(
            "face_brow_left",
            (0.14, -0.49, 4.42),
            (0.18, 0.045, 0.045),
            rotation_y_degrees=-8.0,
        ),
        BoxPart(
            "face_brow_right",
            (-0.14, -0.49, 4.42),
            (0.18, 0.045, 0.045),
            rotation_y_degrees=8.0,
        ),
    ),
    eyes=(
        BoxPart(
            "face_eye_left",
            (0.14, -0.505, 4.28),
            (0.08, 0.04, 0.05),
        ),
        BoxPart(
            "face_eye_right",
            (-0.14, -0.505, 4.28),
            (0.08, 0.04, 0.05),
        ),
    ),
    mouth=BoxPart(
        "face_mouth",
        (0.0, -0.515, 4.04),
        (0.18, 0.04, 0.04),
    ),
)


HUMAN_WARRIOR_M01_HEAD_V03 = HeadProfile(
    character_id="human_warrior_m01",
    revision="v03",
    proxy_revision="v06",
    head_base=EllipsoidPart(
        "head_base",
        (0.0, -0.08, 4.30),
        (0.46, 0.37, 0.58),
    ),
    jaw=EllipsoidPart(
        "head_jaw",
        (0.0, -0.22, 4.03),
        (0.36, 0.30, 0.36),
    ),
    ears=(
        EllipsoidPart(
            "head_ear_left",
            (0.43, -0.03, 4.27),
            (0.085, 0.075, 0.13),
        ),
        EllipsoidPart(
            "head_ear_right",
            (-0.43, -0.03, 4.27),
            (0.085, 0.075, 0.13),
        ),
    ),
    nose=NosePart(
        location=(0.0, -0.53, 4.21),
        radius_bottom=0.075,
        radius_top=0.032,
        depth=0.22,
    ),
    hair_cap=EllipsoidPart(
        "hair_cap",
        (0.0, 0.10, 4.69),
        (0.44, 0.34, 0.27),
    ),
    hair_back_masses=(
        EllipsoidPart(
            "hair_back_mass",
            (0.0, 0.34, 4.43),
            (0.31, 0.20, 0.35),
        ),
        EllipsoidPart(
            "hair_lock_crown_back",
            (-0.05, 0.66, 4.86),
            (0.16, 0.11, 0.24),
        ),
        EllipsoidPart(
            "hair_back_left",
            (0.30, 0.31, 4.39),
            (0.16, 0.15, 0.32),
        ),
        EllipsoidPart(
            "hair_back_right",
            (-0.30, 0.31, 4.39),
            (0.16, 0.15, 0.32),
        ),
        EllipsoidPart(
            "hair_nape_left",
            (0.20, 0.34, 4.18),
            (0.12, 0.14, 0.23),
        ),
        EllipsoidPart(
            "hair_nape_right",
            (-0.20, 0.34, 4.18),
            (0.12, 0.14, 0.23),
        ),
    ),
    hair_front_locks=(
        EllipsoidPart(
            "hair_lock_crown_front",
            (0.06, -0.61, 4.84),
            (0.16, 0.11, 0.22),
        ),
        EllipsoidPart(
            "hair_lock_front_left",
            (0.18, -0.40, 4.65),
            (0.12, 0.09, 0.13),
        ),
        EllipsoidPart(
            "hair_lock_front_center",
            (-0.02, -0.47, 4.58),
            (0.10, 0.08, 0.17),
        ),
        EllipsoidPart(
            "hair_lock_front_right",
            (-0.18, -0.39, 4.64),
            (0.12, 0.09, 0.13),
        ),
    ),
    hair_side_locks=(
        EllipsoidPart(
            "hair_lock_side_left",
            (0.43, 0.00, 4.32),
            (0.10, 0.14, 0.31),
        ),
        EllipsoidPart(
            "hair_lock_side_right",
            (-0.43, 0.00, 4.33),
            (0.10, 0.14, 0.30),
        ),
    ),
    brows=(
        BoxPart(
            "face_brow_left",
            (0.13, -0.51, 4.39),
            (0.14, 0.035, 0.035),
            rotation_y_degrees=-6.0,
        ),
        BoxPart(
            "face_brow_right",
            (-0.13, -0.51, 4.39),
            (0.14, 0.035, 0.035),
            rotation_y_degrees=6.0,
        ),
    ),
    eyes=(
        BoxPart(
            "face_eye_left",
            (0.13, -0.54, 4.23),
            (0.06, 0.03, 0.035),
        ),
        BoxPart(
            "face_eye_right",
            (-0.13, -0.54, 4.23),
            (0.06, 0.03, 0.035),
        ),
    ),
    mouth=BoxPart(
        "face_mouth",
        (0.0, -0.54, 3.98),
        (0.11, 0.03, 0.03),
    ),
)


def load_head_profile(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V03.character_id:
        raise KeyError(f"No head profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V03.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V03
