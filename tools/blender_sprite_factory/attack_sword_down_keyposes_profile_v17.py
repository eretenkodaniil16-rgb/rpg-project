from __future__ import annotations

from dataclasses import dataclass

from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
)


ATTACK_KEYPOSE_FRAME_ORDER = (1, 2, 3, 4, 5)
ATTACK_KEYPOSE_PHASE_ORDER = (
    "guard",
    "anticipation",
    "contact",
    "follow_through",
    "recovery",
)
ATTACK_KEYPOSE_FPS = 6
MAX_ROTATION_DELTA_DEGREES = 72.0
MAX_PELVIS_TRANSLATION = 0.08


@dataclass(frozen=True)
class AttackSwordDownPoseDeltaV17:
    frame: int
    phase: str
    pelvis_x: float = 0.0
    pelvis_z: float = 0.0
    pelvis_roll_z_degrees: float = 0.0
    spine_pitch_x_degrees: float = 0.0
    chest_yaw_z_degrees: float = 0.0
    head_yaw_z_degrees: float = 0.0
    thigh_left_x_degrees: float = 0.0
    thigh_right_x_degrees: float = 0.0
    shin_left_x_degrees: float = 0.0
    shin_right_x_degrees: float = 0.0
    foot_left_x_degrees: float = 0.0
    foot_right_x_degrees: float = 0.0
    upper_arm_left_x_degrees: float = 0.0
    upper_arm_left_z_degrees: float = 0.0
    forearm_left_x_degrees: float = 0.0
    forearm_left_z_degrees: float = 0.0
    hand_left_x_degrees: float = 0.0
    hand_left_z_degrees: float = 0.0
    upper_arm_right_x_degrees: float = 0.0
    upper_arm_right_z_degrees: float = 0.0
    forearm_right_x_degrees: float = 0.0
    forearm_right_z_degrees: float = 0.0
    hand_right_x_degrees: float = 0.0
    hand_right_z_degrees: float = 0.0
    cloth_left_x_degrees: float = 0.0
    cloth_center_x_degrees: float = 0.0
    cloth_right_x_degrees: float = 0.0

    def rotation_deltas(self) -> tuple[float, ...]:
        return (
            self.pelvis_roll_z_degrees,
            self.spine_pitch_x_degrees,
            self.chest_yaw_z_degrees,
            self.head_yaw_z_degrees,
            self.thigh_left_x_degrees,
            self.thigh_right_x_degrees,
            self.shin_left_x_degrees,
            self.shin_right_x_degrees,
            self.foot_left_x_degrees,
            self.foot_right_x_degrees,
            self.upper_arm_left_x_degrees,
            self.upper_arm_left_z_degrees,
            self.forearm_left_x_degrees,
            self.forearm_left_z_degrees,
            self.hand_left_x_degrees,
            self.hand_left_z_degrees,
            self.upper_arm_right_x_degrees,
            self.upper_arm_right_z_degrees,
            self.forearm_right_x_degrees,
            self.forearm_right_z_degrees,
            self.hand_right_x_degrees,
            self.hand_right_z_degrees,
            self.cloth_left_x_degrees,
            self.cloth_center_x_degrees,
            self.cloth_right_x_degrees,
        )


@dataclass(frozen=True)
class AttackSwordDownGripV17:
    grip_id: str
    display_name: str
    action_id: str
    stance_variant_id: str
    stance_source_revision: str
    weapon_cycle_id: str
    trajectory_id: str
    poses: tuple[AttackSwordDownPoseDeltaV17, ...]


@dataclass(frozen=True)
class AttackSwordDownKeyposesProfileV17:
    character_id: str
    revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    grips: tuple[AttackSwordDownGripV17, ...]
    appearance_revision: str
    head_revision: str
    proxy_revision: str
    combat_idle_source_revision: str
    directional_weapon_source_revision: str


