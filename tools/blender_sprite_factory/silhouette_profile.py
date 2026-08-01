from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Vector3 = tuple[float, float, float]
PhysicalSide = Literal["L", "R"]


@dataclass(frozen=True)
class EllipsoidPart:
    name: str
    location: Vector3
    scale: Vector3


@dataclass(frozen=True)
class ClothPanel:
    side: str
    location: Vector3
    radius_bottom: float
    radius_top: float
    depth: float
    cross_section_scale: tuple[float, float]
    bone_name: str


@dataclass(frozen=True)
class SilhouetteProfile:
    character_id: str
    revision: str
    pelvis_dimensions: Vector3
    ribcage_radius_bottom: float
    ribcage_radius_top: float
    ribcage_depth: float
    ribcage_depth_scale: float
    chest_armor_dimensions: Vector3
    chainmail_skirt_radius_bottom: float
    chainmail_skirt_radius_top: float
    belt_radius: float
    arm_shoulder_x: float
    arm_elbow_x: float
    arm_wrist_x: float
    arm_hand_x: float
    arm_elbow_y: float
    arm_wrist_y: float
    arm_hand_y: float
    upper_arm_radius: float
    forearm_radius: float
    hand_scale: Vector3
    left_pauldron_plates: tuple[EllipsoidPart, ...]
    right_pauldron: EllipsoidPart
    leg_hip_x: float
    leg_knee_x: float
    leg_ankle_x: float
    boot_x: float
    left_leg_depth: float
    right_leg_depth: float
    thigh_radius: float
    shin_radius: float
    knee_scale: Vector3
    boot_dimensions: Vector3
    boot_outward_degrees: float
    cloth_panels: tuple[ClothPanel, ...]

    def arm_points(
        self,
        side: PhysicalSide,
    ) -> tuple[Vector3, Vector3, Vector3, Vector3, Vector3]:
        sign = _side_sign(side)
        return (
            (self.arm_shoulder_x * sign, 0.0, 3.43),
            (self.arm_elbow_x * sign, self.arm_elbow_y, 2.78),
            (self.arm_wrist_x * sign, self.arm_wrist_y, 2.18),
            (self.arm_hand_x * sign, self.arm_hand_y, 1.96),
            (self.arm_hand_x * sign, self.arm_hand_y - 0.02, 1.88),
        )

    def leg_points(
        self,
        side: PhysicalSide,
    ) -> tuple[Vector3, Vector3, Vector3, Vector3, Vector3]:
        sign = _side_sign(side)
        depth = self.left_leg_depth if side == "L" else self.right_leg_depth
        return (
            (self.leg_hip_x * sign, depth, 2.05),
            (self.leg_knee_x * sign, depth - 0.02, 1.18),
            (self.leg_ankle_x * sign, depth - 0.05, 0.48),
            (self.boot_x * sign, depth - 0.20, 0.22),
            (self.boot_x * sign, depth - 0.46, 0.18),
        )

    def assert_valid(self) -> None:
        if self.character_id != "human_warrior_m01":
            raise ValueError("Silhouette profile belongs to another character")
        if not re.fullmatch(r"v[0-9]{2}", self.revision):
            raise ValueError("Silhouette revision must use the vNN format")
        if not 0.0 < self.ribcage_depth_scale < 1.0:
            raise ValueError("Ribcage must be shallower than it is wide")
        if not (
            self.leg_hip_x < self.leg_knee_x < self.leg_ankle_x <= self.boot_x
        ):
            raise ValueError("Idle legs must form a stable outward stance")
        if self.left_leg_depth == self.right_leg_depth:
            raise ValueError("Idle legs must not overlap in true side views")
        if not (
            self.arm_shoulder_x
            < self.arm_elbow_x
            <= self.arm_wrist_x
            <= self.arm_hand_x
        ):
            raise ValueError("Arms must hang outward without crossing the torso")
        if not self.arm_hand_y < self.arm_wrist_y < self.arm_elbow_y <= 0.0:
            raise ValueError("Idle elbows and hands must bend toward the camera")
        left_extent = max(
            plate.location[0] + plate.scale[0]
            for plate in self.left_pauldron_plates
        )
        right_extent = abs(
            self.right_pauldron.location[0] - self.right_pauldron.scale[0]
        )
        if left_extent <= right_extent * 1.10:
            raise ValueError("The physical-left silver pauldron must stay larger")
        cloth_extent = max(
            abs(panel.location[0]) + panel.radius_bottom
            for panel in self.cloth_panels
        )
        if cloth_extent < left_extent * 0.75:
            raise ValueError("Lower cloth silhouette is too narrow for the approved idle")
        if any(
            panel.radius_bottom <= panel.radius_top
            for panel in self.cloth_panels
        ):
            raise ValueError("Back cloth must flare toward the feet")
        if any(
            scale <= 0.0
            for panel in self.cloth_panels
            for scale in panel.cross_section_scale
        ):
            raise ValueError("Back cloth cross-section scales must be positive")


