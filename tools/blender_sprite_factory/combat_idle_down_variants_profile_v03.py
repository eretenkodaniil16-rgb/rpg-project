from __future__ import annotations

from combat_idle_down_profile_v01 import (
    CombatIdleDownPoseV01,
    HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01,
)
from combat_idle_down_variants_profile_v02 import (
    CombatIdleDownVariantV02,
    CombatIdleDownVariantsProfileV02,
)


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


HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_VARIANTS_V03 = CombatIdleDownVariantsProfileV02(
    character_id="human_warrior_m01",
    revision="v03",
    direction="down",
    weapon_id="sword_01",
    weapon_hand="right",
    variants=(
        CombatIdleDownVariantV02(
            variant_id="center_low",
            display_name="Низкая центральная защита",
            animation_id="combat_idle_center_low_v03",
            pose=_pose(
                phase="center_low",
                pelvis_x=0.0,
                pelvis_z=-0.060,
                pelvis_roll_z_degrees=1.0,
                spine_pitch_x_degrees=-3.0,
                chest_yaw_z_degrees=-3.0,
                head_yaw_z_degrees=2.0,
                upper_arm_left_x_degrees=-10.0,
                upper_arm_left_z_degrees=12.0,
                forearm_left_x_degrees=-16.0,
                forearm_left_z_degrees=-8.0,
                upper_arm_right_x_degrees=-20.0,
                upper_arm_right_z_degrees=-12.0,
                forearm_right_x_degrees=-26.0,
                forearm_right_z_degrees=8.0,
                hand_right_x_degrees=-8.0,
                hand_right_z_degrees=-14.0,
            ),
        ),
        CombatIdleDownVariantV02(
            variant_id="center_mid",
            display_name="Средняя центральная защита",
            animation_id="combat_idle_center_mid_v03",
            pose=_pose(
                phase="center_mid",
                pelvis_x=-0.01,
                pelvis_z=-0.065,
                pelvis_roll_z_degrees=0.0,
                spine_pitch_x_degrees=-4.0,
                chest_yaw_z_degrees=-1.0,
                head_yaw_z_degrees=1.0,
                upper_arm_left_x_degrees=-12.0,
                upper_arm_left_z_degrees=14.0,
                forearm_left_x_degrees=-16.0,
                forearm_left_z_degrees=-10.0,
                upper_arm_right_x_degrees=-18.0,
                upper_arm_right_z_degrees=-15.0,
                forearm_right_x_degrees=-22.0,
                forearm_right_z_degrees=11.0,
                hand_right_x_degrees=-4.0,
                hand_right_z_degrees=-18.0,
            ),
        ),
        CombatIdleDownVariantV02(
            variant_id="center_vertical",
            display_name="Вертикальная центральная защита",
            animation_id="combat_idle_center_vertical_v03",
            pose=_pose(
                phase="center_vertical",
                pelvis_x=0.0,
                pelvis_z=-0.070,
                pelvis_roll_z_degrees=-1.0,
                spine_pitch_x_degrees=-5.0,
                chest_yaw_z_degrees=1.0,
                head_yaw_z_degrees=0.0,
                upper_arm_left_x_degrees=-14.0,
                upper_arm_left_z_degrees=15.0,
                forearm_left_x_degrees=-14.0,
                forearm_left_z_degrees=-12.0,
                upper_arm_right_x_degrees=-16.0,
                upper_arm_right_z_degrees=-18.0,
                forearm_right_x_degrees=-19.0,
                forearm_right_z_degrees=14.0,
                hand_right_x_degrees=0.0,
                hand_right_z_degrees=-22.0,
            ),
        ),
    ),
)


def load_combat_idle_down_variants_profile_v03(
    character_id: str,
) -> CombatIdleDownVariantsProfileV02:
    profile = HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_VARIANTS_V03
    if character_id != profile.character_id:
        raise KeyError(
            f"No combat_idle_down variants v03 profile for character_id={character_id}"
        )
    if profile.revision != "v03":
        raise ValueError("Combat idle centered variants revision must be v03")
    if tuple(item.variant_id for item in profile.variants) != (
        "center_low",
        "center_mid",
        "center_vertical",
    ):
        raise ValueError("Combat idle centered variant order drifted")
    baseline = HUMAN_WARRIOR_M01_COMBAT_IDLE_DOWN_V01.pose
    for item in profile.variants:
        pose = item.pose
        if pose.frame != 1 or pose.phase != item.variant_id:
            raise ValueError(f"Variant {item.variant_id} must be one named static frame")
        if pose.upper_arm_left_z_degrees <= baseline.upper_arm_left_z_degrees:
            raise ValueError(f"Variant {item.variant_id} must keep the left arm open")
        if pose.hand_right_z_degrees >= baseline.hand_right_z_degrees:
            raise ValueError(f"Variant {item.variant_id} must rotate the blade inward")
        if abs(pose.upper_arm_left_x_degrees) > 18.0:
            raise ValueError(f"Variant {item.variant_id} overdrives the left pauldron")
        if max(abs(value) for value in pose.numeric_channels()) > 42.0:
            raise ValueError(f"Variant {item.variant_id} exceeds the safe pose budget")
    return profile