ONEHAND_POSES = (
    AttackSwordDownPoseDeltaV17(frame=1, phase="guard"),
    AttackSwordDownPoseDeltaV17(
        frame=2,
        phase="anticipation",
        pelvis_x=0.02,
        pelvis_z=-0.01,
        pelvis_roll_z_degrees=-3.0,
        spine_pitch_x_degrees=2.0,
        chest_yaw_z_degrees=20.0,
        head_yaw_z_degrees=-8.0,
        thigh_left_x_degrees=-3.0,
        thigh_right_x_degrees=3.0,
        shin_left_x_degrees=2.0,
        shin_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=2.0,
        upper_arm_left_z_degrees=8.0,
        forearm_left_x_degrees=3.0,
        forearm_left_z_degrees=4.0,
        hand_left_z_degrees=4.0,
        upper_arm_right_x_degrees=-18.0,
        upper_arm_right_z_degrees=14.0,
        forearm_right_x_degrees=-22.0,
        forearm_right_z_degrees=-14.0,
        hand_right_x_degrees=-16.0,
        hand_right_z_degrees=28.0,
        cloth_left_x_degrees=-4.0,
        cloth_center_x_degrees=-2.0,
        cloth_right_x_degrees=3.0,
    ),
    AttackSwordDownPoseDeltaV17(
        frame=3,
        phase="contact",
        pelvis_x=-0.02,
        pelvis_z=-0.03,
        pelvis_roll_z_degrees=4.0,
        spine_pitch_x_degrees=-9.0,
        chest_yaw_z_degrees=-28.0,
        head_yaw_z_degrees=10.0,
        thigh_left_x_degrees=6.0,
        thigh_right_x_degrees=-5.0,
        shin_left_x_degrees=-5.0,
        shin_right_x_degrees=4.0,
        foot_left_x_degrees=2.0,
        foot_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=8.0,
        upper_arm_left_z_degrees=-10.0,
        forearm_left_x_degrees=12.0,
        forearm_left_z_degrees=-12.0,
        hand_left_x_degrees=5.0,
        hand_left_z_degrees=-8.0,
        upper_arm_right_x_degrees=34.0,
        upper_arm_right_z_degrees=-42.0,
        forearm_right_x_degrees=42.0,
        forearm_right_z_degrees=-30.0,
        hand_right_x_degrees=32.0,
        hand_right_z_degrees=-62.0,
        cloth_left_x_degrees=8.0,
        cloth_center_x_degrees=5.0,
        cloth_right_x_degrees=-7.0,
    ),
    AttackSwordDownPoseDeltaV17(
        frame=4,
        phase="follow_through",
        pelvis_x=-0.025,
        pelvis_z=-0.025,
        pelvis_roll_z_degrees=5.0,
        spine_pitch_x_degrees=-11.0,
        chest_yaw_z_degrees=-38.0,
        head_yaw_z_degrees=14.0,
        thigh_left_x_degrees=7.0,
        thigh_right_x_degrees=-6.0,
        shin_left_x_degrees=-6.0,
        shin_right_x_degrees=5.0,
        foot_left_x_degrees=3.0,
        foot_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=12.0,
        upper_arm_left_z_degrees=-15.0,
        forearm_left_x_degrees=16.0,
        forearm_left_z_degrees=-16.0,
        hand_left_x_degrees=7.0,
        hand_left_z_degrees=-12.0,
        upper_arm_right_x_degrees=42.0,
        upper_arm_right_z_degrees=-50.0,
        forearm_right_x_degrees=34.0,
        forearm_right_z_degrees=-38.0,
        hand_right_x_degrees=24.0,
        hand_right_z_degrees=-70.0,
        cloth_left_x_degrees=10.0,
        cloth_center_x_degrees=7.0,
        cloth_right_x_degrees=-9.0,
    ),
    AttackSwordDownPoseDeltaV17(
        frame=5,
        phase="recovery",
        pelvis_z=-0.01,
        pelvis_roll_z_degrees=1.0,
        spine_pitch_x_degrees=-3.0,
        chest_yaw_z_degrees=-10.0,
        head_yaw_z_degrees=3.0,
        thigh_left_x_degrees=2.0,
        thigh_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=3.0,
        upper_arm_left_z_degrees=-2.0,
        forearm_left_x_degrees=4.0,
        forearm_left_z_degrees=-3.0,
        upper_arm_right_x_degrees=8.0,
        upper_arm_right_z_degrees=-12.0,
        forearm_right_x_degrees=10.0,
        forearm_right_z_degrees=-8.0,
        hand_right_x_degrees=8.0,
        hand_right_z_degrees=-18.0,
        cloth_left_x_degrees=3.0,
        cloth_center_x_degrees=2.0,
        cloth_right_x_degrees=-3.0,
    ),
)


