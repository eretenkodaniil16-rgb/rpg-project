from __future__ import annotations

from dataclasses import dataclass, fields

from walk_down_profile_v01 import load_walk_down_profile_v01


_PHASES = (
    "left_contact",
    "left_recoil",
    "left_passing",
    "right_contact",
    "right_recoil",
    "right_passing",
)


@dataclass(frozen=True)
class WalkDownFramePoseV02:
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
class WalkDownProfileV02:
    revision: str
    animation_revision: str
    animation_id: str
    fps: int
    loop: bool
    poses: tuple[WalkDownFramePoseV02, ...]

    def assert_valid(self) -> None:
        if self.revision != "v02" or self.animation_revision != "v03":
            raise ValueError("Walk profile must match data v02 / animation v03")
        if self.animation_id != "walk_down" or self.fps != 8 or not self.loop:
            raise ValueError("Walk down v03 must remain a six-frame 8 FPS loop")
        if tuple(item.frame for item in self.poses) != (1, 2, 3, 4, 5, 6):
            raise ValueError("Walk down v03 requires exactly frames 1..6")
        if tuple(item.phase for item in self.poses) != _PHASES:
            raise ValueError("Walk down v03 phase order drifted")

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
            raise ValueError("Walk down v03 needs contact, recoil and passing height phases")

        pelvis_height_range = max(item.pelvis_z for item in self.poses) - min(
            item.pelvis_z for item in self.poses
        )
        if pelvis_height_range > 0.045:
            raise ValueError("Walk down v03 pelvis bounce exceeds the restrained budget")

        predecessor = load_walk_down_profile_v01("human_warrior_m01")
        predecessor_height_range = max(item.pelvis_z for item in predecessor.poses) - min(
            item.pelvis_z for item in predecessor.poses
        )
        if pelvis_height_range >= predecessor_height_range * 0.70:
            raise ValueError("Walk down v03 must materially reduce the v02 vertical bounce")

        for pose in self.poses:
            if abs(pose.pelvis_x) > 0.024 or not -0.032 <= pose.pelvis_z <= 0.012:
                raise ValueError(f"Pelvis motion exceeds the v03 gameplay budget: {pose.phase}")
            if abs(pose.pelvis_roll_z_degrees) > 2.4:
                raise ValueError(f"Pelvis roll is too large: {pose.phase}")
            if abs(pose.spine_pitch_x_degrees) > 1.6:
                raise ValueError(f"Spine pitch is too large: {pose.phase}")
            if abs(pose.chest_yaw_z_degrees) > 1.6:
                raise ValueError(f"Chest counter-rotation is too large: {pose.phase}")
            if abs(pose.head_yaw_z_degrees) > 0.6:
                raise ValueError(f"Head stabilization is too large: {pose.phase}")
            if pose.chest_yaw_z_degrees * pose.head_yaw_z_degrees > 0.0:
                raise ValueError(f"Head must stabilize against chest yaw: {pose.phase}")
            if max(abs(pose.thigh_left_x_degrees), abs(pose.thigh_right_x_degrees)) > 18.0:
                raise ValueError(f"Thigh arc is too large: {pose.phase}")
            if max(abs(pose.shin_left_x_degrees), abs(pose.shin_right_x_degrees)) > 18.0:
                raise ValueError(f"Shin arc is too large: {pose.phase}")
            if max(abs(pose.foot_left_x_degrees), abs(pose.foot_right_x_degrees)) > 10.0:
                raise ValueError(f"Foot articulation is too large: {pose.phase}")
            if max(abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)) > 3.2:
                raise ValueError(f"Back cloth swing is too large: {pose.phase}")
            if abs(pose.cloth_center_x_degrees) > max(
                abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)
            ):
                raise ValueError(f"Center cloth panel must remain restrained: {pose.phase}")

        if abs(left_contact.foot_left_x_degrees) > 6.0:
            raise ValueError("Left contact foot must remain visually planted")
        if abs(right_contact.foot_right_x_degrees) > 6.0:
            raise ValueError("Right contact foot must remain visually planted")

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
            if wrap_delta > 12.0:
                raise ValueError(f"Walk loop wrap is too abrupt in channel {index}: {wrap_delta}")


