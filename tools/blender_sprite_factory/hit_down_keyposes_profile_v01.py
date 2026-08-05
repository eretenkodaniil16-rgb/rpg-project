from __future__ import annotations

from dataclasses import dataclass


HIT_DOWN_KEYPOSE_FRAME_ORDER = (1, 2, 3, 4)
HIT_DOWN_KEYPOSE_PHASE_ORDER = (
    "guard",
    "impact",
    "recoil_peak",
    "recovery",
)
HIT_DOWN_KEYPOSE_FPS = 8
MAX_ROTATION_DELTA_DEGREES = 18.0
MAX_PELVIS_TRANSLATION = 0.05


@dataclass(frozen=True)
class HitDownPoseDeltaV01:
    frame: int
    phase: str
    pelvis_x: float = 0.0
    pelvis_y: float = 0.0
    pelvis_z: float = 0.0
    pelvis_roll_z_degrees: float = 0.0
    spine_pitch_x_degrees: float = 0.0
    chest_yaw_z_degrees: float = 0.0
    head_pitch_x_degrees: float = 0.0
    head_yaw_z_degrees: float = 0.0
    thigh_left_x_degrees: float = 0.0
    thigh_right_x_degrees: float = 0.0
    shin_left_x_degrees: float = 0.0
    shin_right_x_degrees: float = 0.0
    foot_left_x_degrees: float = 0.0
    foot_right_x_degrees: float = 0.0
    upper_arm_left_x_degrees: float = 0.0
    upper_arm_left_y_degrees: float = 0.0
    upper_arm_left_z_degrees: float = 0.0
    forearm_left_x_degrees: float = 0.0
    forearm_left_y_degrees: float = 0.0
    forearm_left_z_degrees: float = 0.0
    hand_left_x_degrees: float = 0.0
    hand_left_y_degrees: float = 0.0
    hand_left_z_degrees: float = 0.0
    upper_arm_right_x_degrees: float = 0.0
    upper_arm_right_y_degrees: float = 0.0
    upper_arm_right_z_degrees: float = 0.0
    forearm_right_x_degrees: float = 0.0
    forearm_right_y_degrees: float = 0.0
    forearm_right_z_degrees: float = 0.0
    hand_right_x_degrees: float = 0.0
    hand_right_y_degrees: float = 0.0
    hand_right_z_degrees: float = 0.0
    cloth_left_x_degrees: float = 0.0
    cloth_center_x_degrees: float = 0.0
    cloth_right_x_degrees: float = 0.0

    def translation_deltas(self) -> tuple[float, ...]:
        return (self.pelvis_x, self.pelvis_y, self.pelvis_z)

    def rotation_deltas(self) -> tuple[float, ...]:
        return (
            self.pelvis_roll_z_degrees,
            self.spine_pitch_x_degrees,
            self.chest_yaw_z_degrees,
            self.head_pitch_x_degrees,
            self.head_yaw_z_degrees,
            self.thigh_left_x_degrees,
            self.thigh_right_x_degrees,
            self.shin_left_x_degrees,
            self.shin_right_x_degrees,
            self.foot_left_x_degrees,
            self.foot_right_x_degrees,
            self.upper_arm_left_x_degrees,
            self.upper_arm_left_y_degrees,
            self.upper_arm_left_z_degrees,
            self.forearm_left_x_degrees,
            self.forearm_left_y_degrees,
            self.forearm_left_z_degrees,
            self.hand_left_x_degrees,
            self.hand_left_y_degrees,
            self.hand_left_z_degrees,
            self.upper_arm_right_x_degrees,
            self.upper_arm_right_y_degrees,
            self.upper_arm_right_z_degrees,
            self.forearm_right_x_degrees,
            self.forearm_right_y_degrees,
            self.forearm_right_z_degrees,
            self.hand_right_x_degrees,
            self.hand_right_y_degrees,
            self.hand_right_z_degrees,
            self.cloth_left_x_degrees,
            self.cloth_center_x_degrees,
            self.cloth_right_x_degrees,
        )


@dataclass(frozen=True)
class HitDownKeyposesProfileV01:
    character_id: str
    revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    stance_variant_id: str
    stance_source_revision: str
    weapon_cycle_id: str
    incoming_direction: str
    poses: tuple[HitDownPoseDeltaV01, ...]
    appearance_revision: str
    head_revision: str
    proxy_revision: str