TWOHAND_POSES = (
    AttackSwordDownPoseDeltaV17(frame=1, phase="guard"),
    AttackSwordDownPoseDeltaV17(
        frame=2,
        phase="anticipation",
        pelvis_z=-0.015,
        pelvis_roll_z_degrees=-1.0,
        spine_pitch_x_degrees=4.0,
        chest_yaw_z_degrees=8.0,
        head_yaw_z_degrees=-3.0,
        thigh_left_x_degrees=-2.0,
        thigh_right_x_degrees=2.0,
        shin_left_x_degrees=2.0,
        shin_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=-22.0,
        upper_arm_left_z_degrees=-6.0,
        forearm_left_x_degrees=-20.0,
        forearm_left_z_degrees=10.0,
        hand_left_x_degrees=-10.0,
        hand_left_z_degrees=6.0,
        upper_arm_right_x_degrees=-22.0,
        upper_arm_right_z_degrees=6.0,
        forearm_right_x_degrees=-20.0,
        forearm_right_z_degrees=-10.0,
        hand_right_x_degrees=-10.0,
        hand_right_z_degrees=-6.0,
        cloth_left_x_degrees=-3.0,
        cloth_center_x_degrees=-2.0,
        cloth_right_x_degrees=3.0,
    ),
    AttackSwordDownPoseDeltaV17(
        frame=3,
        phase="contact",
        pelvis_z=-0.045,
        pelvis_roll_z_degrees=2.0,
        spine_pitch_x_degrees=-14.0,
        chest_yaw_z_degrees=-6.0,
        head_yaw_z_degrees=3.0,
        thigh_left_x_degrees=5.0,
        thigh_right_x_degrees=5.0,
        shin_left_x_degrees=-5.0,
        shin_right_x_degrees=-5.0,
        foot_left_x_degrees=2.0,
        foot_right_x_degrees=2.0,
        upper_arm_left_x_degrees=38.0,
        upper_arm_left_z_degrees=8.0,
        forearm_left_x_degrees=42.0,
        forearm_left_z_degrees=-14.0,
        hand_left_x_degrees=30.0,
        hand_left_z_degrees=-8.0,
        upper_arm_right_x_degrees=38.0,
        upper_arm_right_z_degrees=-8.0,
        forearm_right_x_degrees=42.0,
        forearm_right_z_degrees=14.0,
        hand_right_x_degrees=30.0,
        hand_right_z_degrees=8.0,
        cloth_left_x_degrees=7.0,
        cloth_center_x_degrees=5.0,
        cloth_right_x_degrees=-7.0,
    ),
    AttackSwordDownPoseDeltaV17(
        frame=4,
        phase="follow_through",
        pelvis_z=-0.05,
        pelvis_roll_z_degrees=3.0,
        spine_pitch_x_degrees=-18.0,
        chest_yaw_z_degrees=-10.0,
        head_yaw_z_degrees=5.0,
        thigh_left_x_degrees=7.0,
        thigh_right_x_degrees=7.0,
        shin_left_x_degrees=-7.0,
        shin_right_x_degrees=-7.0,
        foot_left_x_degrees=3.0,
        foot_right_x_degrees=3.0,
        upper_arm_left_x_degrees=50.0,
        upper_arm_left_z_degrees=12.0,
        forearm_left_x_degrees=48.0,
        forearm_left_z_degrees=-18.0,
        hand_left_x_degrees=38.0,
        hand_left_z_degrees=-12.0,
        upper_arm_right_x_degrees=50.0,
        upper_arm_right_z_degrees=-12.0,
        forearm_right_x_degrees=48.0,
        forearm_right_z_degrees=18.0,
        hand_right_x_degrees=38.0,
        hand_right_z_degrees=12.0,
        cloth_left_x_degrees=10.0,
        cloth_center_x_degrees=8.0,
        cloth_right_x_degrees=-10.0,
    ),
    AttackSwordDownPoseDeltaV17(
        frame=5,
        phase="recovery",
        pelvis_z=-0.02,
        spine_pitch_x_degrees=-6.0,
        chest_yaw_z_degrees=-3.0,
        head_yaw_z_degrees=1.0,
        thigh_left_x_degrees=2.0,
        thigh_right_x_degrees=2.0,
        shin_left_x_degrees=-2.0,
        shin_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=10.0,
        upper_arm_left_z_degrees=3.0,
        forearm_left_x_degrees=12.0,
        forearm_left_z_degrees=-5.0,
        hand_left_x_degrees=8.0,
        hand_left_z_degrees=-3.0,
        upper_arm_right_x_degrees=10.0,
        upper_arm_right_z_degrees=-3.0,
        forearm_right_x_degrees=12.0,
        forearm_right_z_degrees=5.0,
        hand_right_x_degrees=8.0,
        hand_right_z_degrees=3.0,
        cloth_left_x_degrees=4.0,
        cloth_center_x_degrees=3.0,
        cloth_right_x_degrees=-4.0,
    ),
)


