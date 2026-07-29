from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CombatIdleDownPoseV01:
    frame: int
    phase: str
    pelvis_x: float
    pelvis_z: float
    pelvis_roll_z_degrees: float
    spine_pitch_x_degrees: float
    chest_yaw_z_degrees: float
    head_yaw_z_degrees: float
    thigh_left_x_degrees: float
    thigh_right_x_degrees: float
    thigh_left_z_degrees: float
    thigh_right_z_degrees: float
    shin_left_x_degrees: float
    shin_right_x_degrees: float
    foot_left_x_degrees: float
    foot_right_x_degrees: float
    upper_arm_left_x_degrees: float
    upper_arm_left_z_degrees: float
    forearm_left_x_degrees: float
    forearm_left_z_degrees: float
    upper_arm_right_x_degrees: float
    upper_arm_right_z_degrees: float
    forearm_right_x_degrees: float
    forearm_right_z_degrees: float
    hand_right_x_degrees: float
    hand_right_z_degrees: float
    cloth_left_x_degrees: float
    cloth_center_x_degrees: float
    cloth_right_x_degrees: float

    def numeric_channels(self) -> tuple[float, ...]:
        return tuple(
            float(value)
            for name, value in self.__dict__.items()
            if name not in {"frame", "phase"}
        )


@dataclass(frozen=True)
class CombatIdleDownProfileV01:
    character_id: str
    revision: str
    pose_revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    weapon_id: str
    weapon_hand: str
    pose: CombatIdleDownPoseV01

    def assert_valid(self) -> None:
        if self.character_id != "human_warrior_m01":
            raise ValueError("Combat idle profile belongs to another character")
        if not re.fullmatch(r"v[0-9]{2}", self.revision):
            raise ValueError("Combat idle profile revision must use vNN")
        if not re.fullmatch(r"v[0-9]{2}", self.pose_revision):
            raise ValueError("Combat idle pose revision must use vNN")
        if self.animation_id != "combat_idle":
            raise ValueError("Combat idle animation_id drifted")
        if self.direction != "down":
            raise ValueError("The first combat idle candidate must face down")
        if self.fps != 1 or self.loop:
            raise ValueError("Static combat idle must be one non-looping frame")
        if self.weapon_id != "sword_01" or self.weapon_hand != "right":
            raise ValueError("The approved warrior must draw sword_01 in the right hand")
        if self.pose.frame != 1 or self.pose.phase != "guard_ready":
            raise ValueError("Combat idle v01 must contain the guard_ready frame")
        if not -0.10 <= self.pose.pelvis_z <= -0.03:
            raise ValueError("Combat idle center of gravity must be lower than normal idle")
        if not 3.0 <= self.pose.thigh_left_z_degrees <= 9.0:
            raise ValueError("Physical-left leg must widen the stance")
        if not -9.0 <= self.pose.thigh_right_z_degrees <= -3.0:
            raise ValueError("Physical-right leg must widen the stance")
        if not -35.0 <= self.pose.upper_arm_right_x_degrees <= -15.0:
            raise ValueError("Right weapon arm is outside the guarded ready range")
        if not -42.0 <= self.pose.forearm_right_x_degrees <= -20.0:
            raise ValueError("Right forearm must hold the sword below the face")
        if abs(self.pose.upper_arm_left_x_degrees) > 18.0:
            raise ValueError("Large left pauldron arm motion is too wide")
        if max(abs(value) for value in self.pose.numeric_channels()) > 42.0:
            raise ValueError("Combat idle pose exceeds the safe static-pose budget")


HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01 = CombatIdleDownProfileV01(
    character_id="human_warrior_m01",
    revision="v01",
    pose_revision="v01",
    animation_id="combat_idle",
    direction="down",
    fps=1,
    loop=False,
    weapon_id="sword_01",
    weapon_hand="right",
    pose=CombatIdleDownPoseV01(
        frame=1,
        phase="guard_ready",
        pelvis_x=0.02,
        pelvis_z=-0.065,
        pelvis_roll_z_degrees=2.0,
        spine_pitch_x_degrees=-4.0,
        chest_yaw_z_degrees=-8.0,
        head_yaw_z_degrees=5.0,
        thigh_left_x_degrees=6.0,
        thigh_right_x_degrees=4.0,
        thigh_left_z_degrees=5.0,
        thigh_right_z_degrees=-6.0,
        shin_left_x_degrees=-8.0,
        shin_right_x_degrees=-10.0,
        foot_left_x_degrees=3.0,
        foot_right_x_degrees=4.0,
        upper_arm_left_x_degrees=-8.0,
        upper_arm_left_z_degrees=8.0,
        forearm_left_x_degrees=-18.0,
        forearm_left_z_degrees=-5.0,
        upper_arm_right_x_degrees=-24.0,
        upper_arm_right_z_degrees=-10.0,
        forearm_right_x_degrees=-32.0,
        forearm_right_z_degrees=6.0,
        hand_right_x_degrees=-12.0,
        hand_right_z_degrees=-8.0,
        cloth_left_x_degrees=2.0,
        cloth_center_x_degrees=0.0,
        cloth_right_x_degrees=-2.0,
    ),
)


def load_combat_idle_down_profile_v01(
    character_id: str,
) -> CombatIdleDownProfileV01:
    if character_id != HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01.character_id:
        raise KeyError(f"No combat_idle_down v01 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01.assert_valid()
    return HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01
