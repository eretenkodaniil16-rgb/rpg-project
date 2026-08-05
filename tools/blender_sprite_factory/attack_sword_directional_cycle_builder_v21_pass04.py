from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import (
    BONE_DELTAS_DEGREES,
    _fcurve,
    _point,
    create_attack_sword_directional_cycle_actions_v21_pass03,
)
from attack_sword_directional_cycle_correction_v21_pass04 import (
    ANTICIPATION_CLEARANCE_REVISION,
    SELECTED_INCREMENTAL_WEIGHT,
    SELECTED_TOTAL_WEIGHT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
)


def _apply_left_anticipation_weight(
    context: factory.BuildContext,
) -> dict[str, float]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass04 action is missing: {action_name}"
        )
    if action.get("directional_arm_correction_revision") is None:
        raise RuntimeError(
            "attack sword directional v21 pass04 requires pass03 arm correction"
        )

    applied: dict[str, float] = {}
    for bone_name, axis_deltas in BONE_DELTAS_DEGREES.items():
        data_path = f'pose.bones["{bone_name}"].rotation_euler'
        for axis_index, base_delta_degrees in axis_deltas.items():
            delta_degrees = (
                float(base_delta_degrees) * SELECTED_INCREMENTAL_WEIGHT
            )
            if abs(delta_degrees) <= 1.0e-9:
                continue
            curve = _fcurve(action, data_path, axis_index)
            point = _point(curve, TARGET_FRAME)
            point.co[1] = float(point.co[1]) + math.radians(delta_degrees)
            applied[f"{bone_name}[{axis_index}]"] = delta_degrees

    action["directional_anticipation_revision"] = (
        ANTICIPATION_CLEARANCE_REVISION
    )
    action["directional_anticipation_direction"] = TARGET_DIRECTION
    action["directional_anticipation_frame"] = TARGET_FRAME
    action["directional_anticipation_total_weight"] = SELECTED_TOTAL_WEIGHT
    action["directional_anticipation_incremental_weight"] = (
        SELECTED_INCREMENTAL_WEIGHT
    )
    action["directional_anticipation_action_only"] = True
    action["directional_anticipation_geometry_changed"] = False
    action["directional_anticipation_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass04_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass04_total_weight"] = (
        SELECTED_TOTAL_WEIGHT
    )
    scene["attack_sword_directional_cycle_v21_pass04_action_only"] = True
    scene["attack_sword_directional_cycle_v21_pass04_down_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass04(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass03(context)
    _apply_left_anticipation_weight(context)
