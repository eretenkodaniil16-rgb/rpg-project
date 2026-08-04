from __future__ import annotations

from dataclasses import fields, replace

from attack_sword_down_cycle_profile_v20 import (
    FULL_CYCLE_FRAME_ORDER,
    FULL_CYCLE_PHASE_ORDER,
    load_attack_sword_down_cycle_profile_v20,
)
from attack_sword_down_keyposes_profile_v17 import AttackSwordDownPoseDeltaV17


OVERHEAD_REVIEW_REVISION = "twohand_down_centered_overhead_v21_review"
OVERHEAD_ACTION_ID = "attack_sword_01_twohand_down_overhead_v21"
OVERHEAD_TRAJECTORY_ID = "center_high_overhead_to_center_low_vertical_chop"
OVERHEAD_SOURCE_ACTION_ID = "attack_sword_01_twohand_down_v20"


def _pose(frame: int, phase: str, **values: float) -> AttackSwordDownPoseDeltaV17:
    return AttackSwordDownPoseDeltaV17(frame=frame, phase=phase, **values)


TWOHAND_OVERHEAD_POSES = (
    _pose(1, "guard"),
    _pose(
        2,
        "windup",
        pelvis_z=-0.008,
        spine_pitch_x_degrees=2.0,
        thigh_left_x_degrees=-1.0,
        thigh_right_x_degrees=-1.0,
        shin_left_x_degrees=1.0,
        shin_right_x_degrees=1.0,
        upper_arm_left_x_degrees=-12.0,
        upper_arm_left_z_degrees=-5.0,
        forearm_left_x_degrees=-10.0,
        forearm_left_z_degrees=4.0,
        hand_left_x_degrees=-6.0,
        hand_left_z_degrees=2.0,
        upper_arm_right_x_degrees=-12.0,
        upper_arm_right_z_degrees=5.0,
        forearm_right_x_degrees=-10.0,
        forearm_right_z_degrees=-4.0,
        hand_right_x_degrees=-6.0,
        hand_right_z_degrees=-2.0,
        cloth_left_x_degrees=-2.0,
        cloth_center_x_degrees=-1.0,
        cloth_right_x_degrees=-2.0,
    ),
    _pose(
        3,
        "anticipation",
        pelvis_z=-0.015,
        spine_pitch_x_degrees=5.0,
        thigh_left_x_degrees=-2.0,
        thigh_right_x_degrees=-2.0,
        shin_left_x_degrees=2.0,
        shin_right_x_degrees=2.0,
        upper_arm_left_x_degrees=-30.0,
        upper_arm_left_z_degrees=-7.0,
        forearm_left_x_degrees=-28.0,
        forearm_left_z_degrees=5.0,
        hand_left_x_degrees=-18.0,
        hand_left_z_degrees=3.0,
        upper_arm_right_x_degrees=-30.0,
        upper_arm_right_z_degrees=7.0,
        forearm_right_x_degrees=-28.0,
        forearm_right_z_degrees=-5.0,
        hand_right_x_degrees=-18.0,
        hand_right_z_degrees=-3.0,
        cloth_left_x_degrees=-4.0,
        cloth_center_x_degrees=-3.0,
        cloth_right_x_degrees=-4.0,
    ),
    _pose(
        4,
        "contact",
        pelvis_z=-0.040,
        spine_pitch_x_degrees=-13.0,
        thigh_left_x_degrees=5.0,
        thigh_right_x_degrees=5.0,
        shin_left_x_degrees=-5.0,
        shin_right_x_degrees=-5.0,
        foot_left_x_degrees=2.0,
        foot_right_x_degrees=2.0,
        upper_arm_left_x_degrees=36.0,
        upper_arm_left_z_degrees=-4.0,
        forearm_left_x_degrees=40.0,
        forearm_left_z_degrees=5.0,
        hand_left_x_degrees=28.0,
        hand_left_z_degrees=3.0,
        upper_arm_right_x_degrees=36.0,
        upper_arm_right_z_degrees=4.0,
        forearm_right_x_degrees=40.0,
        forearm_right_z_degrees=-5.0,
        hand_right_x_degrees=28.0,
        hand_right_z_degrees=-3.0,
        cloth_left_x_degrees=7.0,
        cloth_center_x_degrees=5.0,
        cloth_right_x_degrees=7.0,
    ),
    _pose(
        5,
        "follow_through",
        pelvis_z=-0.052,
        spine_pitch_x_degrees=-19.0,
        thigh_left_x_degrees=7.0,
        thigh_right_x_degrees=7.0,
        shin_left_x_degrees=-7.0,
        shin_right_x_degrees=-7.0,
        foot_left_x_degrees=3.0,
        foot_right_x_degrees=3.0,
        upper_arm_left_x_degrees=50.0,
        upper_arm_left_z_degrees=-3.0,
        forearm_left_x_degrees=48.0,
        forearm_left_z_degrees=4.0,
        hand_left_x_degrees=38.0,
        hand_left_z_degrees=2.0,
        upper_arm_right_x_degrees=50.0,
        upper_arm_right_z_degrees=3.0,
        forearm_right_x_degrees=48.0,
        forearm_right_z_degrees=-4.0,
        hand_right_x_degrees=38.0,
        hand_right_z_degrees=-2.0,
        cloth_left_x_degrees=10.0,
        cloth_center_x_degrees=8.0,
        cloth_right_x_degrees=10.0,
    ),
    _pose(
        6,
        "rebound",
        pelvis_z=-0.034,
        spine_pitch_x_degrees=-11.0,
        thigh_left_x_degrees=4.0,
        thigh_right_x_degrees=4.0,
        shin_left_x_degrees=-4.0,
        shin_right_x_degrees=-4.0,
        foot_left_x_degrees=2.0,
        foot_right_x_degrees=2.0,
        upper_arm_left_x_degrees=31.0,
        upper_arm_left_z_degrees=-3.0,
        forearm_left_x_degrees=31.0,
        forearm_left_z_degrees=4.0,
        hand_left_x_degrees=23.0,
        hand_left_z_degrees=2.0,
        upper_arm_right_x_degrees=31.0,
        upper_arm_right_z_degrees=3.0,
        forearm_right_x_degrees=31.0,
        forearm_right_z_degrees=-4.0,
        hand_right_x_degrees=23.0,
        hand_right_z_degrees=-2.0,
        cloth_left_x_degrees=7.0,
        cloth_center_x_degrees=5.0,
        cloth_right_x_degrees=7.0,
    ),
    _pose(
        7,
        "recovery",
        pelvis_z=-0.012,
        spine_pitch_x_degrees=-4.0,
        thigh_left_x_degrees=2.0,
        thigh_right_x_degrees=2.0,
        shin_left_x_degrees=-2.0,
        shin_right_x_degrees=-2.0,
        upper_arm_left_x_degrees=10.0,
        upper_arm_left_z_degrees=-2.0,
        forearm_left_x_degrees=12.0,
        forearm_left_z_degrees=3.0,
        hand_left_x_degrees=8.0,
        hand_left_z_degrees=2.0,
        upper_arm_right_x_degrees=10.0,
        upper_arm_right_z_degrees=2.0,
        forearm_right_x_degrees=12.0,
        forearm_right_z_degrees=-3.0,
        hand_right_x_degrees=8.0,
        hand_right_z_degrees=-2.0,
        cloth_left_x_degrees=3.0,
        cloth_center_x_degrees=2.0,
        cloth_right_x_degrees=3.0,
    ),
    _pose(8, "settle"),
)