HIT_DOWN_ONEHAND_POSES_V01 = (
    HitDownPoseDeltaV01(frame=1, phase="guard"),
    HitDownPoseDeltaV01(
        frame=2,
        phase="impact",
        pelvis_y=0.018,
        pelvis_z=-0.006,
        pelvis_roll_z_degrees=-1.5,
        spine_pitch_x_degrees=-7.0,
        chest_yaw_z_degrees=3.0,
        head_pitch_x_degrees=-8.0,
        head_yaw_z_degrees=-4.0,
        thigh_left_x_degrees=-1.5,
        thigh_right_x_degrees=-1.0,
        shin_left_x_degrees=1.5,
        shin_right_x_degrees=1.0,
        upper_arm_left_x_degrees=5.0,
        upper_arm_left_y_degrees=-2.0,
        upper_arm_left_z_degrees=5.0,
        forearm_left_x_degrees=5.0,
        forearm_left_z_degrees=4.0,
        hand_left_z_degrees=3.0,
        upper_arm_right_x_degrees=4.0,
        upper_arm_right_y_degrees=1.5,
        upper_arm_right_z_degrees=-3.0,
        forearm_right_x_degrees=5.0,
        forearm_right_z_degrees=-3.0,
        hand_right_x_degrees=4.0,
        hand_right_z_degrees=-2.0,
        cloth_left_x_degrees=-3.0,
        cloth_center_x_degrees=-2.0,
        cloth_right_x_degrees=-2.5,
    ),
    HitDownPoseDeltaV01(
        frame=3,
        phase="recoil_peak",
        pelvis_y=0.036,
        pelvis_z=-0.012,
        pelvis_roll_z_degrees=-2.5,
        spine_pitch_x_degrees=-12.0,
        chest_yaw_z_degrees=5.0,
        head_pitch_x_degrees=-14.0,
        head_yaw_z_degrees=-7.0,
        thigh_left_x_degrees=-2.5,
        thigh_right_x_degrees=-2.0,
        shin_left_x_degrees=2.5,
        shin_right_x_degrees=2.0,
        foot_left_x_degrees=-1.0,
        foot_right_x_degrees=-1.0,
        upper_arm_left_x_degrees=9.0,
        upper_arm_left_y_degrees=-3.5,
        upper_arm_left_z_degrees=8.0,
        forearm_left_x_degrees=9.0,
        forearm_left_z_degrees=7.0,
        hand_left_x_degrees=3.0,
        hand_left_z_degrees=5.0,
        upper_arm_right_x_degrees=7.0,
        upper_arm_right_y_degrees=2.5,
        upper_arm_right_z_degrees=-5.0,
        forearm_right_x_degrees=8.0,
        forearm_right_z_degrees=-5.0,
        hand_right_x_degrees=7.0,
        hand_right_z_degrees=-4.0,
        cloth_left_x_degrees=-5.0,
        cloth_center_x_degrees=-4.0,
        cloth_right_x_degrees=-4.5,
    ),
    HitDownPoseDeltaV01(
        frame=4,
        phase="recovery",
        pelvis_y=0.012,
        pelvis_z=-0.004,
        pelvis_roll_z_degrees=-0.8,
        spine_pitch_x_degrees=-4.0,
        chest_yaw_z_degrees=1.5,
        head_pitch_x_degrees=-5.0,
        head_yaw_z_degrees=-2.0,
        thigh_left_x_degrees=-0.8,
        thigh_right_x_degrees=-0.6,
        shin_left_x_degrees=0.8,
        shin_right_x_degrees=0.6,
        upper_arm_left_x_degrees=3.0,
        upper_arm_left_z_degrees=2.5,
        forearm_left_x_degrees=3.0,
        forearm_left_z_degrees=2.0,
        upper_arm_right_x_degrees=2.5,
        upper_arm_right_z_degrees=-2.0,
        forearm_right_x_degrees=3.0,
        forearm_right_z_degrees=-2.0,
        hand_right_x_degrees=2.0,
        hand_right_z_degrees=-1.5,
        cloth_left_x_degrees=-1.5,
        cloth_center_x_degrees=-1.0,
        cloth_right_x_degrees=-1.5,
    ),
)


HUMAN_WARRIOR_M01_HIT_DOWN_KEYPOSES_V01 = HitDownKeyposesProfileV01(
    character_id="human_warrior_m01",
    revision="hit_down_keyposes_v01_pass02",
    animation_id="hit_01_onehand_down_keyposes_v01",
    direction="down",
    fps=HIT_DOWN_KEYPOSE_FPS,
    loop=False,
    frame_order=HIT_DOWN_KEYPOSE_FRAME_ORDER,
    phase_order=HIT_DOWN_KEYPOSE_PHASE_ORDER,
    stance_variant_id="onehand_ready",
    stance_source_revision="v09_artist_approved",
    weapon_cycle_id="onehand_ready",
    incoming_direction="front",
    poses=HIT_DOWN_ONEHAND_POSES_V01,
    appearance_revision="v03",
    head_revision="v22",
    proxy_revision="v25",
)


def load_hit_down_keyposes_profile_v01(
    character_id: str,
) -> HitDownKeyposesProfileV01:
    profile = HUMAN_WARRIOR_M01_HIT_DOWN_KEYPOSES_V01
    if character_id != profile.character_id:
        raise KeyError(f"No hit down v01 profile for character_id={character_id}")
    if profile.direction != "down" or profile.loop:
        raise ValueError("Hit down v01 identity drifted")
    if profile.frame_order != HIT_DOWN_KEYPOSE_FRAME_ORDER:
        raise ValueError("Hit down v01 frame order drifted")
    if profile.phase_order != HIT_DOWN_KEYPOSE_PHASE_ORDER:
        raise ValueError("Hit down v01 phase order drifted")
    if tuple(pose.frame for pose in profile.poses) != profile.frame_order:
        raise ValueError("Hit down v01 pose frames drifted")
    if tuple(pose.phase for pose in profile.poses) != profile.phase_order:
        raise ValueError("Hit down v01 pose phases drifted")
    if any(
        abs(value) > MAX_PELVIS_TRANSLATION
        for pose in profile.poses
        for value in pose.translation_deltas()
    ):
        raise ValueError("Hit down v01 pelvis translation exceeds review budget")
    if any(
        abs(value) > MAX_ROTATION_DELTA_DEGREES
        for pose in profile.poses
        for value in pose.rotation_deltas()
    ):
        raise ValueError("Hit down v01 rotation exceeds review budget")
    return profile
