from __future__ import annotations

from dataclasses import dataclass, fields


_PHASES = (
    "left_contact",
    "left_recoil",
    "left_passing",
    "right_contact",
    "right_recoil",
    "right_passing",
)


@dataclass(frozen=True)
class WalkDownFramePoseV01:
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
    shin_left_x_degrees: float
    shin_right_x_degrees: float
    foot_left_x_degrees: float
    foot_right_x_degrees: float
    upper_arm_left_x_degrees: float
    upper_arm_right_x_degrees: float
    cloth_left_x_degrees: float
    cloth_center_x_degrees: float
    cloth_right_x_degrees: float

    def numeric_channels(self) -> tuple[float, ...]:
        return tuple(
            float(getattr(self, item.name))
            for item in fields(self)
            if item.name not in {"frame", "phase"}
        )


@dataclass(frozen=True)
class WalkDownProfileV01:
    revision: str
    animation_revision: str
    animation_id: str
    fps: int
    loop: bool
    poses: tuple[WalkDownFramePoseV01, ...]

    def assert_valid(self) -> None:
        if self.revision != "v01" or self.animation_revision != "v02":
            raise ValueError("Walk profile must match data v01 / animation v02")
        if self.animation_id != "walk_down" or self.fps != 8 or not self.loop:
            raise ValueError("Walk down v02 must remain a six-frame 8 FPS loop")
        if tuple(item.frame for item in self.poses) != (1, 2, 3, 4, 5, 6):
            raise ValueError("Walk down v02 requires exactly frames 1..6")
        if tuple(item.phase for item in self.poses) != _PHASES:
            raise ValueError("Walk down v02 phase order drifted")

        left_contact, left_recoil, left_passing, right_contact, right_recoil, right_passing = (
            self.poses
        )
        if not left_contact.pelvis_x < 0.0 < right_contact.pelvis_x:
            raise ValueError("Pelvis weight transfer must alternate physical sides")
        if abs(left_contact.pelvis_z - right_contact.pelvis_z) > 1e-9:
            raise ValueError("Opposite contact phases must keep equal body height")
        if abs(left_recoil.pelvis_z - right_recoil.pelvis_z) > 1e-9:
            raise ValueError("Opposite recoil phases must keep equal body height")
        if abs(left_passing.pelvis_z - right_passing.pelvis_z) > 1e-9:
            raise ValueError("Opposite passing phases must keep equal body height")
        if not (
            left_recoil.pelvis_z < left_contact.pelvis_z < left_passing.pelvis_z
            and right_recoil.pelvis_z < right_contact.pelvis_z < right_passing.pelvis_z
        ):
            raise ValueError("Walk down v02 needs contact, recoil and passing height phases")

        for pose in self.poses:
            if abs(pose.pelvis_x) > 0.04 or not -0.065 <= pose.pelvis_z <= 0.025:
                raise ValueError(f"Pelvis motion exceeds gameplay silhouette budget: {pose.phase}")
            if abs(pose.pelvis_roll_z_degrees) > 3.5:
                raise ValueError(f"Pelvis roll is too large: {pose.phase}")
            if abs(pose.spine_pitch_x_degrees) > 2.5:
                raise ValueError(f"Spine pitch is too large: {pose.phase}")
            if abs(pose.chest_yaw_z_degrees) > 2.5:
                raise ValueError(f"Chest counter-rotation is too large: {pose.phase}")
            if abs(pose.head_yaw_z_degrees) > 1.25:
                raise ValueError(f"Head stabilization is too large: {pose.phase}")
            if pose.chest_yaw_z_degrees * pose.head_yaw_z_degrees > 0.0:
                raise ValueError(f"Head must stabilize against chest yaw: {pose.phase}")
            if max(abs(pose.foot_left_x_degrees), abs(pose.foot_right_x_degrees)) > 15.0:
                raise ValueError(f"Foot articulation is too large: {pose.phase}")
            if max(abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)) > 5.0:
                raise ValueError(f"Back cloth swing is too large: {pose.phase}")
            if abs(pose.cloth_center_x_degrees) > max(
                abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)
            ):
                raise ValueError(f"Center cloth panel must remain restrained: {pose.phase}")

        left_arm = tuple(item.upper_arm_left_x_degrees for item in self.poses)
        right_arm = tuple(item.upper_arm_right_x_degrees for item in self.poses)
        if left_arm == tuple(-value for value in right_arm):
            raise ValueError("Arm swing must respect asymmetric pauldrons, not mirror exactly")
        if max(abs(value) for value in left_arm) >= max(abs(value) for value in right_arm):
            raise ValueError("Large left pauldron must use the more restrained arm arc")

        channel_count = len(self.poses[0].numeric_channels())
        for index in range(channel_count):
            wrap_delta = abs(
                self.poses[-1].numeric_channels()[index]
                - self.poses[0].numeric_channels()[index]
            )
            if wrap_delta > 14.0:
                raise ValueError(f"Walk loop wrap is too abrupt in channel {index}: {wrap_delta}")


