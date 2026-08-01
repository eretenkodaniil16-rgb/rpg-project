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
class WalkLeftFramePoseV01:
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
class WalkLeftProfileV01:
    revision: str
    animation_revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    poses: tuple[WalkLeftFramePoseV01, ...]

    def assert_valid(self) -> None:
        if self.revision != "v01" or self.animation_revision != "v01":
            raise ValueError("Walk left profile must remain data v01 / animation v01")
        if self.animation_id != "walk_left" or self.direction != "left":
            raise ValueError("Walk left v01 must render the real left direction")
        if self.fps != 8 or not self.loop:
            raise ValueError("Walk left v01 must remain a six-frame 8 FPS loop")
        if tuple(item.frame for item in self.poses) != (1, 2, 3, 4, 5, 6):
            raise ValueError("Walk left v01 requires exactly frames 1..6")
        if tuple(item.phase for item in self.poses) != _PHASES:
            raise ValueError("Walk left v01 phase order drifted")

        left_contact, left_recoil, left_passing, right_contact, right_recoil, right_passing = (
            self.poses
        )
        if not left_contact.pelvis_x < 0.0 < right_contact.pelvis_x:
            raise ValueError("Walk left weight transfer must alternate physical sides")
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
            raise ValueError("Walk left requires recoil/contact/passing height phases")

        pelvis_height_range = max(item.pelvis_z for item in self.poses) - min(
            item.pelvis_z for item in self.poses
        )
        if pelvis_height_range > 0.024:
            raise ValueError("Walk left pelvis bounce exceeds the gameplay budget")

        for pose in self.poses:
            if abs(pose.pelvis_x) > 0.018 or not -0.020 <= pose.pelvis_z <= 0.004:
                raise ValueError(f"Pelvis motion exceeds the walk left budget: {pose.phase}")
            if abs(pose.pelvis_roll_z_degrees) > 1.8:
                raise ValueError(f"Pelvis roll is too large: {pose.phase}")
            if abs(pose.spine_pitch_x_degrees) > 1.4:
                raise ValueError(f"Spine pitch is too large: {pose.phase}")
            if abs(pose.chest_yaw_z_degrees) > 1.3:
                raise ValueError(f"Chest yaw is too large: {pose.phase}")
            if abs(pose.head_yaw_z_degrees) > 0.4:
                raise ValueError(f"Head stabilization is too large: {pose.phase}")
            if pose.chest_yaw_z_degrees * pose.head_yaw_z_degrees > 0.0:
                raise ValueError(f"Head must counter chest yaw: {pose.phase}")
            if max(abs(pose.thigh_left_x_degrees), abs(pose.thigh_right_x_degrees)) > 17.0:
                raise ValueError(f"Thigh arc is too large: {pose.phase}")
            if max(abs(pose.shin_left_x_degrees), abs(pose.shin_right_x_degrees)) > 13.0:
                raise ValueError(f"Shin arc is too large: {pose.phase}")
            if max(abs(pose.foot_left_x_degrees), abs(pose.foot_right_x_degrees)) > 8.0:
                raise ValueError(f"Foot articulation is too large: {pose.phase}")
            if max(abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)) > 2.3:
                raise ValueError(f"Back cloth swing is too large: {pose.phase}")
            if abs(pose.cloth_center_x_degrees) > max(
                abs(pose.cloth_left_x_degrees), abs(pose.cloth_right_x_degrees)
            ):
                raise ValueError(f"Center cloth panel must remain restrained: {pose.phase}")

        if abs(left_contact.foot_left_x_degrees) > 5.0:
            raise ValueError("Physical left contact foot must remain planted")
        if abs(right_contact.foot_right_x_degrees) > 5.0:
            raise ValueError("Physical right contact foot must remain planted")

        left_arm = tuple(item.upper_arm_left_x_degrees for item in self.poses)
        right_arm = tuple(item.upper_arm_right_x_degrees for item in self.poses)
        if left_arm == tuple(-value for value in right_arm):
            raise ValueError("Side walk arm swing must not be mirrored")
        if max(abs(value) for value in left_arm) >= max(abs(value) for value in right_arm):
            raise ValueError("Foreground large left pauldron requires the restrained arm arc")

        channel_count = len(self.poses[0].numeric_channels())
        for index in range(channel_count):
            wrap_delta = abs(
                self.poses[-1].numeric_channels()[index]
                - self.poses[0].numeric_channels()[index]
            )
            if wrap_delta > 10.0:
                raise ValueError(f"Walk left loop wrap is too abrupt in channel {index}: {wrap_delta}")