HUMAN_WARRIOR_M01_ATTACK_SWORD_DOWN_KEYPOSES_V17 = (
    AttackSwordDownKeyposesProfileV17(
        character_id="human_warrior_m01",
        revision="v17",
        animation_id="attack_sword_01_down_keyposes",
        direction="down",
        fps=ATTACK_KEYPOSE_FPS,
        loop=False,
        frame_order=ATTACK_KEYPOSE_FRAME_ORDER,
        phase_order=ATTACK_KEYPOSE_PHASE_ORDER,
        grips=(
            AttackSwordDownGripV17(
                grip_id="onehand_ready",
                display_name="Одноручный диагональный рубящий удар вниз",
                action_id="attack_sword_01_onehand_down_keyposes_v17",
                stance_variant_id="onehand_ready",
                stance_source_revision="v09_artist_approved",
                weapon_cycle_id="onehand_ready",
                trajectory_id="physical_right_high_to_left_low_diagonal",
                poses=ONEHAND_POSES,
            ),
            AttackSwordDownGripV17(
                grip_id="twohand_center_high",
                display_name="Двуручный тяжёлый нисходящий удар",
                action_id="attack_sword_01_twohand_down_keyposes_v17",
                stance_variant_id="twohand_center_high",
                stance_source_revision="v06_exact_in_v09_artist_approved",
                weapon_cycle_id="twohand_center_high",
                trajectory_id="center_high_to_center_low_heavy_descending",
                poses=TWOHAND_POSES,
            ),
        ),
        appearance_revision="v03",
        head_revision="v22",
        proxy_revision="v25",
        combat_idle_source_revision="directional_cycles_v14_artist_approved",
        directional_weapon_source_revision="directional_weapon_v12_artist_approved",
    )
)


def _all_zero_guard(pose: AttackSwordDownPoseDeltaV17) -> bool:
    return (
        pose.pelvis_x == 0.0
        and pose.pelvis_z == 0.0
        and all(value == 0.0 for value in pose.rotation_deltas())
    )


