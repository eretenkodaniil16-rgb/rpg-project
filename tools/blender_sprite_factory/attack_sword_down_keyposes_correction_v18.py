from __future__ import annotations

from dataclasses import replace

from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
    AttackSwordDownPoseDeltaV17,
    load_attack_sword_down_keyposes_profile_v17,
)


CORRECTION_REVISION = "v18"
ONEHAND_TRAJECTORY_REVISION = "high_windup_to_low_follow_v18"
TWOHAND_ANTICIPATION_REVISION = "contained_high_guard_v18"


def _onehand_recovery_pose(
    source: AttackSwordDownPoseDeltaV17,
) -> AttackSwordDownPoseDeltaV17:
    return replace(
        source,
        frame=5,
        phase="recovery",
        pelvis_x=0.0,
        pelvis_z=-0.005,
        pelvis_roll_z_degrees=0.5,
        spine_pitch_x_degrees=-1.5,
        chest_yaw_z_degrees=-5.0,
        head_yaw_z_degrees=1.5,
        thigh_left_x_degrees=1.0,
        thigh_right_x_degrees=-1.0,
        shin_left_x_degrees=0.0,
        shin_right_x_degrees=0.0,
        foot_left_x_degrees=0.0,
        foot_right_x_degrees=0.0,
        upper_arm_left_x_degrees=1.5,
        upper_arm_left_z_degrees=-1.0,
        forearm_left_x_degrees=2.0,
        forearm_left_z_degrees=-1.5,
        hand_left_x_degrees=0.0,
        hand_left_z_degrees=0.0,
        upper_arm_right_x_degrees=4.0,
        upper_arm_right_z_degrees=-6.0,
        forearm_right_x_degrees=5.0,
        forearm_right_z_degrees=-4.0,
        hand_right_x_degrees=4.0,
        hand_right_z_degrees=-9.0,
        cloth_left_x_degrees=1.5,
        cloth_center_x_degrees=1.0,
        cloth_right_x_degrees=-1.5,
    )


def _correct_onehand_poses(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
) -> tuple[AttackSwordDownPoseDeltaV17, ...]:
    guard, low_anticipation, high_contact, high_follow, horizontal_recovery = poses
    return (
        guard,
        replace(high_contact, frame=2, phase="anticipation"),
        replace(horizontal_recovery, frame=3, phase="contact"),
        replace(low_anticipation, frame=4, phase="follow_through"),
        _onehand_recovery_pose(horizontal_recovery),
    )


def _correct_twohand_poses(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
) -> tuple[AttackSwordDownPoseDeltaV17, ...]:
    guard, anticipation, contact, follow, recovery = poses
    contained_anticipation = replace(
        anticipation,
        upper_arm_left_x_degrees=-10.0,
        forearm_left_x_degrees=-9.0,
        hand_left_x_degrees=-5.0,
        upper_arm_right_x_degrees=-10.0,
        forearm_right_x_degrees=-9.0,
        hand_right_x_degrees=-5.0,
    )
    return (guard, contained_anticipation, contact, follow, recovery)


def load_attack_sword_down_keyposes_profile_v18(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v17(character_id)
    onehand, twohand = source.grips
    corrected = replace(
        source,
        grips=(
            replace(onehand, poses=_correct_onehand_poses(onehand.poses)),
            replace(twohand, poses=_correct_twohand_poses(twohand.poses)),
        ),
    )

    corrected_onehand, corrected_twohand = corrected.grips
    if tuple(pose.frame for pose in corrected_onehand.poses) != corrected.frame_order:
        raise ValueError("One-hand v18 correction changed frame order")
    if tuple(pose.phase for pose in corrected_onehand.poses) != corrected.phase_order:
        raise ValueError("One-hand v18 correction changed phase order")
    if corrected_onehand.poses[1].hand_right_z_degrees >= -50.0:
        raise ValueError("One-hand v18 anticipation is not visibly high")
    if corrected_onehand.poses[2].hand_right_z_degrees > -10.0:
        raise ValueError("One-hand v18 contact did not cross the central arc")
    if corrected_onehand.poses[3].hand_right_z_degrees <= 20.0:
        raise ValueError("One-hand v18 follow-through is not visibly low")
    if abs(corrected_onehand.poses[4].hand_right_z_degrees) > 12.0:
        raise ValueError("One-hand v18 recovery did not return toward guard")

    anticipation = corrected_twohand.poses[1]
    if anticipation.upper_arm_left_x_degrees != anticipation.upper_arm_right_x_degrees:
        raise ValueError("Two-hand v18 anticipation lost upper-arm symmetry")
    if anticipation.forearm_left_x_degrees != anticipation.forearm_right_x_degrees:
        raise ValueError("Two-hand v18 anticipation lost forearm symmetry")
    if anticipation.hand_left_x_degrees != anticipation.hand_right_x_degrees:
        raise ValueError("Two-hand v18 anticipation lost hand symmetry")
    if min(
        anticipation.upper_arm_left_x_degrees,
        anticipation.forearm_left_x_degrees,
        anticipation.hand_left_x_degrees,
    ) < -12.0:
        raise ValueError("Two-hand v18 anticipation remains too high for 96x96")
    return corrected