HUMAN_WARRIOR_M01_SILHOUETTE_V03 = SilhouetteProfile(
    character_id="human_warrior_m01",
    revision="v03",
    pelvis_dimensions=(1.18, 0.54, 0.46),
    ribcage_radius_bottom=0.60,
    ribcage_radius_top=0.72,
    ribcage_depth=1.31,
    ribcage_depth_scale=0.78,
    chest_armor_dimensions=(1.22, 0.36, 1.02),
    chainmail_skirt_radius_bottom=0.72,
    chainmail_skirt_radius_top=0.55,
    belt_radius=0.63,
    arm_shoulder_x=0.66,
    arm_elbow_x=0.84,
    arm_wrist_x=0.87,
    arm_hand_x=0.87,
    arm_elbow_y=-0.07,
    arm_wrist_y=-0.31,
    arm_hand_y=-0.36,
    upper_arm_radius=0.21,
    forearm_radius=0.18,
    hand_scale=(0.19, 0.17, 0.23),
    left_pauldron_plates=(
        EllipsoidPart(
            "pauldron_left_plate_01",
            (0.73, -0.01, 3.49),
            (0.40, 0.38, 0.31),
        ),
        EllipsoidPart(
            "pauldron_left_plate_02",
            (0.82, -0.04, 3.39),
            (0.35, 0.34, 0.26),
        ),
        EllipsoidPart(
            "pauldron_left_plate_03",
            (0.88, -0.06, 3.29),
            (0.29, 0.29, 0.21),
        ),
    ),
    right_pauldron=EllipsoidPart(
        "pauldron_right_small",
        (-0.72, -0.01, 3.43),
        (0.31, 0.31, 0.25),
    ),
    leg_hip_x=0.42,
    leg_knee_x=0.49,
    leg_ankle_x=0.55,
    boot_x=0.58,
    left_leg_depth=-0.16,
    right_leg_depth=0.10,
    thigh_radius=0.27,
    shin_radius=0.25,
    knee_scale=(0.30, 0.27, 0.19),
    boot_dimensions=(0.52, 0.80, 0.40),
    boot_outward_degrees=9.0,
    cloth_panels=(
        ClothPanel(
            "L",
            (0.54, 0.36, 1.47),
            radius_bottom=0.52,
            radius_top=0.29,
            depth=1.74,
            cross_section_scale=(1.0, 1.40),
            bone_name="cloth.L",
        ),
        ClothPanel(
            "C",
            (0.0, 0.38, 1.42),
            radius_bottom=0.48,
            radius_top=0.31,
            depth=1.84,
            cross_section_scale=(1.0, 1.35),
            bone_name="cloth.C",
        ),
        ClothPanel(
            "R",
            (-0.54, 0.36, 1.47),
            radius_bottom=0.52,
            radius_top=0.29,
            depth=1.74,
            cross_section_scale=(1.0, 1.40),
            bone_name="cloth.R",
        ),
    ),
)


def load_silhouette_profile(character_id: str) -> SilhouetteProfile:
    if character_id != HUMAN_WARRIOR_M01_SILHOUETTE_V03.character_id:
        raise KeyError(f"No silhouette profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_SILHOUETTE_V03.assert_valid()
    return HUMAN_WARRIOR_M01_SILHOUETTE_V03


def _side_sign(side: PhysicalSide) -> float:
    if side == "L":
        return 1.0
    if side == "R":
        return -1.0
    raise ValueError(f"Unknown physical side: {side}")