def load_attack_sword_down_keyposes_profile_v17(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    profile = HUMAN_WARRIOR_M01_ATTACK_SWORD_DOWN_KEYPOSES_V17
    if character_id != profile.character_id:
        raise KeyError(
            f"No sword attack down key-pose v17 profile for character_id={character_id}"
        )
    if profile.revision != "v17" or profile.direction != "down":
        raise ValueError("Sword attack down key-pose v17 identity drifted")
    if profile.fps != ATTACK_KEYPOSE_FPS or profile.loop:
        raise ValueError("Sword attack down key poses must remain a non-looping 6 FPS review")
    if profile.frame_order != ATTACK_KEYPOSE_FRAME_ORDER:
        raise ValueError("Sword attack down key-pose frame order drifted")
    if profile.phase_order != ATTACK_KEYPOSE_PHASE_ORDER:
        raise ValueError("Sword attack down key-pose phase order drifted")
    if tuple(item.grip_id for item in profile.grips) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Sword attack down key-pose grip order drifted")
    if profile.appearance_revision != "v03":
        raise ValueError("Sword attack down key poses lost approved appearance v03")
    if profile.head_revision != "v22" or profile.proxy_revision != "v25":
        raise ValueError("Sword attack down key poses require head v22 / proxy v25")

    stance_profile = load_weapon_stance_profile_v09(character_id)
    stance_by_id = {item.variant_id: item for item in stance_profile.variants}
    for grip in profile.grips:
        stance = stance_by_id.get(grip.stance_variant_id)
        if stance is None:
            raise ValueError(f"Missing approved source stance: {grip.stance_variant_id}")
        if tuple(pose.frame for pose in grip.poses) != profile.frame_order:
            raise ValueError(f"Frame order drifted for {grip.grip_id}")
        if tuple(pose.phase for pose in grip.poses) != profile.phase_order:
            raise ValueError(f"Phase order drifted for {grip.grip_id}")
        if not _all_zero_guard(grip.poses[0]):
            raise ValueError(f"Guard pose must exactly preserve source stance: {grip.grip_id}")
        for pose in grip.poses:
            if abs(pose.pelvis_x) > MAX_PELVIS_TRANSLATION:
                raise ValueError(f"Pelvis X delta is excessive: {grip.grip_id}/{pose.phase}")
            if abs(pose.pelvis_z) > MAX_PELVIS_TRANSLATION:
                raise ValueError(f"Pelvis Z delta is excessive: {grip.grip_id}/{pose.phase}")
            if max(abs(value) for value in pose.rotation_deltas()) > MAX_ROTATION_DELTA_DEGREES:
                raise ValueError(f"Rotation delta is excessive: {grip.grip_id}/{pose.phase}")

        if grip.grip_id == "onehand_ready":
            if stance.grip_mode != "one_handed" or stance.blade_tip != "down":
                raise ValueError("One-hand attack lost the approved one-handed source")
            for pose in grip.poses:
                if stance.pose.upper_arm_left_z_degrees + pose.upper_arm_left_z_degrees < 15.0:
                    raise ValueError(
                        f"One-hand free arm collapsed into torso: {pose.phase}"
                    )
            if grip.trajectory_id != "physical_right_high_to_left_low_diagonal":
                raise ValueError("One-hand attack trajectory drifted")
        elif grip.grip_id == "twohand_center_high":
            if stance.grip_mode != "two_handed" or stance.blade_tip != "up":
                raise ValueError("Two-hand attack lost the approved two-handed source")
            for pose in grip.poses:
                if abs(pose.upper_arm_left_x_degrees - pose.upper_arm_right_x_degrees) > 0.001:
                    raise ValueError(f"Two-hand upper-arm timing lost symmetry: {pose.phase}")
                if abs(pose.forearm_left_x_degrees - pose.forearm_right_x_degrees) > 0.001:
                    raise ValueError(f"Two-hand forearm timing lost symmetry: {pose.phase}")
            if grip.trajectory_id != "center_high_to_center_low_heavy_descending":
                raise ValueError("Two-hand attack trajectory drifted")
        else:
            raise ValueError(f"Unknown attack grip: {grip.grip_id}")
    return profile
