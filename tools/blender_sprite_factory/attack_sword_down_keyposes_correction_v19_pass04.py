from __future__ import annotations

from dataclasses import replace

from attack_sword_down_keyposes_correction_v19_pass03 import (
    load_attack_sword_down_keyposes_profile_v19_pass03,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
)


CORRECTION_PASS = "v19_pass04"
TWOHAND_ANTICIPATION_REVISION = "raised_outside_head_windup_v19_pass04"


def load_attack_sword_down_keyposes_profile_v19_pass04(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v19_pass03(character_id)
    onehand, twohand = source.grips
    guard, anticipation, contact, follow, recovery = twohand.poses
    raised_anticipation = replace(
        anticipation,
        pelvis_x=0.010,
        pelvis_z=-0.010,
        pelvis_roll_z_degrees=-2.0,
        spine_pitch_x_degrees=4.0,
        chest_yaw_z_degrees=16.0,
        head_yaw_z_degrees=-8.0,
        upper_arm_left_x_degrees=-14.0,
        upper_arm_left_z_degrees=-18.0,
        forearm_left_x_degrees=-12.0,
        forearm_left_z_degrees=-4.0,
        hand_left_x_degrees=-10.0,
        hand_left_z_degrees=-8.0,
        upper_arm_right_x_degrees=-14.0,
        upper_arm_right_z_degrees=-8.0,
        forearm_right_x_degrees=-12.0,
        forearm_right_z_degrees=-22.0,
        hand_right_x_degrees=-10.0,
        hand_right_z_degrees=-18.0,
        cloth_left_x_degrees=-3.0,
        cloth_center_x_degrees=-2.0,
        cloth_right_x_degrees=3.0,
    )
    corrected_twohand = replace(
        twohand,
        poses=(guard, raised_anticipation, contact, follow, recovery),
    )
    corrected = replace(source, grips=(onehand, corrected_twohand))

    if corrected.grips[0] != source.grips[0]:
        raise ValueError("One-hand v19 trajectory changed in pass04")
    if corrected_twohand.poses[0] != source.grips[1].poses[0]:
        raise ValueError("Two-hand approved guard changed in pass04")
    if corrected_twohand.poses[2:] != source.grips[1].poses[2:]:
        raise ValueError("Two-hand contact/recovery phases changed in pass04")
    if raised_anticipation.upper_arm_left_x_degrees != raised_anticipation.upper_arm_right_x_degrees:
        raise ValueError("Two-hand v19 pass04 upper arms lost paired elevation")
    if raised_anticipation.forearm_left_x_degrees != raised_anticipation.forearm_right_x_degrees:
        raise ValueError("Two-hand v19 pass04 forearms lost paired elevation")
    if raised_anticipation.hand_right_z_degrees >= -12.0:
        raise ValueError("Two-hand v19 pass04 wind-up is not outside the head")
    if raised_anticipation.upper_arm_right_x_degrees >= -10.0:
        raise ValueError("Two-hand v19 pass04 wind-up was not raised")
    return corrected
