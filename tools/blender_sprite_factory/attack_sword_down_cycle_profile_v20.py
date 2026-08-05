from __future__ import annotations

import math
from dataclasses import fields, replace

from attack_sword_down_keyposes_correction_v19_pass04 import (
    load_attack_sword_down_keyposes_profile_v19_pass04,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownKeyposesProfileV17,
    AttackSwordDownPoseDeltaV17,
)


FULL_CYCLE_REVISION = "v20"
FULL_CYCLE_FPS = 12
FULL_CYCLE_FRAME_ORDER = (1, 2, 3, 4, 5, 6, 7, 8)
FULL_CYCLE_PHASE_ORDER = (
    "guard",
    "windup",
    "anticipation",
    "contact",
    "follow_through",
    "rebound",
    "recovery",
    "settle",
)
SOURCE_KEYPOSE_REVISION = "v19_pass07_artist_approved"
WINDUP_BLEND = 0.58
REBOUND_BLEND = 0.48
MAX_ROTATION_DELTA_DEGREES = 72.0
MAX_PELVIS_TRANSLATION = 0.08


def _interpolate_pose(
    start: AttackSwordDownPoseDeltaV17,
    end: AttackSwordDownPoseDeltaV17,
    *,
    frame: int,
    phase: str,
    blend: float,
) -> AttackSwordDownPoseDeltaV17:
    if not 0.0 < blend < 1.0:
        raise ValueError("attack sword down v20 interpolation blend must be internal")
    values: dict[str, int | float | str] = {
        "frame": frame,
        "phase": phase,
    }
    for field_info in fields(AttackSwordDownPoseDeltaV17):
        if field_info.name in ("frame", "phase"):
            continue
        start_value = float(getattr(start, field_info.name))
        end_value = float(getattr(end, field_info.name))
        values[field_info.name] = start_value + (end_value - start_value) * blend
    return AttackSwordDownPoseDeltaV17(**values)


def _expand_keyposes(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
) -> tuple[AttackSwordDownPoseDeltaV17, ...]:
    guard, anticipation, contact, follow, recovery = poses
    return (
        replace(guard, frame=1, phase="guard"),
        _interpolate_pose(
            guard,
            anticipation,
            frame=2,
            phase="windup",
            blend=WINDUP_BLEND,
        ),
        replace(anticipation, frame=3, phase="anticipation"),
        replace(contact, frame=4, phase="contact"),
        replace(follow, frame=5, phase="follow_through"),
        _interpolate_pose(
            follow,
            recovery,
            frame=6,
            phase="rebound",
            blend=REBOUND_BLEND,
        ),
        replace(recovery, frame=7, phase="recovery"),
        replace(guard, frame=8, phase="settle"),
    )


def _pose_values(
    pose: AttackSwordDownPoseDeltaV17,
) -> tuple[float, ...]:
    return tuple(
        float(getattr(pose, field_info.name))
        for field_info in fields(AttackSwordDownPoseDeltaV17)
        if field_info.name not in ("frame", "phase")
    )


def _validate_anchor_preservation(
    source: tuple[AttackSwordDownPoseDeltaV17, ...],
    expanded: tuple[AttackSwordDownPoseDeltaV17, ...],
    *,
    grip_id: str,
) -> None:
    source_indices = (0, 1, 2, 3, 4, 0)
    expanded_indices = (0, 2, 3, 4, 6, 7)
    for source_index, expanded_index in zip(source_indices, expanded_indices):
        if _pose_values(source[source_index]) != _pose_values(expanded[expanded_index]):
            raise ValueError(
                f"{grip_id} v20 changed approved v19 anchor at f{expanded_index + 1:02d}"
            )


def load_attack_sword_down_cycle_profile_v20(
    character_id: str,
) -> AttackSwordDownKeyposesProfileV17:
    source = load_attack_sword_down_keyposes_profile_v19_pass04(character_id)
    expanded_grips = []
    for grip in source.grips:
        action_id = (
            "attack_sword_01_onehand_down_v20"
            if grip.grip_id == "onehand_ready"
            else "attack_sword_01_twohand_down_v20"
        )
        expanded_poses = _expand_keyposes(grip.poses)
        _validate_anchor_preservation(
            grip.poses,
            expanded_poses,
            grip_id=grip.grip_id,
        )
        expanded_grips.append(
            replace(
                grip,
                action_id=action_id,
                trajectory_id=f"{grip.trajectory_id}_full_cycle_v20",
                poses=expanded_poses,
            )
        )

    profile = replace(
        source,
        revision=FULL_CYCLE_REVISION,
        animation_id="attack_sword_01_down",
        fps=FULL_CYCLE_FPS,
        loop=False,
        frame_order=FULL_CYCLE_FRAME_ORDER,
        phase_order=FULL_CYCLE_PHASE_ORDER,
        grips=tuple(expanded_grips),
    )

    if tuple(pose.frame for pose in profile.grips[0].poses) != FULL_CYCLE_FRAME_ORDER:
        raise ValueError("One-hand v20 full-cycle frame order is invalid")
    if tuple(pose.frame for pose in profile.grips[1].poses) != FULL_CYCLE_FRAME_ORDER:
        raise ValueError("Two-hand v20 full-cycle frame order is invalid")
    for grip in profile.grips:
        if tuple(pose.phase for pose in grip.poses) != FULL_CYCLE_PHASE_ORDER:
            raise ValueError(f"{grip.grip_id} v20 full-cycle phase order is invalid")
        for pose in grip.poses:
            if abs(pose.pelvis_x) > MAX_PELVIS_TRANSLATION:
                raise ValueError(f"{grip.grip_id} v20 pelvis x translation is unsafe")
            if abs(pose.pelvis_z) > MAX_PELVIS_TRANSLATION:
                raise ValueError(f"{grip.grip_id} v20 pelvis z translation is unsafe")
            if any(
                abs(value) > MAX_ROTATION_DELTA_DEGREES
                for value in pose.rotation_deltas()
            ):
                raise ValueError(f"{grip.grip_id} v20 rotation delta is unsafe")

        windup = grip.poses[1]
        anticipation = grip.poses[2]
        rebound = grip.poses[5]
        recovery = grip.poses[6]
        for windup_value, anticipation_value in zip(
            _pose_values(windup),
            _pose_values(anticipation),
        ):
            if not math.isfinite(windup_value) or not math.isfinite(anticipation_value):
                raise ValueError(f"{grip.grip_id} v20 wind-up contains non-finite values")
        for rebound_value, recovery_value in zip(
            _pose_values(rebound),
            _pose_values(recovery),
        ):
            if not math.isfinite(rebound_value) or not math.isfinite(recovery_value):
                raise ValueError(f"{grip.grip_id} v20 rebound contains non-finite values")
    return profile