def _pose_values(pose: AttackSwordDownPoseDeltaV17) -> tuple[float, ...]:
    return tuple(
        float(getattr(pose, item.name))
        for item in fields(AttackSwordDownPoseDeltaV17)
        if item.name not in ("frame", "phase")
    )


def _validate_overhead_poses() -> None:
    if tuple(pose.frame for pose in TWOHAND_OVERHEAD_POSES) != FULL_CYCLE_FRAME_ORDER:
        raise ValueError("two-hand overhead v21 frame order is invalid")
    if tuple(pose.phase for pose in TWOHAND_OVERHEAD_POSES) != FULL_CYCLE_PHASE_ORDER:
        raise ValueError("two-hand overhead v21 phase order is invalid")
    if any(_pose_values(TWOHAND_OVERHEAD_POSES[index]) for index in (0, 7)):
        raise ValueError("two-hand overhead v21 guard/settle must be exact stance deltas")

    for pose in TWOHAND_OVERHEAD_POSES[1:7]:
        if pose.pelvis_x != 0.0 or pose.pelvis_roll_z_degrees != 0.0:
            raise ValueError("two-hand overhead v21 introduced lateral pelvis motion")
        if pose.chest_yaw_z_degrees != 0.0 or pose.head_yaw_z_degrees != 0.0:
            raise ValueError("two-hand overhead v21 introduced a side-facing torso twist")
        symmetric_pairs = (
            (pose.upper_arm_left_x_degrees, pose.upper_arm_right_x_degrees),
            (pose.forearm_left_x_degrees, pose.forearm_right_x_degrees),
            (pose.hand_left_x_degrees, pose.hand_right_x_degrees),
            (pose.upper_arm_left_z_degrees, -pose.upper_arm_right_z_degrees),
            (pose.forearm_left_z_degrees, -pose.forearm_right_z_degrees),
            (pose.hand_left_z_degrees, -pose.hand_right_z_degrees),
        )
        if any(left != right for left, right in symmetric_pairs):
            raise ValueError("two-hand overhead v21 lost paired arm symmetry")

    anticipation = TWOHAND_OVERHEAD_POSES[2]
    contact = TWOHAND_OVERHEAD_POSES[3]
    follow = TWOHAND_OVERHEAD_POSES[4]
    if anticipation.upper_arm_left_x_degrees >= -24.0:
        raise ValueError("two-hand overhead v21 anticipation is not raised overhead")
    if contact.upper_arm_left_x_degrees <= 30.0:
        raise ValueError("two-hand overhead v21 contact does not drive downward")
    if follow.upper_arm_left_x_degrees <= contact.upper_arm_left_x_degrees:
        raise ValueError("two-hand overhead v21 follow-through does not continue downward")


def load_attack_sword_twohand_down_overhead_profile_v21(character_id: str) -> object:
    _validate_overhead_poses()
    source = load_attack_sword_down_cycle_profile_v20(character_id)
    onehand, twohand = source.grips
    overhead_twohand = replace(
        twohand,
        display_name="Двуручный вертикальный рубящий удар сверху вниз",
        action_id=OVERHEAD_ACTION_ID,
        trajectory_id=OVERHEAD_TRAJECTORY_ID,
        poses=TWOHAND_OVERHEAD_POSES,
    )
    result = replace(source, grips=(onehand, overhead_twohand))
    if result.grips[0] != source.grips[0]:
        raise ValueError("two-hand overhead v21 changed the one-hand cycle")
    if result.grips[1].stance_variant_id != twohand.stance_variant_id:
        raise ValueError("two-hand overhead v21 changed the approved stance source")
    if result.grips[1].weapon_cycle_id != twohand.weapon_cycle_id:
        raise ValueError("two-hand overhead v21 changed the approved weapon module")
    return result
