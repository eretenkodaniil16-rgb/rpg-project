from __future__ import annotations

from dataclasses import dataclass


DEATH_DOWN_KEYPOSE_FRAME_ORDER = (1, 2, 3, 4, 5)
DEATH_DOWN_KEYPOSE_PHASE_ORDER = (
    "guard",
    "balance_break",
    "knee_drop",
    "ground_impact",
    "final",
)
DEATH_DOWN_KEYPOSE_FPS = 8
MAX_ROTATION_DELTA_DEGREES = 90.0
MAX_PELVIS_TRANSLATION = 0.65


@dataclass(frozen=True)
class DeathDownPoseDeltaV01:
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
class DeathDownKeyposesProfileV01:
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
    fall_side: str
    final_pose_persistent: bool
    weapon_release_deferred: bool
    poses: tuple[DeathDownPoseDeltaV01, ...]
    appearance_revision: str
    head_revision: str
    proxy_revision: str


HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01 = DeathDownKeyposesProfileV01(
    character_id="human_warrior_m01",
    revision="death_down_keyposes_v01_pass01",
    animation_id="death_01_onehand_down_keyposes_v01",
    direction="down",
    fps=DEATH_DOWN_KEYPOSE_FPS,
    loop=False,
    frame_order=DEATH_DOWN_KEYPOSE_FRAME_ORDER,
    phase_order=DEATH_DOWN_KEYPOSE_PHASE_ORDER,
    stance_variant_id="onehand_ready",
    stance_source_revision="v09_artist_approved",
    weapon_cycle_id="onehand_ready",
    fall_side="character_right_back_diagonal",
    final_pose_persistent=True,
    weapon_release_deferred=True,
    poses=(
        DeathDownPoseDeltaV01(frame=1, phase="guard"),
        DeathDownPoseDeltaV01(
            frame=2,
            phase="balance_break",
            pelvis_y=0.035,
            pelvis_z=-0.035,
            pelvis_roll_z_degrees=-8.0,
            spine_pitch_x_degrees=-15.0,
            chest_yaw_z_degrees=-7.0,
            head_pitch_x_degrees=-12.0,
            head_yaw_z_degrees=4.0,
            thigh_left_x_degrees=-7.0,
            thigh_right_x_degrees=-3.0,
            shin_left_x_degrees=8.0,
            shin_right_x_degrees=4.0,
            upper_arm_left_x_degrees=7.0,
            upper_arm_left_y_degrees=-3.0,
            upper_arm_left_z_degrees=10.0,
            forearm_left_x_degrees=8.0,
            forearm_left_z_degrees=6.0,
            upper_arm_right_x_degrees=6.0,
            upper_arm_right_y_degrees=2.0,
            upper_arm_right_z_degrees=-7.0,
            forearm_right_x_degrees=7.0,
            forearm_right_z_degrees=-5.0,
            hand_right_x_degrees=4.0,
            cloth_left_x_degrees=-5.0,
            cloth_center_x_degrees=-3.0,
            cloth_right_x_degrees=-4.0,
        ),
        DeathDownPoseDeltaV01(
            frame=3,
            phase="knee_drop",
            pelvis_y=0.095,
            pelvis_z=-0.185,
            pelvis_roll_z_degrees=-19.0,
            spine_pitch_x_degrees=-31.0,
            chest_yaw_z_degrees=-16.0,
            head_pitch_x_degrees=-27.0,
            head_yaw_z_degrees=7.0,
            thigh_left_x_degrees=-27.0,
            thigh_right_x_degrees=-13.0,
            shin_left_x_degrees=36.0,
            shin_right_x_degrees=21.0,
            foot_left_x_degrees=-8.0,
            foot_right_x_degrees=-4.0,
            upper_arm_left_x_degrees=17.0,
            upper_arm_left_y_degrees=-7.0,
            upper_arm_left_z_degrees=23.0,
            forearm_left_x_degrees=19.0,
            forearm_left_z_degrees=13.0,
            hand_left_z_degrees=7.0,
            upper_arm_right_x_degrees=14.0,
            upper_arm_right_y_degrees=5.0,
            upper_arm_right_z_degrees=-16.0,
            forearm_right_x_degrees=17.0,
            forearm_right_z_degrees=-12.0,
            hand_right_x_degrees=10.0,
            hand_right_z_degrees=-6.0,
            cloth_left_x_degrees=-13.0,
            cloth_center_x_degrees=-9.0,
            cloth_right_x_degrees=-11.0,
        ),
        DeathDownPoseDeltaV01(
            frame=4,
            phase="ground_impact",
            pelvis_y=0.155,
            pelvis_z=-0.455,
            pelvis_roll_z_degrees=-43.0,
            spine_pitch_x_degrees=-57.0,
            chest_yaw_z_degrees=-29.0,
            head_pitch_x_degrees=-55.0,
            head_yaw_z_degrees=11.0,
            thigh_left_x_degrees=-44.0,
            thigh_right_x_degrees=-30.0,
            shin_left_x_degrees=64.0,
            shin_right_x_degrees=46.0,
            foot_left_x_degrees=-18.0,
            foot_right_x_degrees=-12.0,
            upper_arm_left_x_degrees=31.0,
            upper_arm_left_y_degrees=-13.0,
            upper_arm_left_z_degrees=39.0,
            forearm_left_x_degrees=34.0,
            forearm_left_z_degrees=25.0,
            hand_left_x_degrees=13.0,
            hand_left_z_degrees=15.0,
            upper_arm_right_x_degrees=27.0,
            upper_arm_right_y_degrees=9.0,
            upper_arm_right_z_degrees=-31.0,
            forearm_right_x_degrees=31.0,
            forearm_right_z_degrees=-22.0,
            hand_right_x_degrees=22.0,
            hand_right_z_degrees=-14.0,
            cloth_left_x_degrees=-27.0,
            cloth_center_x_degrees=-20.0,
            cloth_right_x_degrees=-24.0,
        ),
        DeathDownPoseDeltaV01(
            frame=5,
            phase="final",
            pelvis_y=0.175,
            pelvis_z=-0.535,
            pelvis_roll_z_degrees=-52.0,
            spine_pitch_x_degrees=-68.0,
            chest_yaw_z_degrees=-34.0,
            head_pitch_x_degrees=-68.0,
            head_yaw_z_degrees=12.0,
            thigh_left_x_degrees=-51.0,
            thigh_right_x_degrees=-38.0,
            shin_left_x_degrees=72.0,
            shin_right_x_degrees=51.0,
            foot_left_x_degrees=-22.0,
            foot_right_x_degrees=-16.0,
            upper_arm_left_x_degrees=37.0,
            upper_arm_left_y_degrees=-15.0,
            upper_arm_left_z_degrees=45.0,
            forearm_left_x_degrees=39.0,
            forearm_left_z_degrees=29.0,
            hand_left_x_degrees=17.0,
            hand_left_z_degrees=18.0,
            upper_arm_right_x_degrees=32.0,
            upper_arm_right_y_degrees=11.0,
            upper_arm_right_z_degrees=-36.0,
            forearm_right_x_degrees=36.0,
            forearm_right_z_degrees=-26.0,
            hand_right_x_degrees=25.0,
            hand_right_z_degrees=-17.0,
            cloth_left_x_degrees=-31.0,
            cloth_center_x_degrees=-23.0,
            cloth_right_x_degrees=-28.0,
        ),
    ),
    appearance_revision="v03",
    head_revision="v22",
    proxy_revision="v25",
)


