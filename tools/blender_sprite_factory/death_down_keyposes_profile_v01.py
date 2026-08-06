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
DEATH_DOWN_VARIANT_IDS = (
    "death_01_base",
    "death_02_base",
    "death_03_base",
)
MAX_ROTATION_DELTA_DEGREES = 90.0
MAX_PELVIS_TRANSLATION = 0.70


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
    death_variant_id: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    source_stance_variant_id: str
    source_stance_revision: str
    weapon_visible: bool
    fall_side: str
    final_pose_persistent: bool
    gore_mode: str
    detached_part_id: str | None
    detachment_frame: int | None
    poses: tuple[DeathDownPoseDeltaV01, ...]
    appearance_revision: str
    head_revision: str
    proxy_revision: str


DEATH_01_BASE_POSES_V01 = (
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
        pelvis_x=0.025,
        pelvis_y=0.160,
        pelvis_z=-0.490,
        pelvis_roll_z_degrees=-55.0,
        spine_pitch_x_degrees=-62.0,
        chest_yaw_z_degrees=-42.0,
        head_pitch_x_degrees=-62.0,
        head_yaw_z_degrees=18.0,
        thigh_left_x_degrees=-58.0,
        thigh_right_x_degrees=-22.0,
        shin_left_x_degrees=80.0,
        shin_right_x_degrees=35.0,
        foot_left_x_degrees=-30.0,
        foot_right_x_degrees=-5.0,
        upper_arm_left_x_degrees=45.0,
        upper_arm_left_y_degrees=-18.0,
        upper_arm_left_z_degrees=58.0,
        forearm_left_x_degrees=52.0,
        forearm_left_z_degrees=35.0,
        hand_left_x_degrees=25.0,
        hand_left_z_degrees=25.0,
        upper_arm_right_x_degrees=20.0,
        upper_arm_right_y_degrees=10.0,
        upper_arm_right_z_degrees=-48.0,
        forearm_right_x_degrees=26.0,
        forearm_right_z_degrees=-32.0,
        hand_right_x_degrees=18.0,
        hand_right_z_degrees=-20.0,
        cloth_left_x_degrees=-34.0,
        cloth_center_x_degrees=-26.0,
        cloth_right_x_degrees=-30.0,
    ),
    DeathDownPoseDeltaV01(
        frame=5,
        phase="final",
        pelvis_x=0.040,
        pelvis_y=0.180,
        pelvis_z=-0.600,
        pelvis_roll_z_degrees=-68.0,
        spine_pitch_x_degrees=-74.0,
        chest_yaw_z_degrees=-52.0,
        head_pitch_x_degrees=-78.0,
        head_yaw_z_degrees=22.0,
        thigh_left_x_degrees=-72.0,
        thigh_right_x_degrees=-28.0,
        shin_left_x_degrees=86.0,
        shin_right_x_degrees=38.0,
        foot_left_x_degrees=-34.0,
        foot_right_x_degrees=-8.0,
        upper_arm_left_x_degrees=54.0,
        upper_arm_left_y_degrees=-22.0,
        upper_arm_left_z_degrees=68.0,
        forearm_left_x_degrees=60.0,
        forearm_left_z_degrees=42.0,
        hand_left_x_degrees=30.0,
        hand_left_z_degrees=28.0,
        upper_arm_right_x_degrees=16.0,
        upper_arm_right_y_degrees=12.0,
        upper_arm_right_z_degrees=-58.0,
        forearm_right_x_degrees=22.0,
        forearm_right_z_degrees=-38.0,
        hand_right_x_degrees=14.0,
        hand_right_z_degrees=-24.0,
        cloth_left_x_degrees=-40.0,
        cloth_center_x_degrees=-31.0,
        cloth_right_x_degrees=-36.0,
    ),
)


