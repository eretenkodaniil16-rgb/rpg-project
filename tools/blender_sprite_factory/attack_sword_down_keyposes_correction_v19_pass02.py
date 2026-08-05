from __future__ import annotations

from dataclasses import replace

from attack_sword_down_keyposes_correction_v19 import (
    load_attack_sword_down_keyposes_profile_v19,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
    AttackSwordDownPoseDeltaV17,
)


CORRECTION_PASS = "v19_pass02"
ONEHAND_CONTACT_REVISION = "diagonal_down_contact_v19_pass02"
ONEHAND_FOLLOW_REVISION = "low_follow_without_torso_reversal_v19_pass02"


def _correct_onehand_contact(
    source: AttackSwordDownPoseDeltaV17,
) -> AttackSwordDownPoseDeltaV17:
    return replace(
        source,
        pelvis_x=-0.010,
        pelvis_z=-0.025,
        pelvis_roll_z_degrees=2.5,
        spine_pitch_x_degrees=-6.0,
        chest_yaw_z_degrees=-16.0,
        head_yaw_z_degrees=6.0,
        thigh_left_x_degrees=4.0,
        thigh_right_x_degrees=-4.0,
        shin_left_x_degrees=-3.0,
        shin_right_x_degrees=3.0,
        foot_left_x_degrees=1.0,
        foot_right_x_degrees=-1.0,
        upper_arm_left_x_degrees=6.0,
        upper_arm_left_z_degrees=-6.0,
        forearm_left_x_degrees=9.0,
        forearm_left_z_degrees=-8.0,
        hand_left_x_degrees=4.0,
        hand_left_z_degrees=-5.0,
        upper_arm_right_x_degrees=-4.0,
        upper_arm_right_z_degrees=-18.0,
        forearm_right_x_degrees=-8.0,
        forearm_right_z_degrees=-10.0,
        hand_right_x_degrees=-6.0,
        hand_right_z_degrees=8.0,
        cloth_left_x_degrees=6.0,
        cloth_center_x_degrees=4.0,
        cloth_right_x_degrees=-5.0,
    )


def _correct_onehand_follow(
    source: AttackSwordDownPoseDeltaV17,
) -> AttackSwordDownPoseDeltaV17:
    return replace(
        source,
        pelvis_x=-0.015,
        pelvis_z=-0.030,
        pelvis_roll_z_degrees=4.0,
        spine_pitch_x_degrees=-10.0,
        chest_yaw_z_degrees=-22.0,
        head_yaw_z_degrees=8.0,
        thigh_left_x_degrees=6.0,
        thigh_right_x_degrees=-5.0,
        shin_left_x_degrees=-5.0,
        shin_right_x_degrees=4.0,
        foot_left_x_degrees=2.0,
        foot_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=10.0,
        upper_arm_left_z_degrees=-12.0,
        forearm_left_x_degrees=14.0,
        forearm_left_z_degrees=-14.0,
        hand_left_x_degrees=6.0,
        hand_left_z_degrees=-10.0,
        upper_arm_right_x_degrees=-16.0,
        upper_arm_right_z_degrees=10.0,
        forearm_right_x_degrees=-20.0,
        forearm_right_z_degrees=-10.0,
        hand_right_x_degrees=-14.0,
        hand_right_z_degrees=28.0,
        cloth_left_x_degrees=8.0,
        cloth_center_x_degrees=6.0,
        cloth_right_x_degrees=-7.0,
    )


def load_attack_sword_down_keyposes_profile_v19_pass02(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v19(character_id)
    onehand, twohand = source.grips
    guard, anticipation, contact, follow, recovery = onehand.poses
    corrected_onehand = replace(
        onehand,
        poses=(
            guard,
            anticipation,
            _correct_onehand_contact(contact),
            _correct_onehand_follow(follow),
            recovery,
        ),
    )
    corrected = replace(source, grips=(corrected_onehand, twohand))

    _guard, corrected_anticipation, corrected_contact, corrected_follow, corrected_recovery = corrected_onehand.poses
    if not (
        corrected_anticipation.hand_right_z_degrees
        < corrected_contact.hand_right_z_degrees
        < corrected_follow.hand_right_z_degrees
    ):
        raise ValueError("One-hand v19 pass02 lost the high-to-low sword arc")
    if corrected_contact.upper_arm_right_x_degrees >= 0.0:
        raise ValueError("One-hand v19 pass02 contact did not descend")
    if corrected_follow.upper_arm_right_x_degrees >= corrected_contact.upper_arm_right_x_degrees:
        raise ValueError("One-hand v19 pass02 follow-through is not lower than contact")
    if corrected_contact.chest_yaw_z_degrees >= 0.0 or corrected_follow.chest_yaw_z_degrees >= 0.0:
        raise ValueError("One-hand v19 pass02 torso reverses during the strike")
    if abs(corrected_recovery.hand_right_z_degrees) > 8.0:
        raise ValueError("One-hand v19 pass02 recovery drifted from guard")
    return corrected
