from __future__ import annotations

from dataclasses import dataclass, fields, replace

from attack_sword_down_keyposes_correction_v19_pass03 import (
    load_attack_sword_down_keyposes_profile_v19_pass03,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
    AttackSwordDownPoseDeltaV17,
)


CORRECTION_PASS = "v19_pass05"
TWOHAND_ANTICIPATION_REVISION = "foreshortened_depth_windup_v19_pass05"
DEPTH_ROTATION_DEGREES = 46.0


@dataclass(frozen=True)
class AttackSwordDownPoseDeltaV19(AttackSwordDownPoseDeltaV17):
    upper_arm_left_y_degrees: float = 0.0
    forearm_left_y_degrees: float = 0.0
    hand_left_y_degrees: float = 0.0
    upper_arm_right_y_degrees: float = 0.0
    forearm_right_y_degrees: float = 0.0
    hand_right_y_degrees: float = 0.0

    def depth_rotation_deltas(self) -> tuple[float, ...]:
        return (
            self.upper_arm_left_y_degrees,
            self.forearm_left_y_degrees,
            self.hand_left_y_degrees,
            self.upper_arm_right_y_degrees,
            self.forearm_right_y_degrees,
            self.hand_right_y_degrees,
        )


def _with_depth_rotation(
    source: AttackSwordDownPoseDeltaV17,
    *,
    upper_arm_y_degrees: float,
    forearm_y_degrees: float,
    hand_y_degrees: float,
) -> AttackSwordDownPoseDeltaV19:
    source_payload = {
        field.name: getattr(source, field.name)
        for field in fields(AttackSwordDownPoseDeltaV17)
    }
    return AttackSwordDownPoseDeltaV19(
        **source_payload,
        upper_arm_left_y_degrees=upper_arm_y_degrees,
        forearm_left_y_degrees=forearm_y_degrees,
        hand_left_y_degrees=hand_y_degrees,
        upper_arm_right_y_degrees=upper_arm_y_degrees,
        forearm_right_y_degrees=forearm_y_degrees,
        hand_right_y_degrees=hand_y_degrees,
    )


def load_attack_sword_down_keyposes_profile_v19_pass05(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v19_pass03(character_id)
    onehand, twohand = source.grips
    guard, anticipation, contact, follow, recovery = twohand.poses
    depth_anticipation = _with_depth_rotation(
        anticipation,
        upper_arm_y_degrees=6.0,
        forearm_y_degrees=14.0,
        hand_y_degrees=DEPTH_ROTATION_DEGREES,
    )
    corrected_twohand = replace(
        twohand,
        poses=(guard, depth_anticipation, contact, follow, recovery),
    )
    corrected = replace(source, grips=(onehand, corrected_twohand))

    if corrected.grips[0] != source.grips[0]:
        raise ValueError("One-hand v19 trajectory changed in pass05")
    if corrected_twohand.poses[0] != source.grips[1].poses[0]:
        raise ValueError("Two-hand approved guard changed in pass05")
    if corrected_twohand.poses[2:] != source.grips[1].poses[2:]:
        raise ValueError("Two-hand contact/recovery phases changed in pass05")
    for field in fields(AttackSwordDownPoseDeltaV17):
        if getattr(depth_anticipation, field.name) != getattr(anticipation, field.name):
            raise ValueError(
                f"Two-hand v19 pass05 changed non-depth field: {field.name}"
            )
    if depth_anticipation.hand_left_y_degrees != depth_anticipation.hand_right_y_degrees:
        raise ValueError("Two-hand v19 pass05 hands lost paired depth rotation")
    if depth_anticipation.forearm_left_y_degrees != depth_anticipation.forearm_right_y_degrees:
        raise ValueError("Two-hand v19 pass05 forearms lost paired depth rotation")
    if max(abs(value) for value in depth_anticipation.depth_rotation_deltas()) > 55.0:
        raise ValueError("Two-hand v19 pass05 depth rotation exceeds safe limit")
    if abs(depth_anticipation.hand_right_y_degrees) < 35.0:
        raise ValueError("Two-hand v19 pass05 does not sufficiently foreshorten the sword")
    return corrected