DEATH_02_BASE_POSES_V01 = (
    DeathDownPoseDeltaV01(frame=1, phase="guard"),
    DeathDownPoseDeltaV01(
        frame=2,
        phase="balance_break",
        pelvis_x=-0.025,
        pelvis_y=-0.020,
        pelvis_z=-0.050,
        pelvis_roll_z_degrees=9.0,
        spine_pitch_x_degrees=18.0,
        chest_yaw_z_degrees=11.0,
        head_pitch_x_degrees=20.0,
        head_yaw_z_degrees=-6.0,
        thigh_left_x_degrees=-4.0,
        thigh_right_x_degrees=-9.0,
        shin_left_x_degrees=5.0,
        shin_right_x_degrees=11.0,
        upper_arm_left_x_degrees=-4.0,
        upper_arm_left_y_degrees=4.0,
        upper_arm_left_z_degrees=-13.0,
        forearm_left_x_degrees=8.0,
        forearm_left_z_degrees=-8.0,
        upper_arm_right_x_degrees=11.0,
        upper_arm_right_y_degrees=-3.0,
        upper_arm_right_z_degrees=15.0,
        forearm_right_x_degrees=13.0,
        forearm_right_z_degrees=9.0,
        cloth_left_x_degrees=5.0,
        cloth_center_x_degrees=4.0,
        cloth_right_x_degrees=6.0,
    ),
    DeathDownPoseDeltaV01(
        frame=3,
        phase="knee_drop",
        pelvis_x=-0.070,
        pelvis_y=-0.060,
        pelvis_z=-0.230,
        pelvis_roll_z_degrees=26.0,
        spine_pitch_x_degrees=38.0,
        chest_yaw_z_degrees=24.0,
        head_pitch_x_degrees=44.0,
        head_yaw_z_degrees=-12.0,
        thigh_left_x_degrees=-15.0,
        thigh_right_x_degrees=-34.0,
        shin_left_x_degrees=22.0,
        shin_right_x_degrees=48.0,
        foot_left_x_degrees=-4.0,
        foot_right_x_degrees=-14.0,
        upper_arm_left_x_degrees=-12.0,
        upper_arm_left_y_degrees=9.0,
        upper_arm_left_z_degrees=-30.0,
        forearm_left_x_degrees=18.0,
        forearm_left_z_degrees=-19.0,
        hand_left_x_degrees=8.0,
        upper_arm_right_x_degrees=25.0,
        upper_arm_right_y_degrees=-7.0,
        upper_arm_right_z_degrees=34.0,
        forearm_right_x_degrees=29.0,
        forearm_right_z_degrees=21.0,
        hand_right_x_degrees=13.0,
        cloth_left_x_degrees=14.0,
        cloth_center_x_degrees=11.0,
        cloth_right_x_degrees=16.0,
    ),
    DeathDownPoseDeltaV01(
        frame=4,
        phase="ground_impact",
        pelvis_x=-0.120,
        pelvis_y=-0.110,
        pelvis_z=-0.500,
        pelvis_roll_z_degrees=58.0,
        spine_pitch_x_degrees=68.0,
        chest_yaw_z_degrees=50.0,
        head_pitch_x_degrees=72.0,
        head_yaw_z_degrees=-22.0,
        thigh_left_x_degrees=-24.0,
        thigh_right_x_degrees=-64.0,
        shin_left_x_degrees=39.0,
        shin_right_x_degrees=82.0,
        foot_left_x_degrees=-10.0,
        foot_right_x_degrees=-31.0,
        upper_arm_left_x_degrees=-22.0,
        upper_arm_left_y_degrees=17.0,
        upper_arm_left_z_degrees=-54.0,
        forearm_left_x_degrees=31.0,
        forearm_left_z_degrees=-34.0,
        hand_left_x_degrees=16.0,
        hand_left_z_degrees=-10.0,
        upper_arm_right_x_degrees=42.0,
        upper_arm_right_y_degrees=-13.0,
        upper_arm_right_z_degrees=59.0,
        forearm_right_x_degrees=47.0,
        forearm_right_z_degrees=39.0,
        hand_right_x_degrees=24.0,
        hand_right_z_degrees=13.0,
        cloth_left_x_degrees=29.0,
        cloth_center_x_degrees=23.0,
        cloth_right_x_degrees=33.0,
    ),
    DeathDownPoseDeltaV01(
        frame=5,
        phase="final",
        pelvis_x=-0.145,
        pelvis_y=-0.145,
        pelvis_z=-0.620,
        pelvis_roll_z_degrees=76.0,
        spine_pitch_x_degrees=82.0,
        chest_yaw_z_degrees=61.0,
        head_pitch_x_degrees=86.0,
        head_yaw_z_degrees=-29.0,
        thigh_left_x_degrees=-31.0,
        thigh_right_x_degrees=-78.0,
        shin_left_x_degrees=48.0,
        shin_right_x_degrees=88.0,
        foot_left_x_degrees=-14.0,
        foot_right_x_degrees=-38.0,
        upper_arm_left_x_degrees=-31.0,
        upper_arm_left_y_degrees=22.0,
        upper_arm_left_z_degrees=-67.0,
        forearm_left_x_degrees=40.0,
        forearm_left_z_degrees=-43.0,
        hand_left_x_degrees=22.0,
        hand_left_z_degrees=-15.0,
        upper_arm_right_x_degrees=52.0,
        upper_arm_right_y_degrees=-17.0,
        upper_arm_right_z_degrees=72.0,
        forearm_right_x_degrees=57.0,
        forearm_right_z_degrees=48.0,
        hand_right_x_degrees=31.0,
        hand_right_z_degrees=18.0,
        cloth_left_x_degrees=38.0,
        cloth_center_x_degrees=30.0,
        cloth_right_x_degrees=42.0,
    ),
)