HUMAN_WARRIOR_M01_WALK_LEFT_V01 = WalkLeftProfileV01(
    revision="v01",
    animation_revision="v01",
    animation_id="walk_left",
    direction="left",
    fps=8,
    loop=True,
    poses=(
        WalkLeftFramePoseV01(
            frame=1,
            phase="physical_left_contact",
            pelvis_x=-0.010,
            pelvis_z=-0.004,
            pelvis_roll_z_degrees=-1.0,
            spine_pitch_x_degrees=0.8,
            chest_yaw_z_degrees=0.8,
            head_yaw_z_degrees=-0.2,
            thigh_left_x_degrees=17.0,
            thigh_right_x_degrees=-13.0,
            shin_left_x_degrees=-4.0,
            shin_right_x_degrees=7.0,
            foot_left_x_degrees=-4.0,
            foot_right_x_degrees=8.0,
            upper_arm_left_x_degrees=-4.5,
            upper_arm_right_x_degrees=6.5,
            forearm_left_x_degrees=6.0,
            forearm_right_x_degrees=10.0,
            cloth_left_x_degrees=-1.8,
            cloth_center_x_degrees=-0.7,
            cloth_right_x_degrees=1.2,
        ),
        WalkLeftFramePoseV01(
            frame=2,
            phase="physical_left_recoil",
            pelvis_x=-0.016,
            pelvis_z=-0.018,
            pelvis_roll_z_degrees=-1.6,
            spine_pitch_x_degrees=1.3,
            chest_yaw_z_degrees=1.2,
            head_yaw_z_degrees=-0.4,
            thigh_left_x_degrees=8.0,
            thigh_right_x_degrees=-4.0,
            shin_left_x_degrees=-7.0,
            shin_right_x_degrees=13.0,
            foot_left_x_degrees=-1.0,
            foot_right_x_degrees=3.0,
            upper_arm_left_x_degrees=-2.0,
            upper_arm_right_x_degrees=3.0,
            forearm_left_x_degrees=7.0,
            forearm_right_x_degrees=11.0,
            cloth_left_x_degrees=-0.8,
            cloth_center_x_degrees=-0.3,
            cloth_right_x_degrees=2.1,
        ),
        WalkLeftFramePoseV01(
            frame=3,
            phase="physical_left_passing",
            pelvis_x=-0.005,
            pelvis_z=0.003,
            pelvis_roll_z_degrees=-0.5,
            spine_pitch_x_degrees=0.7,
            chest_yaw_z_degrees=0.3,
            head_yaw_z_degrees=-0.1,
            thigh_left_x_degrees=-5.0,
            thigh_right_x_degrees=9.0,
            shin_left_x_degrees=-11.0,
            shin_right_x_degrees=7.0,
            foot_left_x_degrees=5.0,
            foot_right_x_degrees=-1.0,
            upper_arm_left_x_degrees=1.2,
            upper_arm_right_x_degrees=-3.8,
            forearm_left_x_degrees=9.0,
            forearm_right_x_degrees=6.0,
            cloth_left_x_degrees=1.2,
            cloth_center_x_degrees=0.4,
            cloth_right_x_degrees=0.6,
        ),
        WalkLeftFramePoseV01(
            frame=4,
            phase="physical_right_contact",
            pelvis_x=0.010,
            pelvis_z=-0.004,
            pelvis_roll_z_degrees=1.0,
            spine_pitch_x_degrees=0.8,
            chest_yaw_z_degrees=-0.8,
            head_yaw_z_degrees=0.2,
            thigh_left_x_degrees=-13.0,
            thigh_right_x_degrees=17.0,
            shin_left_x_degrees=7.0,
            shin_right_x_degrees=-4.0,
            foot_left_x_degrees=8.0,
            foot_right_x_degrees=-4.0,
            upper_arm_left_x_degrees=4.0,
            upper_arm_right_x_degrees=-6.5,
            forearm_left_x_degrees=10.0,
            forearm_right_x_degrees=6.0,
            cloth_left_x_degrees=2.2,
            cloth_center_x_degrees=0.8,
            cloth_right_x_degrees=-1.8,
        ),
        WalkLeftFramePoseV01(
            frame=5,
            phase="physical_right_recoil",
            pelvis_x=0.016,
            pelvis_z=-0.018,
            pelvis_roll_z_degrees=1.6,
            spine_pitch_x_degrees=1.3,
            chest_yaw_z_degrees=-1.2,
            head_yaw_z_degrees=0.4,
            thigh_left_x_degrees=-4.0,
            thigh_right_x_degrees=8.0,
            shin_left_x_degrees=13.0,
            shin_right_x_degrees=-7.0,
            foot_left_x_degrees=3.0,
            foot_right_x_degrees=-1.0,
            upper_arm_left_x_degrees=2.0,
            upper_arm_right_x_degrees=-3.0,
            forearm_left_x_degrees=11.0,
            forearm_right_x_degrees=7.0,
            cloth_left_x_degrees=1.2,
            cloth_center_x_degrees=0.4,
            cloth_right_x_degrees=-0.8,
        ),
        WalkLeftFramePoseV01(
            frame=6,
            phase="physical_right_passing",
            pelvis_x=0.005,
            pelvis_z=0.003,
            pelvis_roll_z_degrees=0.5,
            spine_pitch_x_degrees=0.7,
            chest_yaw_z_degrees=-0.3,
            head_yaw_z_degrees=0.1,
            thigh_left_x_degrees=8.0,
            thigh_right_x_degrees=-9.0,
            shin_left_x_degrees=5.0,
            shin_right_x_degrees=-3.0,
            foot_left_x_degrees=-1.0,
            foot_right_x_degrees=5.0,
            upper_arm_left_x_degrees=-2.0,
            upper_arm_right_x_degrees=4.2,
            forearm_left_x_degrees=6.0,
            forearm_right_x_degrees=9.0,
            cloth_left_x_degrees=-1.2,
            cloth_center_x_degrees=-0.4,
            cloth_right_x_degrees=1.4,
        ),
    ),
)


def load_walk_left_profile_v01(character_id: str) -> WalkLeftProfileV01:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No walk_left v01 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_WALK_LEFT_V01.assert_valid()
    return HUMAN_WARRIOR_M01_WALK_LEFT_V01
