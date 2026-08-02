from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21 import (
    create_attack_sword_directional_cycle_actions_v21,
)
from attack_sword_directional_cycle_correction_v21_pass03 import (
    ARM_CLEARANCE_REVISION,
    SELECTED_DEPTH_DEGREES,
    SELECTED_LIFT_DEGREES,
    SELECTED_SWEEP_DEGREES,
    SMOOTHING_WEIGHTS,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
)


BONE_DELTAS_DEGREES = {
    "upper_arm.R": {
        0: SELECTED_LIFT_DEGREES * 0.70,
        1: SELECTED_DEPTH_DEGREES * 0.70,
        2: SELECTED_SWEEP_DEGREES * 0.55,
    },
    "forearm.R": {
        0: SELECTED_LIFT_DEGREES,
        1: SELECTED_DEPTH_DEGREES,
        2: SELECTED_SWEEP_DEGREES,
    },
    "hand.R": {
        0: SELECTED_LIFT_DEGREES * 0.35,
        1: SELECTED_DEPTH_DEGREES * 0.45,
        2: SELECTED_SWEEP_DEGREES * 0.35,
    },
}


def _channelbag(action: object) -> object:
    if len(action.slots) != 1:
        raise RuntimeError(
            f"attack sword directional v21 pass03 expected one slot: {action.name}"
        )
    if len(action.layers) != 1 or len(action.layers[0].strips) != 1:
        raise RuntimeError(
            f"attack sword directional v21 pass03 expected one layer/strip: "
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
        f"attack sword directional v21 pass03 missing curve: "
        f"{data_path}[{array_index}]"
    )


def _point(curve: object, frame_number: int) -> object:
    for point in curve.keyframe_points:
        if abs(float(point.co[0]) - float(frame_number)) <= 1.0e-4:
            return point
    raise RuntimeError(
        f"attack sword directional v21 pass03 missing frame {frame_number}: "
        f"{curve.data_path}[{curve.array_index}]"
    )


def _apply_left_windup_correction(
    context: factory.BuildContext,
) -> dict[str, dict[str, float]]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass03 action is missing: {action_name}"
        )
    if action.get("profile_revision") != "v21":
        raise RuntimeError(
            f"attack sword directional v21 pass03 action revision drifted: "
            f"{action_name}"
        )

    applied: dict[str, dict[str, float]] = {}
    for frame_number, weight in sorted(SMOOTHING_WEIGHTS.items()):
        frame_payload: dict[str, float] = {}
        for bone_name, axis_deltas in BONE_DELTAS_DEGREES.items():
            data_path = f'pose.bones["{bone_name}"].rotation_euler'
            for axis_index, base_delta in axis_deltas.items():
                delta_degrees = float(base_delta) * float(weight)
                if abs(delta_degrees) <= 1.0e-9:
                    continue
                curve = _fcurve(action, data_path, axis_index)
                point = _point(curve, frame_number)
                point.co[1] = float(point.co[1]) + math.radians(delta_degrees)
                frame_payload[f"{bone_name}[{axis_index}]"] = delta_degrees
        applied[f"f{frame_number:02d}"] = frame_payload

    action["directional_arm_correction_revision"] = ARM_CLEARANCE_REVISION
    action["directional_arm_correction_direction"] = TARGET_DIRECTION
    action["directional_arm_correction_frame"] = TARGET_FRAME
    action["directional_arm_correction_lift_degrees"] = SELECTED_LIFT_DEGREES
    action["directional_arm_correction_sweep_degrees"] = SELECTED_SWEEP_DEGREES
    action["directional_arm_correction_depth_degrees"] = SELECTED_DEPTH_DEGREES
    action["directional_arm_correction_smoothing_frames"] = "1,2,3"
    action["directional_arm_correction_action_only"] = True
    action["directional_arm_correction_geometry_changed"] = False
    action["directional_arm_correction_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass03_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass03_deltas"] = str(applied)
    scene["attack_sword_directional_cycle_v21_pass03_action_only"] = True
    scene["attack_sword_directional_cycle_v21_pass03_down_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass03(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21(context)
    _apply_left_windup_correction(context)
