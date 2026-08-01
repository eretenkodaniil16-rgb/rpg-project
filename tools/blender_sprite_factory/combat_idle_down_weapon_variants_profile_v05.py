from __future__ import annotations

from dataclasses import dataclass

from combat_idle_down_profile_v01 import CombatIdleDownPoseV01


@dataclass(frozen=True)
class WeaponStanceVariantV05:
    variant_id: str
    display_name: str
    animation_id: str
    grip_mode: str
    weapon_id: str
    blade_tip: str
    pose: CombatIdleDownPoseV01
    hand_left_x_degrees: float
    hand_left_z_degrees: float


@dataclass(frozen=True)
class WeaponStanceProfileV05:
    character_id: str
    revision: str
    direction: str
    variants: tuple[WeaponStanceVariantV05, ...]


ONE_HAND_BLADE_LENGTH = 1.82
TWO_HAND_BLADE_LENGTH = 2.12
ONE_HAND_GRIP_LENGTH = 0.52
TWO_HAND_GRIP_LENGTH = 0.92


def _pose(
    *,
    phase: str,
    pelvis_x: float,
    pelvis_z: float,
    pelvis_roll_z_degrees: float,
    spine_pitch_x_degrees: float,
    chest_yaw_z_degrees: float,
    head_yaw_z_degrees: float,
    upper_arm_left_x_degrees: float,
    upper_arm_left_z_degrees: float,
    forearm_left_x_degrees: float,
    forearm_left_z_degrees: float,
    upper_arm_right_x_degrees: float,
    upper_arm_right_z_degrees: float,
    forearm_right_x_degrees: float,
    forearm_right_z_degrees: float,
    hand_right_x_degrees: float,
    hand_right_z_degrees: float,
) -> CombatIdleDownPoseV01:
    return CombatIdleDownPoseV01(
        frame=1,
        phase=phase,
        pelvis_x=pelvis_x,
        pelvis_z=pelvis_z,
        pelvis_roll_z_degrees=pelvis_roll_z_degrees,
        spine_pitch_x_degrees=spine_pitch_x_degrees,
        chest_yaw_z_degrees=chest_yaw_z_degrees,
        head_yaw_z_degrees=head_yaw_z_degrees,
        thigh_left_x_degrees=6.0,
        thigh_right_x_degrees=4.0,
        thigh_left_z_degrees=5.0,
        thigh_right_z_degrees=-6.0,
        shin_left_x_degrees=-8.0,
        shin_right_x_degrees=-10.0,
        foot_left_x_degrees=3.0,
        foot_right_x_degrees=4.0,
        upper_arm_left_x_degrees=upper_arm_left_x_degrees,
        upper_arm_left_z_degrees=upper_arm_left_z_degrees,
        forearm_left_x_degrees=forearm_left_x_degrees,
        forearm_left_z_degrees=forearm_left_z_degrees,
        upper_arm_right_x_degrees=upper_arm_right_x_degrees,
        upper_arm_right_z_degrees=upper_arm_right_z_degrees,
        forearm_right_x_degrees=forearm_right_x_degrees,
        forearm_right_z_degrees=forearm_right_z_degrees,
        hand_right_x_degrees=hand_right_x_degrees,
        hand_right_z_degrees=hand_right_z_degrees,
        cloth_left_x_degrees=1.5,
        cloth_center_x_degrees=0.0,
        cloth_right_x_degrees=-1.5,
    )


