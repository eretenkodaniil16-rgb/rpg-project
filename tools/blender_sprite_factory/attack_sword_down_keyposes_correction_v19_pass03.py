from __future__ import annotations

from dataclasses import replace

from attack_sword_down_keyposes_correction_v19_pass02 import (
    load_attack_sword_down_keyposes_profile_v19_pass02,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
)


CORRECTION_PASS = "v19_pass03"
ONEHAND_FOLLOW_CONTAINMENT_REVISION = "cross_body_low_follow_v19_pass03"


def load_attack_sword_down_keyposes_profile_v19_pass03(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v19_pass02(character_id)
    onehand, twohand = source.grips
    guard, anticipation, contact, follow, recovery = onehand.poses
    contained_follow = replace(
        follow,
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
        foot_left_x_degrees=0.0,
        foot_right_x_degrees=0.0,
        upper_arm_left_x_degrees=2.0,
        upper_arm_left_z_degrees=8.0,
        forearm_left_x_degrees=3.0,
        forearm_left_z_degrees=4.0,
        hand_left_x_degrees=0.0,
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
    )
    corrected_onehand = replace(
        onehand,
        poses=(guard, anticipation, contact, contained_follow, recovery),
    )
    corrected = replace(source, grips=(corrected_onehand, twohand))

    _guard, corrected_anticipation, corrected_contact, corrected_follow, _recovery = corrected_onehand.poses
    if not (
        corrected_anticipation.hand_right_z_degrees
        < corrected_contact.hand_right_z_degrees
        < corrected_follow.hand_right_z_degrees
    ):
        raise ValueError("One-hand v19 pass03 lost the high-to-low sword arc")
    if corrected_follow.hand_right_z_degrees > 32.0:
        raise ValueError("One-hand v19 pass03 follow-through remains too lateral")
    if corrected_contact.chest_yaw_z_degrees >= 0.0:
        raise ValueError("One-hand v19 pass03 contact must remain on the wind-up side")
    if corrected_follow.chest_yaw_z_degrees <= 0.0:
        raise ValueError("One-hand v19 pass03 follow-through did not carry across the body")
    if corrected_follow.pelvis_x < 0.0:
        raise ValueError("One-hand v19 pass03 did not restore frame-centred follow-through")
    if corrected.grips[1] != source.grips[1]:
        raise ValueError("Two-hand v19 trajectory changed in pass03")
    return corrected
