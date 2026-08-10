from __future__ import annotations

import math
from dataclasses import fields, replace

from death_down_keyposes_profile_v01 import (
    DEATH_DOWN_VARIANT_IDS,
    MAX_PELVIS_TRANSLATION,
    MAX_ROTATION_DELTA_DEGREES,
    DeathDownKeyposesProfileV01,
    DeathDownPoseDeltaV01,
    load_death_down_keyposes_profiles_v01,
)


DEATH_DOWN_CYCLE_FRAME_ORDER = (1, 2, 3, 4, 5, 6, 7, 8)
DEATH_DOWN_CYCLE_PHASE_ORDER = (
    "guard",
    "stagger",
    "balance_break",
    "knee_drop",
    "fall_acceleration",
    "ground_impact",
    "final",
    "corpse_hold",
)
DEATH_DOWN_CYCLE_FPS = 10
DEATH_DOWN_CYCLE_DURATION_SECONDS = (
    len(DEATH_DOWN_CYCLE_FRAME_ORDER) / DEATH_DOWN_CYCLE_FPS
)
STAGGER_BLEND_TO_BALANCE_BREAK = 0.52
FALL_BLEND_TO_GROUND_IMPACT = 0.58
SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME = {
    1: 1,
    3: 2,
    4: 3,
    6: 4,
    7: 5,
    8: 5,
}
APPROVED_ANCHOR_FRAMES = tuple(SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME)
INTERPOLATED_FRAMES = (2, 5)
CORPSE_HOLD_FRAME = 8
DETACHMENT_CYCLE_FRAME = 6


_REVISION_BY_VARIANT = {
    "death_01_base": "death_01_base_down_cycle_v01_from_keyposes_pass02",
    "death_02_base": "death_02_base_down_cycle_v01_from_keyposes_pass01",
    "death_03_base": (
        "death_03_base_down_cycle_v01_from_keyposes_pass02_waist_separation"
    ),
}


def _pose_values(pose: DeathDownPoseDeltaV01) -> tuple[float, ...]:
    return tuple(
        float(getattr(pose, field_info.name))
        for field_info in fields(DeathDownPoseDeltaV01)
        if field_info.name not in {"frame", "phase"}
    )


def _copy_pose(
    source: DeathDownPoseDeltaV01,
    *,
    frame: int,
    phase: str,
) -> DeathDownPoseDeltaV01:
    return replace(source, frame=frame, phase=phase)


def _blend_pose(
    source: DeathDownPoseDeltaV01,
    target: DeathDownPoseDeltaV01,
    weight_to_target: float,
    *,
    frame: int,
    phase: str,
) -> DeathDownPoseDeltaV01:
    if not 0.0 < weight_to_target < 1.0:
        raise ValueError("death down cycle blend weight must be between zero and one")
    values: dict[str, float | int | str] = {
        "frame": frame,
        "phase": phase,
    }
    for field_info in fields(DeathDownPoseDeltaV01):
        if field_info.name in {"frame", "phase"}:
            continue
        source_value = float(getattr(source, field_info.name))
        target_value = float(getattr(target, field_info.name))
        values[field_info.name] = source_value + (
            target_value - source_value
        ) * weight_to_target
    return DeathDownPoseDeltaV01(**values)


def _expand_keyposes(
    poses: tuple[DeathDownPoseDeltaV01, ...],
) -> tuple[DeathDownPoseDeltaV01, ...]:
    guard, balance_break, knee_drop, ground_impact, final = poses
    return (
        _copy_pose(guard, frame=1, phase="guard"),
        _blend_pose(
            guard,
            balance_break,
            STAGGER_BLEND_TO_BALANCE_BREAK,
            frame=2,
            phase="stagger",
        ),
        _copy_pose(balance_break, frame=3, phase="balance_break"),
        _copy_pose(knee_drop, frame=4, phase="knee_drop"),
        _blend_pose(
            knee_drop,
            ground_impact,
            FALL_BLEND_TO_GROUND_IMPACT,
            frame=5,
            phase="fall_acceleration",
        ),
        _copy_pose(ground_impact, frame=6, phase="ground_impact"),
        _copy_pose(final, frame=7, phase="final"),
        _copy_pose(final, frame=8, phase="corpse_hold"),
    )


def _validate_anchor_preservation(
    source: DeathDownKeyposesProfileV01,
    cycle: DeathDownKeyposesProfileV01,
) -> None:
    source_by_frame = {pose.frame: pose for pose in source.poses}
    cycle_by_frame = {pose.frame: pose for pose in cycle.poses}
    for cycle_frame, source_frame in SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME.items():
        if _pose_values(cycle_by_frame[cycle_frame]) != _pose_values(
            source_by_frame[source_frame]
        ):
            raise ValueError(
                f"{source.death_variant_id} changed source keypose "
                f"f{source_frame:02d} at cycle f{cycle_frame:02d}"
            )