HUMAN_WARRIOR_M01_WALK_DOWN_V02 = WalkDownProfileV02(
    revision="v02",
    animation_revision="v03",
    animation_id="walk_down",
    fps=8,
    loop=True,
    poses=(
        WalkDownFramePoseV02(
            frame=1,
            phase="left_contact",
            pelvis_x=-0.014,
            pelvis_z=-0.004,
            pelvis_roll_z_degrees=-1.6,
            spine_pitch_x_degrees=0.8,
            chest_yaw_z_degrees=1.2,
            head_yaw_z_degrees=-0.4,
            thigh_left_x_degrees=18.0,
            thigh_right_x_degrees=-14.0,
            shin_left_x_degrees=-4.0,
            shin_right_x_degrees=8.0,
            foot_left_x_degrees=-6.0,
            foot_right_x_degrees=10.0,
            upper_arm_left_x_degrees=-5.0,
            upper_arm_right_x_degrees=7.0,
            cloth_left_x_degrees=-2.5,
            cloth_center_x_degrees=-1.0,
            cloth_right_x_degrees=1.5,
        ),
        WalkDownFramePoseV02(
            frame=2,
            phase="left_recoil",
            pelvis_x=-0.022,
            pelvis_z=-0.030,
            pelvis_roll_z_degrees=-2.2,
            spine_pitch_x_degrees=1.4,
            chest_yaw_z_degrees=1.5,
            head_yaw_z_degrees=-0.5,
            thigh_left_x_degrees=9.0,
            thigh_right_x_degrees=-5.0,
            shin_left_x_degrees=-10.0,
            shin_right_x_degrees=18.0,
            foot_left_x_degrees=-2.0,
            foot_right_x_degrees=4.0,
            upper_arm_left_x_degrees=-2.5,
            upper_arm_right_x_degrees=3.5,
            cloth_left_x_degrees=-1.0,
            cloth_center_x_degrees=-0.4,
            cloth_right_x_degrees=2.5,
        ),
        WalkDownFramePoseV02(
            frame=3,
            phase="left_passing",
            pelvis_x=-0.008,
            pelvis_z=0.009,
            pelvis_roll_z_degrees=-0.8,
            spine_pitch_x_degrees=0.3,
            chest_yaw_z_degrees=0.4,
            head_yaw_z_degrees=-0.15,
            thigh_left_x_degrees=-6.0,
            thigh_right_x_degrees=10.0,
            shin_left_x_degrees=-14.0,
            shin_right_x_degrees=6.0,
            foot_left_x_degrees=6.0,
            foot_right_x_degrees=-2.0,
            upper_arm_left_x_degrees=1.5,
            upper_arm_right_x_degrees=-4.0,
            cloth_left_x_degrees=1.5,
            cloth_center_x_degrees=0.6,
            cloth_right_x_degrees=0.8,
        ),
        WalkDownFramePoseV02(
            frame=4,
            phase="right_contact",
            pelvis_x=0.014,
            pelvis_z=-0.004,
            pelvis_roll_z_degrees=1.6,
            spine_pitch_x_degrees=0.8,
            chest_yaw_z_degrees=-1.2,
            head_yaw_z_degrees=0.4,
            thigh_left_x_degrees=-16.0,
            thigh_right_x_degrees=18.0,
            shin_left_x_degrees=6.0,
            shin_right_x_degrees=-4.0,
            foot_left_x_degrees=10.0,
            foot_right_x_degrees=-6.0,
            upper_arm_left_x_degrees=5.0,
            upper_arm_right_x_degrees=-7.0,
            cloth_left_x_degrees=3.0,
            cloth_center_x_degrees=1.2,
            cloth_right_x_degrees=-2.5,
        ),
        WalkDownFramePoseV02(
            frame=5,
            phase="right_recoil",
            pelvis_x=0.022,
            pelvis_z=-0.030,
            pelvis_roll_z_degrees=2.2,
            spine_pitch_x_degrees=1.4,
            chest_yaw_z_degrees=-1.5,
            head_yaw_z_degrees=0.5,
            thigh_left_x_degrees=-6.0,
            thigh_right_x_degrees=9.0,
            shin_left_x_degrees=18.0,
            shin_right_x_degrees=-10.0,
            foot_left_x_degrees=4.0,
            foot_right_x_degrees=-2.0,
            upper_arm_left_x_degrees=2.5,
            upper_arm_right_x_degrees=-3.5,
            cloth_left_x_degrees=1.5,
            cloth_center_x_degrees=0.6,
            cloth_right_x_degrees=-1.0,
        ),
        WalkDownFramePoseV02(
            frame=6,
            phase="right_passing",
            pelvis_x=0.008,
            pelvis_z=0.009,
            pelvis_roll_z_degrees=0.8,
            spine_pitch_x_degrees=0.3,
            chest_yaw_z_degrees=-0.4,
            head_yaw_z_degrees=0.15,
            thigh_left_x_degrees=8.0,
            thigh_right_x_degrees=-10.0,
            shin_left_x_degrees=4.0,
            shin_right_x_degrees=-4.0,
            foot_left_x_degrees=-2.0,
            foot_right_x_degrees=6.0,
            upper_arm_left_x_degrees=-2.5,
            upper_arm_right_x_degrees=4.5,
            cloth_left_x_degrees=-1.5,
            cloth_center_x_degrees=-0.6,
            cloth_right_x_degrees=1.8,
        ),
    ),
)


def load_walk_down_profile_v02(character_id: str) -> WalkDownProfileV02:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No walk_down v03 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_WALK_DOWN_V02.assert_valid()
    return HUMAN_WARRIOR_M01_WALK_DOWN_V02
