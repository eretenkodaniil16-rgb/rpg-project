from __future__ import annotations

from dataclasses import replace

from attack_sword_down_keyposes_correction_v19_pass02 import (
    load_attack_sword_down_keyposes_profile_v19_pass02,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
)


CORRECTION_PASS = "v19_pass03"
ONEHAND_FOLLOW_CONTAINMENT_REVISION = "inward_follow_clear_canvas_v19_pass03"


def load_attack_sword_down_keyposes_profile_v19_pass03(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v19_pass02(character_id)
    onehand, twohand = source.grips
    guard, anticipation, contact, follow, recovery = onehand.poses
    contained_follow = replace(
        follow,
        pelvis_x=0.0,
        upper_arm_right_x_degrees=-14.0,
        upper_arm_right_z_degrees=6.0,
        forearm_right_x_degrees=-18.0,
        forearm_right_z_degrees=-6.0,
        hand_right_x_degrees=-12.0,
        hand_right_z_degrees=20.0,
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
    if corrected_follow.hand_right_z_degrees >= 24.0:
        raise ValueError("One-hand v19 pass03 follow-through remains too lateral")
    if corrected_follow.pelvis_x < -0.001:
        raise ValueError("One-hand v19 pass03 did not restore frame-centred follow-through")
    if corrected.grips[1] != source.grips[1]:
        raise ValueError("Two-hand v19 trajectory changed in pass03")
    return corrected