DEATH_03_BASE_POSES_V01 = (
    DeathDownPoseDeltaV01(frame=1, phase="guard"),
    DeathDownPoseDeltaV01(
        frame=2,
        phase="balance_break",
        pelvis_x=-0.010,
        pelvis_y=0.015,
        pelvis_z=-0.035,
        pelvis_roll_z_degrees=-4.0,
        spine_pitch_x_degrees=8.0,
        chest_yaw_z_degrees=-10.0,
        head_pitch_x_degrees=12.0,
        head_yaw_z_degrees=5.0,
        thigh_left_x_degrees=-8.0,
        thigh_right_x_degrees=-11.0,
        shin_left_x_degrees=12.0,
        shin_right_x_degrees=15.0,
        upper_arm_left_x_degrees=-7.0,
        upper_arm_left_y_degrees=6.0,
        upper_arm_left_z_degrees=-22.0,
        forearm_left_x_degrees=13.0,
        forearm_left_z_degrees=-12.0,
        upper_arm_right_x_degrees=-5.0,
        upper_arm_right_y_degrees=-6.0,
        upper_arm_right_z_degrees=24.0,
        forearm_right_x_degrees=15.0,
        forearm_right_z_degrees=14.0,
        cloth_left_x_degrees=3.0,
        cloth_center_x_degrees=2.0,
        cloth_right_x_degrees=4.0,
    ),
    DeathDownPoseDeltaV01(
        frame=3,
        phase="knee_drop",
        pelvis_x=-0.080,
        pelvis_y=0.040,
        pelvis_z=-0.220,
        pelvis_roll_z_degrees=-18.0,
        spine_pitch_x_degrees=12.0,
        chest_yaw_z_degrees=-22.0,
        head_pitch_x_degrees=18.0,
        head_yaw_z_degrees=10.0,
        thigh_left_x_degrees=-38.0,
        thigh_right_x_degrees=-44.0,
        shin_left_x_degrees=56.0,
        shin_right_x_degrees=63.0,
        foot_left_x_degrees=-15.0,
        foot_right_x_degrees=-18.0,
        upper_arm_left_x_degrees=-18.0,
        upper_arm_left_y_degrees=13.0,
        upper_arm_left_z_degrees=-47.0,
        forearm_left_x_degrees=30.0,
        forearm_left_z_degrees=-27.0,
        hand_left_x_degrees=14.0,
        upper_arm_right_x_degrees=-15.0,
        upper_arm_right_y_degrees=-13.0,
        upper_arm_right_z_degrees=49.0,
        forearm_right_x_degrees=32.0,
        forearm_right_z_degrees=29.0,
        hand_right_x_degrees=16.0,
        cloth_left_x_degrees=10.0,
        cloth_center_x_degrees=8.0,
        cloth_right_x_degrees=12.0,
    ),
    DeathDownPoseDeltaV01(
        frame=4,
        phase="ground_impact",
        pelvis_x=-0.200,
        pelvis_y=0.080,
        pelvis_z=-0.520,
        pelvis_roll_z_degrees=-48.0,
        spine_pitch_x_degrees=18.0,
        chest_yaw_z_degrees=-34.0,
        head_pitch_x_degrees=24.0,
        head_yaw_z_degrees=16.0,
        thigh_left_x_degrees=-62.0,
        thigh_right_x_degrees=-53.0,
        shin_left_x_degrees=82.0,
        shin_right_x_degrees=73.0,
        foot_left_x_degrees=-31.0,
        foot_right_x_degrees=-25.0,
        upper_arm_left_x_degrees=-34.0,
        upper_arm_left_y_degrees=22.0,
        upper_arm_left_z_degrees=-69.0,
        forearm_left_x_degrees=47.0,
        forearm_left_z_degrees=-42.0,
        hand_left_x_degrees=24.0,
        hand_left_z_degrees=-16.0,
        upper_arm_right_x_degrees=-28.0,
        upper_arm_right_y_degrees=-21.0,
        upper_arm_right_z_degrees=72.0,
        forearm_right_x_degrees=49.0,
        forearm_right_z_degrees=44.0,
        hand_right_x_degrees=26.0,
        hand_right_z_degrees=17.0,
        cloth_left_x_degrees=22.0,
        cloth_center_x_degrees=17.0,
        cloth_right_x_degrees=25.0,
    ),
    DeathDownPoseDeltaV01(
        frame=5,
        phase="final",
        pelvis_x=-0.260,
        pelvis_y=0.100,
        pelvis_z=-0.640,
        pelvis_roll_z_degrees=-67.0,
        spine_pitch_x_degrees=24.0,
        chest_yaw_z_degrees=-42.0,
        head_pitch_x_degrees=31.0,
        head_yaw_z_degrees=21.0,
        thigh_left_x_degrees=-78.0,
        thigh_right_x_degrees=-69.0,
        shin_left_x_degrees=89.0,
        shin_right_x_degrees=84.0,
        foot_left_x_degrees=-39.0,
        foot_right_x_degrees=-34.0,
        upper_arm_left_x_degrees=-45.0,
        upper_arm_left_y_degrees=28.0,
        upper_arm_left_z_degrees=-81.0,
        forearm_left_x_degrees=58.0,
        forearm_left_z_degrees=-52.0,
        hand_left_x_degrees=31.0,
        hand_left_z_degrees=-22.0,
        upper_arm_right_x_degrees=-39.0,
        upper_arm_right_y_degrees=-27.0,
        upper_arm_right_z_degrees=84.0,
        forearm_right_x_degrees=61.0,
        forearm_right_z_degrees=55.0,
        hand_right_x_degrees=34.0,
        hand_right_z_degrees=23.0,
        cloth_left_x_degrees=31.0,
        cloth_center_x_degrees=24.0,
        cloth_right_x_degrees=35.0,
    ),
)


HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01 = (
    DeathDownKeyposesProfileV01(
        character_id="human_warrior_m01",
        revision="death_01_base_down_keyposes_v01_pass02_approved",
        death_variant_id="death_01_base",
        animation_id="death_01_base_down_keyposes_v01",
        direction="down",
        fps=DEATH_DOWN_KEYPOSE_FPS,
        loop=False,
        frame_order=DEATH_DOWN_KEYPOSE_FRAME_ORDER,
        phase_order=DEATH_DOWN_KEYPOSE_PHASE_ORDER,
        source_stance_variant_id="onehand_ready",
        source_stance_revision="v09_artist_approved_source_only",
        weapon_visible=False,
        fall_side="character_right_back_diagonal",
        final_pose_persistent=True,
        gore_mode="none",
        detached_part_id=None,
        detachment_frame=None,
        poses=DEATH_01_BASE_POSES_V01,
        appearance_revision="v03",
        head_revision="v22",
        proxy_revision="v25",
    ),
    DeathDownKeyposesProfileV01(
        character_id="human_warrior_m01",
        revision="death_02_base_down_keyposes_v01_pass01",
        death_variant_id="death_02_base",
        animation_id="death_02_base_down_keyposes_v01",
        direction="down",
        fps=DEATH_DOWN_KEYPOSE_FPS,
        loop=False,
        frame_order=DEATH_DOWN_KEYPOSE_FRAME_ORDER,
        phase_order=DEATH_DOWN_KEYPOSE_PHASE_ORDER,
        source_stance_variant_id="onehand_ready",
        source_stance_revision="v09_artist_approved_source_only",
        weapon_visible=False,
        fall_side="character_left_forward_diagonal",
        final_pose_persistent=True,
        gore_mode="severe_impact",
        detached_part_id=None,
        detachment_frame=None,
        poses=DEATH_02_BASE_POSES_V01,
        appearance_revision="v03",
        head_revision="v22",
        proxy_revision="v25",
    ),
    DeathDownKeyposesProfileV01(
        character_id="human_warrior_m01",
        revision="death_03_base_down_keyposes_v01_pass02_waist_separation",
        death_variant_id="death_03_base",
        animation_id="death_03_base_down_keyposes_v01",
        direction="down",
        fps=DEATH_DOWN_KEYPOSE_FPS,
        loop=False,
        frame_order=DEATH_DOWN_KEYPOSE_FRAME_ORDER,
        phase_order=DEATH_DOWN_KEYPOSE_PHASE_ORDER,
        source_stance_variant_id="onehand_ready",
        source_stance_revision="v09_artist_approved_source_only",
        weapon_visible=False,
        fall_side="torso_right_legs_left_split",
        final_pose_persistent=True,
        gore_mode="waist_torso_legs_separation",
        detached_part_id="upper_torso_and_lower_body",
        detachment_frame=4,
        poses=DEATH_03_BASE_POSES_V01,
        appearance_revision="v03",
        head_revision="v22",
        proxy_revision="v25",
    ),
)


