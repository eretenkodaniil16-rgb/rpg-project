from __future__ import annotations

from dataclasses import replace

from attack_sword_down_keyposes_correction_v18 import (
    load_attack_sword_down_keyposes_profile_v18,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
    AttackSwordDownPoseDeltaV17,
)


CORRECTION_REVISION = "v19"
ONEHAND_TRAJECTORY_REVISION = "continuous_diagonal_cut_v19"
TWOHAND_TRAJECTORY_REVISION = "outside_head_descending_arc_v19"
MIN_TWOHAND_HEAD_CLEARANCE_PIXELS = 4.0


def _correct_onehand_poses(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
) -> tuple[AttackSwordDownPoseDeltaV17, ...]:
    guard, anticipation, contact, follow, recovery = poses
    corrected_anticipation = replace(
        anticipation,
        pelvis_x=-0.015,
        pelvis_z=-0.012,
        pelvis_roll_z_degrees=-2.0,
        spine_pitch_x_degrees=1.5,
        chest_yaw_z_degrees=-20.0,
        head_yaw_z_degrees=7.0,
        thigh_left_x_degrees=-2.0,
        thigh_right_x_degrees=2.0,
        shin_left_x_degrees=1.0,
        shin_right_x_degrees=-1.0,
        upper_arm_left_x_degrees=3.0,
        upper_arm_left_z_degrees=10.0,
        forearm_left_x_degrees=4.0,
        forearm_left_z_degrees=6.0,
        hand_left_x_degrees=1.0,
        hand_left_z_degrees=5.0,
        upper_arm_right_x_degrees=26.0,
        upper_arm_right_z_degrees=-34.0,
        forearm_right_x_degrees=32.0,
        forearm_right_z_degrees=-22.0,
        hand_right_x_degrees=24.0,
        hand_right_z_degrees=-46.0,
        cloth_left_x_degrees=-3.0,
        cloth_center_x_degrees=-2.0,
        cloth_right_x_degrees=3.0,
    )
    corrected_contact = replace(
        contact,
        pelvis_x=-0.015,
        pelvis_z=-0.025,
        pelvis_roll_z_degrees=3.0,
        spine_pitch_x_degrees=-7.0,
        chest_yaw_z_degrees=-18.0,
        head_yaw_z_degrees=7.0,
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
        upper_arm_right_x_degrees=22.0,
        upper_arm_right_z_degrees=-24.0,
        forearm_right_x_degrees=26.0,
        forearm_right_z_degrees=-14.0,
        hand_right_x_degrees=20.0,
        hand_right_z_degrees=0.0,
        cloth_left_x_degrees=6.0,
        cloth_center_x_degrees=4.0,
        cloth_right_x_degrees=-5.0,
    )
    corrected_follow = replace(
        follow,
        pelvis_x=-0.020,
        pelvis_z=-0.030,
        pelvis_roll_z_degrees=4.0,
        spine_pitch_x_degrees=-10.0,
        chest_yaw_z_degrees=-24.0,
        head_yaw_z_degrees=9.0,
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
        upper_arm_right_x_degrees=16.0,
        upper_arm_right_z_degrees=-8.0,
        forearm_right_x_degrees=12.0,
        forearm_right_z_degrees=2.0,
        hand_right_x_degrees=8.0,
        hand_right_z_degrees=34.0,
        cloth_left_x_degrees=8.0,
        cloth_center_x_degrees=6.0,
        cloth_right_x_degrees=-7.0,
    )
    corrected_recovery = replace(
        recovery,
        pelvis_z=-0.004,
        pelvis_roll_z_degrees=0.5,
        spine_pitch_x_degrees=-1.0,
        chest_yaw_z_degrees=-3.0,
        head_yaw_z_degrees=1.0,
        upper_arm_left_x_degrees=1.0,
        upper_arm_left_z_degrees=-0.5,
        forearm_left_x_degrees=1.5,
        forearm_left_z_degrees=-1.0,
        upper_arm_right_x_degrees=3.0,
        upper_arm_right_z_degrees=-3.0,
        forearm_right_x_degrees=4.0,
        forearm_right_z_degrees=-2.0,
        hand_right_x_degrees=3.0,
        hand_right_z_degrees=-4.0,
        cloth_left_x_degrees=1.0,
        cloth_center_x_degrees=0.5,
        cloth_right_x_degrees=-1.0,
    )
    return (
        guard,
        corrected_anticipation,
        corrected_contact,
        corrected_follow,
        corrected_recovery,
    )


