from __future__ import annotations

from dataclasses import dataclass, fields

from hit_down_keyposes_profile_v01 import (
    MAX_PELVIS_TRANSLATION,
    MAX_ROTATION_DELTA_DEGREES,
    HitDownPoseDeltaV01,
    load_hit_down_keyposes_profile_v01,
)


HIT_DOWN_CYCLE_FRAME_ORDER = (1, 2, 3, 4, 5, 6)
HIT_DOWN_CYCLE_PHASE_ORDER = (
    "impact",
    "recoil_peak",
    "release_mid",
    "recovery",
    "settle",
    "guard",
)
HIT_DOWN_CYCLE_FPS = 15
HIT_DOWN_CYCLE_DURATION_SECONDS = len(HIT_DOWN_CYCLE_FRAME_ORDER) / HIT_DOWN_CYCLE_FPS
RELEASE_BLEND_TO_RECOVERY = 0.55
SETTLE_BLEND_TO_GUARD = 0.70


@dataclass(frozen=True)
class HitDownCycleProfileV01:
    character_id: str
    revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    stance_variant_id: str
    stance_source_revision: str
    weapon_cycle_id: str
    incoming_direction: str
    poses: tuple[HitDownPoseDeltaV01, ...]
    source_keypose_revision: str
    appearance_revision: str
    head_revision: str
    proxy_revision: str


def _copy_pose(
    source: HitDownPoseDeltaV01,
    *,
    frame: int,
    phase: str,
) -> HitDownPoseDeltaV01:
    values = {
        field.name: getattr(source, field.name)
        for field in fields(HitDownPoseDeltaV01)
        if field.name not in {"frame", "phase"}
    }
    return HitDownPoseDeltaV01(frame=frame, phase=phase, **values)


def _blend_pose(
    source: HitDownPoseDeltaV01,
    target: HitDownPoseDeltaV01,
    weight_to_target: float,
    *,
    frame: int,
    phase: str,
) -> HitDownPoseDeltaV01:
    if not 0.0 < weight_to_target < 1.0:
        raise ValueError("hit_down cycle blend weight must be between zero and one")
    values: dict[str, float] = {}
    for field in fields(HitDownPoseDeltaV01):
        if field.name in {"frame", "phase"}:
            continue
        source_value = float(getattr(source, field.name))
        target_value = float(getattr(target, field.name))
        values[field.name] = source_value + (
            target_value - source_value
        ) * weight_to_target
    return HitDownPoseDeltaV01(frame=frame, phase=phase, **values)


def _build_cycle_poses() -> tuple[HitDownPoseDeltaV01, ...]:
    keyposes = load_hit_down_keyposes_profile_v01("human_warrior_m01")
    guard, impact, recoil_peak, recovery = keyposes.poses
    return (
        _copy_pose(impact, frame=1, phase="impact"),
        _copy_pose(recoil_peak, frame=2, phase="recoil_peak"),
        _blend_pose(
            recoil_peak,
            recovery,
            RELEASE_BLEND_TO_RECOVERY,
            frame=3,
            phase="release_mid",
        ),
        _copy_pose(recovery, frame=4, phase="recovery"),
        _blend_pose(
            recovery,
            guard,
            SETTLE_BLEND_TO_GUARD,
            frame=5,
            phase="settle",
        ),
        _copy_pose(guard, frame=6, phase="guard"),
    )


_KEYPOSE_PROFILE = load_hit_down_keyposes_profile_v01("human_warrior_m01")

HUMAN_WARRIOR_M01_HIT_DOWN_CYCLE_V01 = HitDownCycleProfileV01(
    character_id="human_warrior_m01",
    revision="hit_down_cycle_v01_from_keyposes_pass02",
    animation_id="hit_01_onehand_down_v01",
    direction="down",
    fps=HIT_DOWN_CYCLE_FPS,
    loop=False,
    frame_order=HIT_DOWN_CYCLE_FRAME_ORDER,
    phase_order=HIT_DOWN_CYCLE_PHASE_ORDER,
    stance_variant_id=_KEYPOSE_PROFILE.stance_variant_id,
    stance_source_revision=_KEYPOSE_PROFILE.stance_source_revision,
    weapon_cycle_id=_KEYPOSE_PROFILE.weapon_cycle_id,
    incoming_direction=_KEYPOSE_PROFILE.incoming_direction,
    poses=_build_cycle_poses(),
    source_keypose_revision=_KEYPOSE_PROFILE.revision,
    appearance_revision=_KEYPOSE_PROFILE.appearance_revision,
    head_revision=_KEYPOSE_PROFILE.head_revision,
    proxy_revision=_KEYPOSE_PROFILE.proxy_revision,
)


def load_hit_down_cycle_profile_v01(
    character_id: str,
) -> HitDownCycleProfileV01:
    profile = HUMAN_WARRIOR_M01_HIT_DOWN_CYCLE_V01
    if character_id != profile.character_id:
        raise KeyError(f"No hit down cycle v01 profile for character_id={character_id}")
    if profile.direction != "down" or profile.loop:
        raise ValueError("Hit down cycle v01 identity drifted")
    if profile.frame_order != HIT_DOWN_CYCLE_FRAME_ORDER:
        raise ValueError("Hit down cycle v01 frame order drifted")
    if profile.phase_order != HIT_DOWN_CYCLE_PHASE_ORDER:
        raise ValueError("Hit down cycle v01 phase order drifted")
    if tuple(pose.frame for pose in profile.poses) != profile.frame_order:
        raise ValueError("Hit down cycle v01 pose frames drifted")
    if tuple(pose.phase for pose in profile.poses) != profile.phase_order:
        raise ValueError("Hit down cycle v01 pose phases drifted")
    if profile.source_keypose_revision != "hit_down_keyposes_v01_pass02":
        raise ValueError("Hit down cycle v01 source keyposes drifted")
    if any(
        abs(value) > MAX_PELVIS_TRANSLATION
        for pose in profile.poses
        for value in pose.translation_deltas()
    ):
        raise ValueError("Hit down cycle v01 pelvis translation exceeds budget")
    if any(
        abs(value) > MAX_ROTATION_DELTA_DEGREES
        for pose in profile.poses
        for value in pose.rotation_deltas()
    ):
        raise ValueError("Hit down cycle v01 rotation exceeds budget")
    return profile
