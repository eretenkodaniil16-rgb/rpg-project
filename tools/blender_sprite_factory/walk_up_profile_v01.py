from __future__ import annotations

from dataclasses import dataclass, fields


_PHASES = (
    "physical_left_contact",
    "physical_left_recoil",
    "physical_left_passing",
    "physical_right_contact",
    "physical_right_recoil",
    "physical_right_passing",
)


@dataclass(frozen=True)
class WalkUpFramePoseV01:
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
    forearm_left_x_degrees: float
    forearm_right_x_degrees: float
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
class WalkUpProfileV01:
    revision: str
    animation_revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    poses: tuple[WalkUpFramePoseV01, ...]

    def assert_valid(self) -> None:
        if self.revision != "v01" or self.animation_revision != "v01":
            raise ValueError("Walk up profile must remain data v01 / animation v01")
        if self.animation_id != "walk_up" or self.direction != "up":
            raise ValueError("Walk up v01 must render the real rear direction")
        if self.fps != 8 or not self.loop:
            raise ValueError("Walk up v01 must remain a six-frame 8 FPS loop")
        if tuple(item.frame for item in self.poses) != (1, 2, 3, 4, 5, 6):
            raise ValueError("Walk up v01 requires exactly frames 1..6")
        if tuple(item.phase for item in self.poses) != _PHASES:
            raise ValueError("Walk up v01 phase order drifted")

        left_contact, left_recoil, left_passing, right_contact, right_recoil, right_passing = (
            self.poses
        )
        if not left_contact.pelvis_x < 0.0 < right_contact.pelvis_x:
            raise ValueError("Walk up weight transfer must alternate physical sides")
        if abs(left_contact.pelvis_z - right_contact.pelvis_z) > 1e-9:
            raise ValueError("Opposite contact phases must keep equal height")
        if abs(left_recoil.pelvis_z - right_recoil.pelvis_z) > 1e-9:
            raise ValueError("Opposite recoil phases must keep equal height")
        if abs(left_passing.pelvis_z - right_passing.pelvis_z) > 1e-9:
            raise ValueError("Opposite passing phases must keep equal height")
        if not (
            left_recoil.pelvis_z < left_contact.pelvis_z < left_passing.pelvis_z
            and right_recoil.pelvis_z < right_contact.pelvis_z < right_passing.pelvis_z
        ):
            raise ValueError("Walk up requires recoil/contact/passing height phases")

        pelvis_height_range = max(item.pelvis_z for item in self.poses) - min(
            item.pelvis_z for item in self.poses
        )
        if pelvis_height_range > 0.022:
            raise ValueError("Walk up pelvis bounce exceeds the gameplay budget")

        for pose in self.poses:
            if abs(pose.pelvis_x) > 0.016 or not -0.018 <= pose.pelvis_z <= 0.004:
                raise ValueError(f"Pelvis motion exceeds the walk up budget: {pose.phase}")
            if abs(pose.pelvis_roll_z_degrees) > 1.5:
                raise ValueError(f"Pelvis roll is too large: {pose.phase}")
            if abs(pose.spine_pitch_x_degrees) > 1.2:
                raise ValueError(f"Spine pitch is too large: {pose.phase}")
            if abs(pose.chest_yaw_z_degrees) > 1.0:
                raise ValueError(f"Chest yaw is too large: {pose.phase}")
            if abs(pose.head_yaw_z_degrees) > 0.3:
                raise ValueError(f"Head stabilization is too large: {pose.phase}")
            if pose.chest_yaw_z_degrees * pose.head_yaw_z_degrees > 0.0:
                raise ValueError(f"Head must counter chest yaw: {pose.phase}")
            if max(abs(pose.thigh_left_x_degrees), abs(pose.thigh_right_x_degrees)) > 16.0:
                raise ValueError(f"Thigh arc is too large: {pose.phase}")
            if max(abs(pose.shin_left_x_degrees), abs(pose.shin_right_x_degrees)) > 12.0:
                raise ValueError(f"Shin arc is too large: {pose.phase}")
            if max(abs(pose.foot_left_x_degrees), abs(pose.foot_right_x_degrees)) > 7.0:
                raise ValueError(f"Foot articulation is too large: {pose.phase}")
            if max(abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)) > 3.0:
                raise ValueError(f"Rear cloth swing is too large: {pose.phase}")
            if abs(pose.cloth_center_x_degrees) > 1.2:
                raise ValueError(f"Center rear cloth panel is too large: {pose.phase}")

        if abs(left_contact.foot_left_x_degrees) > 5.0:
            raise ValueError("Physical left contact foot must remain planted")
        if abs(right_contact.foot_right_x_degrees) > 5.0:
            raise ValueError("Physical right contact foot must remain planted")

        left_arm = tuple(item.upper_arm_left_x_degrees for item in self.poses)
        right_arm = tuple(item.upper_arm_right_x_degrees for item in self.poses)
        if left_arm == tuple(-value for value in right_arm):
            raise ValueError("Walk up arm swing must retain physical asymmetry")
        if max(abs(value) for value in left_arm) >= max(abs(value) for value in right_arm):
            raise ValueError("Large physical-left pauldron requires the restrained arm arc")

        cloth_motion = max(
            max(abs(item.cloth_left_x_degrees), abs(item.cloth_right_x_degrees))
            for item in self.poses
        )
        if cloth_motion < 2.5:
            raise ValueError("Rear walk must keep the back cloth readable")

        channel_count = len(self.poses[0].numeric_channels())
        for index in range(channel_count):
            wrap_delta = abs(
                self.poses[-1].numeric_channels()[index]
                - self.poses[0].numeric_channels()[index]
            )
            if wrap_delta > 10.0:
                raise ValueError(
                    f"Walk up loop wrap is too abrupt in channel {index}: {wrap_delta}"
                )