HUMAN_WARRIOR_M01_WEAPON_STANCES_V05 = WeaponStanceProfileV05(
    character_id="human_warrior_m01",
    revision="v05",
    direction="down",
    variants=(
        WeaponStanceVariantV05(
            variant_id="onehand_low",
            display_name="Одноручная боковая низкая",
            animation_id="combat_idle_onehand_low_v05",
            grip_mode="one_handed",
            weapon_id="sword_01_onehand_long",
            blade_tip="down",
            pose=_pose(
                phase="onehand_low",
                pelvis_x=0.01,
                pelvis_z=-0.060,
                pelvis_roll_z_degrees=1.5,
                spine_pitch_x_degrees=-3.0,
                chest_yaw_z_degrees=-5.0,
                head_yaw_z_degrees=3.0,
                upper_arm_left_x_degrees=-8.0,
                upper_arm_left_z_degrees=27.0,
                forearm_left_x_degrees=-8.0,
                forearm_left_z_degrees=12.0,
                upper_arm_right_x_degrees=-19.0,
                upper_arm_right_z_degrees=18.0,
                forearm_right_x_degrees=-22.0,
                forearm_right_z_degrees=-4.0,
                hand_right_x_degrees=-8.0,
                hand_right_z_degrees=14.0,
            ),
            hand_left_x_degrees=0.0,
            hand_left_z_degrees=8.0,
        ),
        WeaponStanceVariantV05(
            variant_id="onehand_ready",
            display_name="Одноручная боковая боевая",
            animation_id="combat_idle_onehand_ready_v05",
            grip_mode="one_handed",
            weapon_id="sword_01_onehand_long",
            blade_tip="down",
            pose=_pose(
                phase="onehand_ready",
                pelvis_x=0.0,
                pelvis_z=-0.065,
                pelvis_roll_z_degrees=0.0,
                spine_pitch_x_degrees=-4.0,
                chest_yaw_z_degrees=-2.0,
                head_yaw_z_degrees=1.0,
                upper_arm_left_x_degrees=-10.0,
                upper_arm_left_z_degrees=31.0,
                forearm_left_x_degrees=-7.0,
                forearm_left_z_degrees=16.0,
                upper_arm_right_x_degrees=-16.0,
                upper_arm_right_z_degrees=23.0,
                forearm_right_x_degrees=-18.0,
                forearm_right_z_degrees=-7.0,
                hand_right_x_degrees=-3.0,
                hand_right_z_degrees=19.0,
            ),
            hand_left_x_degrees=0.0,
            hand_left_z_degrees=12.0,
        ),
        WeaponStanceVariantV05(
            variant_id="twohand_center_low",
            display_name="Двуручная центральная низкая",
            animation_id="combat_idle_twohand_center_low_v05",
            grip_mode="two_handed",
            weapon_id="sword_02_twohand_long",
            blade_tip="up",
            pose=_pose(
                phase="twohand_center_low",
                pelvis_x=0.0,
                pelvis_z=-0.070,
                pelvis_roll_z_degrees=0.0,
                spine_pitch_x_degrees=-5.0,
                chest_yaw_z_degrees=0.0,
                head_yaw_z_degrees=0.0,
                upper_arm_left_x_degrees=-15.0,
                upper_arm_left_z_degrees=-8.0,
                forearm_left_x_degrees=-20.0,
                forearm_left_z_degrees=18.0,
                upper_arm_right_x_degrees=-15.0,
                upper_arm_right_z_degrees=-8.0,
                forearm_right_x_degrees=-20.0,
                forearm_right_z_degrees=-18.0,
                hand_right_x_degrees=6.0,
                hand_right_z_degrees=-5.0,
            ),
            hand_left_x_degrees=-6.0,
            hand_left_z_degrees=5.0,
        ),
        WeaponStanceVariantV05(
            variant_id="twohand_center_high",
            display_name="Двуручная центральная высокая",
            animation_id="combat_idle_twohand_center_high_v05",
            grip_mode="two_handed",
            weapon_id="sword_02_twohand_long",
            blade_tip="up",
            pose=_pose(
                phase="twohand_center_high",
                pelvis_x=0.0,
                pelvis_z=-0.065,
                pelvis_roll_z_degrees=0.0,
                spine_pitch_x_degrees=-3.0,
                chest_yaw_z_degrees=0.0,
                head_yaw_z_degrees=0.0,
                upper_arm_left_x_degrees=-20.0,
                upper_arm_left_z_degrees=-10.0,
                forearm_left_x_degrees=-16.0,
                forearm_left_z_degrees=20.0,
                upper_arm_right_x_degrees=-20.0,
                upper_arm_right_z_degrees=-10.0,
                forearm_right_x_degrees=-16.0,
                forearm_right_z_degrees=-20.0,
                hand_right_x_degrees=2.0,
                hand_right_z_degrees=-4.0,
            ),
            hand_left_x_degrees=-2.0,
            hand_left_z_degrees=4.0,
        ),
    ),
)


def load_weapon_stance_profile_v05(character_id: str) -> WeaponStanceProfileV05:
    profile = HUMAN_WARRIOR_M01_WEAPON_STANCES_V05
    if character_id != profile.character_id:
        raise KeyError(f"No weapon stance v05 profile for character_id={character_id}")
    if profile.revision != "v05" or profile.direction != "down":
        raise ValueError("Weapon stance v05 identity drifted")
    expected_ids = (
        "onehand_low",
        "onehand_ready",
        "twohand_center_low",
        "twohand_center_high",
    )
    if tuple(item.variant_id for item in profile.variants) != expected_ids:
        raise ValueError("Weapon stance v05 order drifted")
    for item in profile.variants:
        if item.pose.frame != 1 or item.pose.phase != item.variant_id:
            raise ValueError(f"Variant {item.variant_id} must be one named static frame")
        if item.grip_mode == "one_handed":
            if item.blade_tip != "down" or item.pose.upper_arm_left_z_degrees < 26.0:
                raise ValueError(f"Variant {item.variant_id} must keep the free arm away")
        elif item.grip_mode == "two_handed":
            if item.blade_tip != "up" or not item.weapon_id.startswith("sword_02"):
                raise ValueError(f"Variant {item.variant_id} must use the centered two-hand sword")
        else:
            raise ValueError(f"Unknown grip mode: {item.grip_mode}")
        if max(
            max(abs(value) for value in item.pose.numeric_channels()),
            abs(item.hand_left_x_degrees),
            abs(item.hand_left_z_degrees),
        ) > 42.0:
            raise ValueError(f"Variant {item.variant_id} exceeds the safe pose budget")
    if ONE_HAND_BLADE_LENGTH <= 1.34:
        raise ValueError("One-hand sword must be longer than the v01 blade")
    if TWO_HAND_BLADE_LENGTH <= ONE_HAND_BLADE_LENGTH:
        raise ValueError("Two-hand sword must be longer than the one-hand sword")
    return profile
