from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass54 import (
    create_attack_sword_directional_cycle_actions_v21_pass54,
)
from attack_sword_onehand_directional_correction_v22_pass01 import (
    BONE_DELTAS_DEGREES_BY_DIRECTION,
    CORRECTION_PASS,
    FRAME_WEIGHTS,
    ONEHAND_DIRECTIONAL_REVISION,
    PRESERVE_SOURCE_FCURVE_TIMING,
    SOURCE_MASTER_ACTION_ID,
    TARGET_ACTION_ID_BY_DIRECTION,
    TARGET_DIRECTIONS,
    TARGET_FRAMES,
)


def _channelbag(action: object) -> object:
    if len(action.slots) != 1:
        raise RuntimeError(
            "onehand directional v22 expected exactly one action slot: "
            f"{action.name}"
        )
    if len(action.layers) != 1 or len(action.layers[0].strips) != 1:
        raise RuntimeError(
            "onehand directional v22 expected one layer and one strip: "
            f"{action.name}"
        )
    return action.layers[0].strips[0].channelbag(action.slots[0])


def _fcurve(action: object, data_path: str, array_index: int) -> object:
    for curve in _channelbag(action).fcurves:
        if (
            str(curve.data_path) == data_path
            and int(curve.array_index) == array_index
        ):
            return curve
    raise RuntimeError(
        "onehand directional v22 missing curve: "
        f"{action.name}:{data_path}[{array_index}]"
    )


def _point(curve: object, frame_number: int) -> object:
    for point in curve.keyframe_points:
        if abs(float(point.co[0]) - float(frame_number)) <= 1.0e-4:
            return point
    raise RuntimeError(
        "onehand directional v22 missing keyframe: "n        f"{curve.data_path}[{curve.array_index}]@{frame_number}"
    )


def _apply_direction_correction(
    context: factory.BuildContext,
    direction: str,
) -> dict[str, dict[str, float]]:
    action_id = TARGET_ACTION_ID_BY_DIRECTION[direction]
    action_name = f"{context.config.character_id}_{action_id}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"onehand directional v22 action is missing: {action_name}"
        )
    if not bool(action.get("directional_copy_of_approved_local_motion", False)):
        raise RuntimeError(
            "onehand directional v22 requires copied source motion: "
            f"{action_name}"
        )
    if str(action.get("source_action_id", "")) != SOURCE_MASTER_ACTION_ID:
        raise RuntimeError(
            "onehand directional v22 source action drifted: "
            f"{action_name}"
        )

    applied: dict[str, dict[str, float]] = {}
    changed_frames: list[int] = []
    direction_deltas = BONE_DELTAS_DEGREES_BY_DIRECTION[direction]
    for frame_number in TARGET_FRAMES:
        weight = float(FRAME_WEIGHTS[frame_number])
        frame_payload: dict[str, float] = {}
        for bone_name, axis_deltas in direction_deltas.items():
            data_path = f'pose.bones["{bone_name}"].rotation_euler'
            for axis_index, base_delta in enumerate(axis_deltas):
                delta_degrees = float(base_delta) * weight
                if abs(delta_degrees) <= 1.0e-9:
                    continue
                curve = _fcurve(action, data_path, axis_index)
                point = _point(curve, frame_number)
                point.co[1] = float(point.co[1]) + math.radians(delta_degrees)
                frame_payload[f"{bone_name}[{axis_index}]"] = delta_degrees
        if frame_payload:
            changed_frames.append(frame_number)
        applied[f"f{frame_number:02d}"] = frame_payload

    action["onehand_directional_revision"] = ONEHAND_DIRECTIONAL_REVISION
    action["onehand_directional_correction_pass"] = CORRECTION_PASS
    action["onehand_directional_source_action_id"] = SOURCE_MASTER_ACTION_ID
    action["onehand_directional_source_timing_preserved"] = (
        PRESERVE_SOURCE_FCURVE_TIMING
    )
    action["onehand_directional_corrected_frames"] = ",".join(
        str(frame) for frame in changed_frames
    )
    action["onehand_directional_action_data_changed"] = bool(changed_frames)
    action["onehand_directional_action_only"] = True
    action["onehand_directional_root_translation_used"] = False
    action["onehand_directional_mirroring_used"] = False
    action["onehand_directional_negative_scale_used"] = False
    action["onehand_directional_weapon_geometry_changed"] = False
    action["onehand_directional_materials_changed"] = False
    return applied


def create_attack_sword_onehand_directional_actions_v22_pass01(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass54(context)

    applied_by_direction: dict[str, dict[str, dict[str, float]]] = {}
    for direction in TARGET_DIRECTIONS:
        applied_by_direction[direction] = _apply_direction_correction(
            context,
            direction,
        )

    scene = factory.bpy.context.scene
    scene["attack_sword_onehand_directional_revision"] = (
        ONEHAND_DIRECTIONAL_REVISION
    )
    scene["attack_sword_onehand_directional_correction_pass"] = CORRECTION_PASS
    scene["attack_sword_onehand_directional_source_action_id"] = (
        SOURCE_MASTER_ACTION_ID
    )
    scene["attack_sword_onehand_directional_target_directions"] = ",".join(
        TARGET_DIRECTIONS
    )
    scene["attack_sword_onehand_directional_applied_deltas"] = str(
        applied_by_direction
    )
    scene["attack_sword_onehand_directional_source_timing_preserved"] = True
    scene["attack_sword_onehand_directional_up_source_preserved"] = not any(
        applied_by_direction["up"].values()
    )
    scene["attack_sword_onehand_directional_twohand_changed"] = False
    scene["attack_sword_onehand_directional_down_changed"] = False
    scene["attack_sword_onehand_directional_root_translation_used"] = False
    scene["attack_sword_onehand_directional_mirroring_used"] = False
    scene["attack_sword_onehand_directional_negative_scale_used"] = False
    scene["attack_sword_onehand_directional_weapon_geometry_changed"] = False
    scene["attack_sword_onehand_directional_materials_changed"] = False