def _build_cycle_profiles() -> tuple[DeathDownKeyposesProfileV01, ...]:
    source_profiles = load_death_down_keyposes_profiles_v01("human_warrior_m01")
    result: list[DeathDownKeyposesProfileV01] = []
    for source in source_profiles:
        cycle = replace(
            source,
            revision=_REVISION_BY_VARIANT[source.death_variant_id],
            animation_id=f"{source.death_variant_id}_down_v01",
            fps=DEATH_DOWN_CYCLE_FPS,
            frame_order=DEATH_DOWN_CYCLE_FRAME_ORDER,
            phase_order=DEATH_DOWN_CYCLE_PHASE_ORDER,
            detachment_frame=(
                DETACHMENT_CYCLE_FRAME
                if source.detachment_frame is not None
                else None
            ),
            poses=_expand_keyposes(source.poses),
        )
        _validate_anchor_preservation(source, cycle)
        result.append(cycle)
    return tuple(result)


HUMAN_WARRIOR_M01_DEATH_DOWN_CYCLES_V01 = _build_cycle_profiles()
SOURCE_KEYPOSE_REVISIONS = {
    profile.death_variant_id: profile.revision
    for profile in load_death_down_keyposes_profiles_v01("human_warrior_m01")
}


def load_death_down_cycle_profiles_v01(
    character_id: str,
) -> tuple[DeathDownKeyposesProfileV01, ...]:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No death down cycles v01 for character_id={character_id}")
    profiles = HUMAN_WARRIOR_M01_DEATH_DOWN_CYCLES_V01
    if tuple(profile.death_variant_id for profile in profiles) != DEATH_DOWN_VARIANT_IDS:
        raise ValueError("Death down cycle v01 variant order drifted")
    source_by_variant = {
        profile.death_variant_id: profile
        for profile in load_death_down_keyposes_profiles_v01(character_id)
    }
    for profile in profiles:
        if profile.direction != "down" or profile.loop:
            raise ValueError(f"{profile.death_variant_id} cycle identity drifted")
        if profile.frame_order != DEATH_DOWN_CYCLE_FRAME_ORDER:
            raise ValueError(f"{profile.death_variant_id} cycle frame order drifted")
        if profile.phase_order != DEATH_DOWN_CYCLE_PHASE_ORDER:
            raise ValueError(f"{profile.death_variant_id} cycle phase order drifted")
        if tuple(pose.frame for pose in profile.poses) != profile.frame_order:
            raise ValueError(f"{profile.death_variant_id} cycle pose frames drifted")
        if tuple(pose.phase for pose in profile.poses) != profile.phase_order:
            raise ValueError(f"{profile.death_variant_id} cycle pose phases drifted")
        if profile.fps != DEATH_DOWN_CYCLE_FPS:
            raise ValueError(f"{profile.death_variant_id} cycle FPS drifted")
        if profile.weapon_visible or not profile.final_pose_persistent:
            raise ValueError(f"{profile.death_variant_id} cycle safety drifted")
        if profile.detached_part_id is not None:
            if profile.detachment_frame != DETACHMENT_CYCLE_FRAME:
                raise ValueError("death_03 cycle detachment frame drifted")
        elif profile.detachment_frame is not None:
            raise ValueError(f"{profile.death_variant_id} has unexpected detachment")
        if any(
            abs(value) > MAX_PELVIS_TRANSLATION
            for pose in profile.poses
            for value in pose.translation_deltas()
        ):
            raise ValueError(
                f"{profile.death_variant_id} cycle pelvis translation exceeds budget"
            )
        if any(
            abs(value) > MAX_ROTATION_DELTA_DEGREES
            for pose in profile.poses
            for value in pose.rotation_deltas()
        ):
            raise ValueError(
                f"{profile.death_variant_id} cycle rotation exceeds budget"
            )
        if any(
            not math.isfinite(value)
            for pose in profile.poses
            for value in (*pose.translation_deltas(), *pose.rotation_deltas())
        ):
            raise ValueError(f"{profile.death_variant_id} cycle is non-finite")
        _validate_anchor_preservation(
            source_by_variant[profile.death_variant_id],
            profile,
        )
    return profiles


def load_death_down_cycle_profile_v01(
    character_id: str,
    death_variant_id: str = "death_01_base",
) -> DeathDownKeyposesProfileV01:
    for profile in load_death_down_cycle_profiles_v01(character_id):
        if profile.death_variant_id == death_variant_id:
            return profile
    raise KeyError(
        f"No death down cycle v01 profile for death_variant_id={death_variant_id}"
    )