def _correct_twohand_poses(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
) -> tuple[AttackSwordDownPoseDeltaV17, ...]:
    guard, anticipation, contact, follow, recovery = poses
    corrected_anticipation = replace(
        anticipation,
        pelvis_x=0.010,
        pelvis_z=-0.012,
        pelvis_roll_z_degrees=-2.0,
        spine_pitch_x_degrees=3.0,
        chest_yaw_z_degrees=22.0,
        head_yaw_z_degrees=-8.0,
        upper_arm_left_x_degrees=-8.0,
        upper_arm_left_z_degrees=-14.0,
        forearm_left_x_degrees=-6.0,
        forearm_left_z_degrees=0.0,
        hand_left_x_degrees=-4.0,
        hand_left_z_degrees=-4.0,
        upper_arm_right_x_degrees=-8.0,
        upper_arm_right_z_degrees=-4.0,
        forearm_right_x_degrees=-6.0,
        forearm_right_z_degrees=-16.0,
        hand_right_x_degrees=-4.0,
        hand_right_z_degrees=-14.0,
        cloth_left_x_degrees=-3.0,
        cloth_center_x_degrees=-2.0,
        cloth_right_x_degrees=3.0,
    )
    corrected_contact = replace(
        contact,
        pelvis_x=-0.012,
        pelvis_z=-0.040,
        pelvis_roll_z_degrees=2.0,
        spine_pitch_x_degrees=-12.0,
        chest_yaw_z_degrees=-10.0,
        head_yaw_z_degrees=5.0,
        upper_arm_left_x_degrees=32.0,
        upper_arm_left_z_degrees=0.0,
        forearm_left_x_degrees=36.0,
        forearm_left_z_degrees=-22.0,
        hand_left_x_degrees=26.0,
        hand_left_z_degrees=-16.0,
        upper_arm_right_x_degrees=32.0,
        upper_arm_right_z_degrees=-16.0,
        forearm_right_x_degrees=36.0,
        forearm_right_z_degrees=6.0,
        hand_right_x_degrees=26.0,
        hand_right_z_degrees=0.0,
        cloth_left_x_degrees=7.0,
        cloth_center_x_degrees=5.0,
        cloth_right_x_degrees=-7.0,
    )
    corrected_follow = replace(
        follow,
        pelvis_x=0.010,
        pelvis_z=-0.050,
        pelvis_roll_z_degrees=3.0,
        spine_pitch_x_degrees=-17.0,
        chest_yaw_z_degrees=-16.0,
        head_yaw_z_degrees=7.0,
        upper_arm_left_x_degrees=48.0,
        upper_arm_left_z_degrees=16.0,
        forearm_left_x_degrees=46.0,
        forearm_left_z_degrees=-14.0,
        hand_left_x_degrees=36.0,
        hand_left_z_degrees=-8.0,
        upper_arm_right_x_degrees=48.0,
        upper_arm_right_z_degrees=-8.0,
        forearm_right_x_degrees=46.0,
        forearm_right_z_degrees=22.0,
        hand_right_x_degrees=36.0,
        hand_right_z_degrees=16.0,
        cloth_left_x_degrees=10.0,
        cloth_center_x_degrees=8.0,
        cloth_right_x_degrees=-10.0,
    )
    return (guard, corrected_anticipation, corrected_contact, corrected_follow, recovery)


def load_attack_sword_down_keyposes_profile_v19(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v18(character_id)
    onehand, twohand = source.grips
    corrected = replace(
        source,
        grips=(
            replace(
                onehand,
                trajectory_id=ONEHAND_TRAJECTORY_REVISION,
                poses=_correct_onehand_poses(onehand.poses),
            ),
            replace(
                twohand,
                trajectory_id=TWOHAND_TRAJECTORY_REVISION,
                poses=_correct_twohand_poses(twohand.poses),
            ),
        ),
    )

    corrected_onehand, corrected_twohand = corrected.grips
    for grip in corrected.grips:
        if tuple(pose.frame for pose in grip.poses) != corrected.frame_order:
            raise ValueError(f"{grip.grip_id} v19 correction changed frame order")
        if tuple(pose.phase for pose in grip.poses) != corrected.phase_order:
            raise ValueError(f"{grip.grip_id} v19 correction changed phase order")
        if any(abs(value) > 72.0 for pose in grip.poses for value in pose.rotation_deltas()):
            raise ValueError(f"{grip.grip_id} v19 exceeds safe rotation delta")

    one_guard, one_anticipation, one_contact, one_follow, one_recovery = corrected_onehand.poses
    if any(value != 0.0 for value in one_guard.rotation_deltas()):
        raise ValueError("One-hand v19 changed approved guard")
    if not one_anticipation.hand_right_z_degrees < one_contact.hand_right_z_degrees < one_follow.hand_right_z_degrees:
        raise ValueError("One-hand v19 sword arc is not monotonic high-to-low")
    if one_contact.chest_yaw_z_degrees * one_follow.chest_yaw_z_degrees <= 0.0:
        raise ValueError("One-hand v19 torso reverses during contact/follow-through")
    if abs(one_recovery.hand_right_z_degrees) > 8.0:
        raise ValueError("One-hand v19 recovery does not return toward guard")

    two_guard, two_anticipation, two_contact, two_follow, _two_recovery = corrected_twohand.poses
    if any(value != 0.0 for value in two_guard.rotation_deltas()):
        raise ValueError("Two-hand v19 changed approved guard")
    if two_anticipation.hand_right_z_degrees >= -12.0:
        raise ValueError("Two-hand v19 anticipation is not displaced outside the head")
    if two_contact.hand_right_z_degrees > 4.0:
        raise ValueError("Two-hand v19 contact crossed toward the head too early")
    if two_follow.hand_right_z_degrees <= two_contact.hand_right_z_degrees:
        raise ValueError("Two-hand v19 follow-through did not complete the lateral arc")
    return corrected
