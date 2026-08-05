from __future__ import annotations

from dataclasses import fields

from hit_down_cycle_profile_v01 import (
    HIT_DOWN_CYCLE_FPS,
    HIT_DOWN_CYCLE_FRAME_ORDER,
    HIT_DOWN_CYCLE_PHASE_ORDER,
    HitDownCycleProfileV01,
    load_hit_down_cycle_profile_v01,
)
from hit_down_keyposes_profile_v01 import (
    MAX_PELVIS_TRANSLATION,
    MAX_ROTATION_DELTA_DEGREES,
    HitDownPoseDeltaV01,
)


TWOHAND_ARM_RESPONSE_SCALE = 0.35
TWOHAND_STANCE_VARIANT_ID = "twohand_center_high"
TWOHAND_STANCE_SOURCE_REVISION = "v06_artist_approved"

_ARM_FIELDS = frozenset(
    {
        "upper_arm_left_x_degrees",
        "upper_arm_left_y_degrees",
        "upper_arm_left_z_degrees",
        "forearm_left_x_degrees",
        "forearm_left_y_degrees",
        "forearm_left_z_degrees",
        "hand_left_x_degrees",
        "hand_left_y_degrees",
        "hand_left_z_degrees",
        "upper_arm_right_x_degrees",
        "upper_arm_right_y_degrees",
        "upper_arm_right_z_degrees",
        "forearm_right_x_degrees",
        "forearm_right_y_degrees",
        "forearm_right_z_degrees",
        "hand_right_x_degrees",
        "hand_right_y_degrees",
        "hand_right_z_degrees",
    }
)


def _symmetric_pair(
    left_value: float,
    right_value: float,
    *,
    opposite_signs: bool,
) -> tuple[float, float]:
    magnitude = (abs(float(left_value)) + abs(float(right_value))) * 0.5
    magnitude *= TWOHAND_ARM_RESPONSE_SCALE
    if opposite_signs:
        return magnitude, -magnitude
    signed_average = (float(left_value) + float(right_value)) * 0.5
    signed_average *= TWOHAND_ARM_RESPONSE_SCALE
    return signed_average, signed_average


def _adapt_pose_for_twohand(source: HitDownPoseDeltaV01) -> HitDownPoseDeltaV01:
    values = {
        field.name: getattr(source, field.name)
        for field in fields(HitDownPoseDeltaV01)
        if field.name not in {"frame", "phase"}
    }

    upper_arm_x = _symmetric_pair(
        source.upper_arm_left_x_degrees,
        source.upper_arm_right_x_degrees,
        opposite_signs=False,
    )
    upper_arm_z = _symmetric_pair(
        source.upper_arm_left_z_degrees,
        source.upper_arm_right_z_degrees,
        opposite_signs=True,
    )
    forearm_x = _symmetric_pair(
        source.forearm_left_x_degrees,
        source.forearm_right_x_degrees,
        opposite_signs=False,
    )
    forearm_z = _symmetric_pair(
        source.forearm_left_z_degrees,
        source.forearm_right_z_degrees,
        opposite_signs=True,
    )
    hand_x = _symmetric_pair(
        source.hand_left_x_degrees,
        source.hand_right_x_degrees,
        opposite_signs=False,
    )
    hand_z = _symmetric_pair(
        source.hand_left_z_degrees,
        source.hand_right_z_degrees,
        opposite_signs=True,
    )

    values.update(
        {
            "upper_arm_left_x_degrees": upper_arm_x[0],
            "upper_arm_left_y_degrees": 0.0,
            "upper_arm_left_z_degrees": upper_arm_z[0],
            "upper_arm_right_x_degrees": upper_arm_x[1],
            "upper_arm_right_y_degrees": 0.0,
            "upper_arm_right_z_degrees": upper_arm_z[1],
            "forearm_left_x_degrees": forearm_x[0],
            "forearm_left_y_degrees": 0.0,
            "forearm_left_z_degrees": forearm_z[0],
            "forearm_right_x_degrees": forearm_x[1],
            "forearm_right_y_degrees": 0.0,
            "forearm_right_z_degrees": forearm_z[1],
            "hand_left_x_degrees": hand_x[0],
            "hand_left_y_degrees": 0.0,
            "hand_left_z_degrees": hand_z[0],
            "hand_right_x_degrees": hand_x[1],
            "hand_right_y_degrees": 0.0,
            "hand_right_z_degrees": hand_z[1],
        }
    )
    return HitDownPoseDeltaV01(
        frame=source.frame,
        phase=source.phase,
        **values,
    )


def _build_twohand_poses() -> tuple[HitDownPoseDeltaV01, ...]:
    onehand = load_hit_down_cycle_profile_v01("human_warrior_m01")
    return tuple(_adapt_pose_for_twohand(pose) for pose in onehand.poses)