def _validate_profile(profile: DeathDownKeyposesProfileV01) -> None:
    if profile.direction != "down" or profile.loop:
        raise ValueError(f"{profile.death_variant_id} identity drifted")
    if profile.frame_order != DEATH_DOWN_KEYPOSE_FRAME_ORDER:
        raise ValueError(f"{profile.death_variant_id} frame order drifted")
    if profile.phase_order != DEATH_DOWN_KEYPOSE_PHASE_ORDER:
        raise ValueError(f"{profile.death_variant_id} phase order drifted")
    if tuple(pose.frame for pose in profile.poses) != profile.frame_order:
        raise ValueError(f"{profile.death_variant_id} pose frames drifted")
    if tuple(pose.phase for pose in profile.poses) != profile.phase_order:
        raise ValueError(f"{profile.death_variant_id} pose phases drifted")
    if not profile.final_pose_persistent:
        raise ValueError(f"{profile.death_variant_id} final pose must persist")
    if profile.weapon_visible:
        raise ValueError(f"{profile.death_variant_id} must be weapon agnostic")
    if profile.gore_mode == "waist_torso_legs_separation":
        if profile.detached_part_id != "upper_torso_and_lower_body":
            raise ValueError("death_03 torso/legs contract drifted")
        if profile.detachment_frame not in profile.frame_order:
            raise ValueError("death_03 separation frame is invalid")
    elif profile.detached_part_id is not None or profile.detachment_frame is not None:
        raise ValueError(f"{profile.death_variant_id} has unexpected detached-part data")
    if any(
        abs(value) > MAX_PELVIS_TRANSLATION
        for pose in profile.poses
        for value in pose.translation_deltas()
    ):
        raise ValueError(f"{profile.death_variant_id} pelvis translation exceeds budget")
    if any(
        abs(value) > MAX_ROTATION_DELTA_DEGREES
        for pose in profile.poses
        for value in pose.rotation_deltas()
    ):
        raise ValueError(f"{profile.death_variant_id} rotation exceeds budget")


def load_death_down_keyposes_profiles_v01(
    character_id: str,
) -> tuple[DeathDownKeyposesProfileV01, ...]:
    profiles = HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01
    if character_id != "human_warrior_m01":
        raise KeyError(f"No death down v01 profiles for character_id={character_id}")
    if tuple(profile.death_variant_id for profile in profiles) != DEATH_DOWN_VARIANT_IDS:
        raise ValueError("Death down v01 variant order drifted")
    for profile in profiles:
        _validate_profile(profile)
    return profiles


def load_death_down_keyposes_profile_v01(
    character_id: str,
    death_variant_id: str = "death_01_base",
) -> DeathDownKeyposesProfileV01:
    profiles = load_death_down_keyposes_profiles_v01(character_id)
    for profile in profiles:
        if profile.death_variant_id == death_variant_id:
            return profile
    raise KeyError(f"No death down v01 profile for death_variant_id={death_variant_id}")