HUMAN_WARRIOR_M01_WALK_DOWN_V01 = WalkDownProfileV01(
    revision="v01",
    animation_revision="v02",
    animation_id="walk_down",
    fps=8,
    loop=True,
    poses=(
        WalkDownFramePoseV01(
            frame=1,
            phase="left_contact",
            pelvis_x=-0.018,
            pelvis_z=-0.005,
            pelvis_roll_z_degrees=-2.0,
            spine_pitch_x_degrees=1.0,
            chest_yaw_z_degrees=1.5,
            head_yaw_z_degrees=-0.75,
            thigh_left_x_degrees=22.0,
            thigh_right_x_degrees=-18.0,
            shin_left_x_degrees=-6.0,
            shin_right_x_degrees=10.0,
            foot_left_x_degrees=-8.0,
            foot_right_x_degrees=14.0,
            upper_arm_left_x_degrees=-6.0,
            upper_arm_right_x_degrees=8.0,
            cloth_left_x_degrees=-3.0,
            cloth_center_x_degrees=-1.5,
            cloth_right_x_degrees=2.0,
        ),
        WalkDownFramePoseV01(
            frame=2,
            phase="left_recoil",
            pelvis_x=-0.030,
            pelvis_z=-0.055,
            pelvis_roll_z_degrees=-3.0,
            spine_pitch_x_degrees=2.0,
            chest_yaw_z_degrees=2.0,
            head_yaw_z_degrees=-1.0,
            thigh_left_x_degrees=10.0,
            thigh_right_x_degrees=-6.0,
            shin_left_x_degrees=-14.0,
            shin_right_x_degrees=24.0,
            foot_left_x_degrees=-4.0,
            foot_right_x_degrees=6.0,
            upper_arm_left_x_degrees=-3.0,
            upper_arm_right_x_degrees=4.0,
            cloth_left_x_degrees=-1.0,
            cloth_center_x_degrees=-0.5,
            cloth_right_x_degrees=3.0,
        ),
        WalkDownFramePoseV01(
            frame=3,
            phase="left_passing",
            pelvis_x=-0.010,
            pelvis_z=0.015,
            pelvis_roll_z_degrees=-1.0,
            spine_pitch_x_degrees=0.5,
            chest_yaw_z_degrees=0.5,
            head_yaw_z_degrees=-0.25,
            thigh_left_x_degrees=-8.0,
            thigh_right_x_degrees=12.0,
            shin_left_x_degrees=-20.0,
            shin_right_x_degrees=8.0,
            foot_left_x_degrees=8.0,
            foot_right_x_degrees=-2.0,
            upper_arm_left_x_degrees=2.0,
            upper_arm_right_x_degrees=-5.0,
            cloth_left_x_degrees=2.0,
            cloth_center_x_degrees=1.0,
            cloth_right_x_degrees=1.0,
        ),
        WalkDownFramePoseV01(
            frame=4,
            phase="right_contact",
            pelvis_x=0.018,
            pelvis_z=-0.005,
            pelvis_roll_z_degrees=2.0,
            spine_pitch_x_degrees=1.0,
            chest_yaw_z_degrees=-1.5,
            head_yaw_z_degrees=0.75,
            thigh_left_x_degrees=-20.0,
            thigh_right_x_degrees=22.0,
            shin_left_x_degrees=8.0,
            shin_right_x_degrees=-6.0,
            foot_left_x_degrees=14.0,
            foot_right_x_degrees=-8.0,
            upper_arm_left_x_degrees=6.0,
            upper_arm_right_x_degrees=-8.0,
            cloth_left_x_degrees=4.0,
            cloth_center_x_degrees=2.0,
            cloth_right_x_degrees=-3.0,
        ),
        WalkDownFramePoseV01(
            frame=5,
            phase="right_recoil",
            pelvis_x=0.030,
            pelvis_z=-0.055,
            pelvis_roll_z_degrees=3.0,
            spine_pitch_x_degrees=2.0,
            chest_yaw_z_degrees=-2.0,
            head_yaw_z_degrees=1.0,
            thigh_left_x_degrees=-8.0,
            thigh_right_x_degrees=8.0,
            shin_left_x_degrees=24.0,
            shin_right_x_degrees=-14.0,
            foot_left_x_degrees=6.0,
            foot_right_x_degrees=-4.0,
            upper_arm_left_x_degrees=3.0,
            upper_arm_right_x_degrees=-4.0,
            cloth_left_x_degrees=2.0,
            cloth_center_x_degrees=1.0,
            cloth_right_x_degrees=-1.0,
        ),
        WalkDownFramePoseV01(
            frame=6,
            phase="right_passing",
            pelvis_x=0.010,
            pelvis_z=0.015,
            pelvis_roll_z_degrees=1.0,
            spine_pitch_x_degrees=0.5,
            chest_yaw_z_degrees=-0.5,
            head_yaw_z_degrees=0.25,
            thigh_left_x_degrees=10.0,
            thigh_right_x_degrees=-12.0,
            shin_left_x_degrees=10.0,
            shin_right_x_degrees=-20.0,
            foot_left_x_degrees=-2.0,
            foot_right_x_degrees=8.0,
            upper_arm_left_x_degrees=-3.0,
            upper_arm_right_x_degrees=5.0,
            cloth_left_x_degrees=-2.0,
            cloth_center_x_degrees=-1.0,
            cloth_right_x_degrees=2.0,
        ),
    ),
)


def load_walk_down_profile_v01(character_id: str) -> WalkDownProfileV01:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No walk_down v02 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_WALK_DOWN_V01.assert_valid()
    return HUMAN_WARRIOR_M01_WALK_DOWN_V01