_ONEHAND_SOURCE = load_hit_down_cycle_profile_v01("human_warrior_m01")

HUMAN_WARRIOR_M01_HIT_DOWN_TWOHAND_CYCLE_V01 = HitDownCycleProfileV01(
    character_id="human_warrior_m01",
    revision="hit_down_twohand_cycle_v01_from_onehand_motion_pass01",
    animation_id="hit_01_twohand_down_v01",
    direction="down",
    fps=HIT_DOWN_CYCLE_FPS,
    loop=False,
    frame_order=HIT_DOWN_CYCLE_FRAME_ORDER,
    phase_order=HIT_DOWN_CYCLE_PHASE_ORDER,
    stance_variant_id=TWOHAND_STANCE_VARIANT_ID,
    stance_source_revision=TWOHAND_STANCE_SOURCE_REVISION,
    weapon_cycle_id=TWOHAND_STANCE_VARIANT_ID,
    incoming_direction=_ONEHAND_SOURCE.incoming_direction,
    poses=_build_twohand_poses(),
    source_keypose_revision=_ONEHAND_SOURCE.revision,
    appearance_revision=_ONEHAND_SOURCE.appearance_revision,
    head_revision=_ONEHAND_SOURCE.head_revision,
    proxy_revision=_ONEHAND_SOURCE.proxy_revision,
)


def load_hit_down_twohand_cycle_profile_v01(
    character_id: str,
) -> HitDownCycleProfileV01:
    profile = HUMAN_WARRIOR_M01_HIT_DOWN_TWOHAND_CYCLE_V01
    if character_id != profile.character_id:
        raise KeyError(
            f"No twohand hit down cycle v01 profile for character_id={character_id}"
        )
    if profile.direction != "down" or profile.loop:
        raise ValueError("Twohand hit down cycle v01 identity drifted")
    if profile.frame_order != HIT_DOWN_CYCLE_FRAME_ORDER:
        raise ValueError("Twohand hit down cycle v01 frame order drifted")
    if profile.phase_order != HIT_DOWN_CYCLE_PHASE_ORDER:
        raise ValueError("Twohand hit down cycle v01 phase order drifted")
    if profile.stance_variant_id != TWOHAND_STANCE_VARIANT_ID:
        raise ValueError("Twohand hit down cycle v01 stance drifted")
    if profile.source_keypose_revision != _ONEHAND_SOURCE.revision:
        raise ValueError("Twohand hit down cycle v01 motion source drifted")
    if tuple(pose.frame for pose in profile.poses) != profile.frame_order:
        raise ValueError("Twohand hit down cycle v01 pose frames drifted")
    if tuple(pose.phase for pose in profile.poses) != profile.phase_order:
        raise ValueError("Twohand hit down cycle v01 pose phases drifted")
    if any(
        abs(value) > MAX_PELVIS_TRANSLATION
        for pose in profile.poses
        for value in pose.translation_deltas()
    ):
        raise ValueError("Twohand hit down cycle v01 pelvis translation exceeds budget")
    if any(
        abs(value) > MAX_ROTATION_DELTA_DEGREES
        for pose in profile.poses
        for value in pose.rotation_deltas()
    ):
        raise ValueError("Twohand hit down cycle v01 rotation exceeds budget")

    onehand = _ONEHAND_SOURCE
    for source, adapted in zip(onehand.poses, profile.poses):
        for field in fields(HitDownPoseDeltaV01):
            if field.name in {"frame", "phase"} or field.name in _ARM_FIELDS:
                continue
            if getattr(source, field.name) != getattr(adapted, field.name):
                raise ValueError(
                    f"Twohand hit down cycle changed shared body channel {field.name}"
                )
        if adapted.upper_arm_left_x_degrees != adapted.upper_arm_right_x_degrees:
            raise ValueError("Twohand upper-arm X response lost symmetry")
        if adapted.forearm_left_x_degrees != adapted.forearm_right_x_degrees:
            raise ValueError("Twohand forearm X response lost symmetry")
        if adapted.hand_left_x_degrees != adapted.hand_right_x_degrees:
            raise ValueError("Twohand hand X response lost symmetry")
        if adapted.upper_arm_left_z_degrees != -adapted.upper_arm_right_z_degrees:
            raise ValueError("Twohand upper-arm Z response lost opposing symmetry")
        if adapted.forearm_left_z_degrees != -adapted.forearm_right_z_degrees:
            raise ValueError("Twohand forearm Z response lost opposing symmetry")
        if adapted.hand_left_z_degrees != -adapted.hand_right_z_degrees:
            raise ValueError("Twohand hand Z response lost opposing symmetry")
    return profile