HUMAN_WARRIOR_M01_WALK_UP_V01 = WalkUpProfileV01(
    revision="v01",
    animation_revision="v01",
    animation_id="walk_up",
    direction="up",
    fps=8,
    loop=True,
    poses=(
        WalkUpFramePoseV01(
            frame=1,
            phase="physical_left_contact",
            pelvis_x=-0.008,
            pelvis_z=-0.004,
            pelvis_roll_z_degrees=-0.8,
            spine_pitch_x_degrees=0.6,
            chest_yaw_z_degrees=0.6,
            head_yaw_z_degrees=-0.15,
            thigh_left_x_degrees=15.0,
            thigh_right_x_degrees=-11.0,
            shin_left_x_degrees=-4.0,
            shin_right_x_degrees=6.0,
            foot_left_x_degrees=-4.0,
            foot_right_x_degrees=7.0,
            upper_arm_left_x_degrees=-3.8,
            upper_arm_right_x_degrees=6.4,
            forearm_left_x_degrees=6.5,
            forearm_right_x_degrees=10.0,
            cloth_left_x_degrees=-2.4,
            cloth_center_x_degrees=-1.0,
            cloth_right_x_degrees=1.5,
        ),
        WalkUpFramePoseV01(
            frame=2,
            phase="physical_left_recoil",
            pelvis_x=-0.014,
            pelvis_z=-0.017,
            pelvis_roll_z_degrees=-1.4,
            spine_pitch_x_degrees=1.1,
            chest_yaw_z_degrees=0.9,
            head_yaw_z_degrees=-0.3,
            thigh_left_x_degrees=7.0,
            thigh_right_x_degrees=-3.0,
            shin_left_x_degrees=-7.0,
            shin_right_x_degrees=12.0,
            foot_left_x_degrees=-1.0,
            foot_right_x_degrees=3.0,
            upper_arm_left_x_degrees=-1.5,
            upper_arm_right_x_degrees=3.2,
            forearm_left_x_degrees=7.5,
            forearm_right_x_degrees=11.0,
            cloth_left_x_degrees=-0.9,
            cloth_center_x_degrees=-0.5,
            cloth_right_x_degrees=3.0,
        ),
        WalkUpFramePoseV01(
            frame=3,
            phase="physical_left_passing",
            pelvis_x=-0.004,
            pelvis_z=0.003,
            pelvis_roll_z_degrees=-0.4,
            spine_pitch_x_degrees=0.5,
            chest_yaw_z_degrees=0.2,
            head_yaw_z_degrees=-0.1,
            thigh_left_x_degrees=-4.0,
            thigh_right_x_degrees=8.0,
            shin_left_x_degrees=-10.0,
            shin_right_x_degrees=6.0,
            foot_left_x_degrees=4.0,
            foot_right_x_degrees=-1.0,
            upper_arm_left_x_degrees=1.2,
            upper_arm_right_x_degrees=-3.8,
            forearm_left_x_degrees=9.0,
            forearm_right_x_degrees=5.5,
            cloth_left_x_degrees=1.5,
            cloth_center_x_degrees=0.8,
            cloth_right_x_degrees=1.0,
        ),
        WalkUpFramePoseV01(
            frame=4,
            phase="physical_right_contact",
            pelvis_x=0.008,
            pelvis_z=-0.004,
            pelvis_roll_z_degrees=0.8,
            spine_pitch_x_degrees=0.6,
            chest_yaw_z_degrees=-0.6,
            head_yaw_z_degrees=0.15,
            thigh_left_x_degrees=-11.0,
            thigh_right_x_degrees=15.0,
            shin_left_x_degrees=6.0,
            shin_right_x_degrees=-4.0,
            foot_left_x_degrees=7.0,
            foot_right_x_degrees=-4.0,
            upper_arm_left_x_degrees=3.5,
            upper_arm_right_x_degrees=-6.6,
            forearm_left_x_degrees=10.0,
            forearm_right_x_degrees=6.5,
            cloth_left_x_degrees=3.0,
            cloth_center_x_degrees=1.2,
            cloth_right_x_degrees=-2.2,
        ),
        WalkUpFramePoseV01(
            frame=5,
            phase="physical_right_recoil",
            pelvis_x=0.014,
            pelvis_z=-0.017,
            pelvis_roll_z_degrees=1.4,
            spine_pitch_x_degrees=1.1,
            chest_yaw_z_degrees=-0.9,
            head_yaw_z_degrees=0.3,
            thigh_left_x_degrees=-3.0,
            thigh_right_x_degrees=7.0,
            shin_left_x_degrees=12.0,
            shin_right_x_degrees=-7.0,
            foot_left_x_degrees=3.0,
            foot_right_x_degrees=-1.0,
            upper_arm_left_x_degrees=1.6,
            upper_arm_right_x_degrees=-3.0,
            forearm_left_x_degrees=11.0,
            forearm_right_x_degrees=7.5,
            cloth_left_x_degrees=1.6,
            cloth_center_x_degrees=0.6,
            cloth_right_x_degrees=-0.9,
        ),
        WalkUpFramePoseV01(
            frame=6,
            phase="physical_right_passing",
            pelvis_x=0.004,
            pelvis_z=0.003,
            pelvis_roll_z_degrees=0.4,
            spine_pitch_x_degrees=0.5,
            chest_yaw_z_degrees=-0.2,
            head_yaw_z_degrees=0.1,
            thigh_left_x_degrees=7.0,
            thigh_right_x_degrees=-8.0,
            shin_left_x_degrees=4.0,
            shin_right_x_degrees=-3.0,
            foot_left_x_degrees=-1.0,
            foot_right_x_degrees=4.0,
            upper_arm_left_x_degrees=-1.6,
            upper_arm_right_x_degrees=4.0,
            forearm_left_x_degrees=6.0,
            forearm_right_x_degrees=9.0,
            cloth_left_x_degrees=-1.4,
            cloth_center_x_degrees=-0.7,
            cloth_right_x_degrees=1.8,
        ),
    ),
)


def load_walk_up_profile_v01(character_id: str) -> WalkUpProfileV01:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No walk_up v01 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_WALK_UP_V01.assert_valid()
    return HUMAN_WARRIOR_M01_WALK_UP_V01