def load_death_down_keyposes_profile_v01(
    character_id: str,
) -> DeathDownKeyposesProfileV01:
    profile = HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01
    if character_id != profile.character_id:
        raise KeyError(f"No death down v01 profile for character_id={character_id}")
    if profile.direction != "down" or profile.loop:
        raise ValueError("Death down v01 identity drifted")
    if profile.frame_order != DEATH_DOWN_KEYPOSE_FRAME_ORDER:
        raise ValueError("Death down v01 frame order drifted")
    if profile.phase_order != DEATH_DOWN_KEYPOSE_PHASE_ORDER:
        raise ValueError("Death down v01 phase order drifted")
    if tuple(pose.frame for pose in profile.poses) != profile.frame_order:
        raise ValueError("Death down v01 pose frames drifted")
    if tuple(pose.phase for pose in profile.poses) != profile.phase_order:
        raise ValueError("Death down v01 pose phases drifted")
    if not profile.final_pose_persistent:
        raise ValueError("Death down v01 final pose must persist")
    if not profile.weapon_release_deferred:
        raise ValueError("Death down v01 must isolate body motion before weapon release")
    if any(
        abs(value) > MAX_PELVIS_TRANSLATION
        for pose in profile.poses
        for value in pose.translation_deltas()
    ):
        raise ValueError("Death down v01 pelvis translation exceeds review budget")
    if any(
        abs(value) > MAX_ROTATION_DELTA_DEGREES
        for pose in profile.poses
        for value in pose.rotation_deltas()
    ):
        raise ValueError("Death down v01 rotation exceeds review budget")
    return profile
