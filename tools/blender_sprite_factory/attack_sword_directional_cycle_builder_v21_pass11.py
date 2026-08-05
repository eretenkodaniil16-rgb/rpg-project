from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass09 import (
    create_attack_sword_directional_cycle_actions_v21_pass09,
)
from attack_sword_directional_cycle_correction_v21_pass11 import (
    SELECTED_ARM_BLEND,
    SOURCE_FRAME,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TWOHAND_LEFT_ANTICIPATION_REVISION,
)


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _apply_twohand_left_anticipation_arm_blend(
    context: factory.BuildContext,
) -> dict[str, float]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass11 action is missing: {action_name}"
        )
    if action.get("directional_twohand_left_windup_revision") is None:
        raise RuntimeError(
            "attack sword directional v21 pass11 requires pass09 windup correction"
        )

    applied: dict[str, float] = {}
    for bone_name in TARGET_BONES:
        data_path = f'pose.bones["{bone_name}"].rotation_euler'
        for axis_index in range(3):
            curve = _fcurve(action, data_path, axis_index)
            target_point = _point(curve, TARGET_FRAME)
            source_point = _point(curve, SOURCE_FRAME)
            target_value = float(target_point.co[1])
            source_value = float(source_point.co[1])
            delta = _shortest_angle_delta(target_value, source_value)
            applied_delta = delta * SELECTED_ARM_BLEND
            target_point.co[1] = target_value + applied_delta
            applied[f"{bone_name}[{axis_index}]"] = math.degrees(applied_delta)

    action["directional_twohand_left_anticipation_revision"] = (
        TWOHAND_LEFT_ANTICIPATION_REVISION
    )
    action["directional_twohand_left_anticipation_direction"] = TARGET_DIRECTION
    action["directional_twohand_left_anticipation_frame"] = TARGET_FRAME
    action["directional_twohand_left_anticipation_source_frame"] = SOURCE_FRAME
    action["directional_twohand_left_anticipation_arm_blend"] = (
        SELECTED_ARM_BLEND
    )
    action["directional_twohand_left_anticipation_action_only"] = True
    action["directional_twohand_left_anticipation_geometry_changed"] = False
    action["directional_twohand_left_anticipation_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass11_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass11_arm_blend"] = (
        SELECTED_ARM_BLEND
    )
    scene["attack_sword_directional_cycle_v21_pass11_action_only"] = True
    scene["attack_sword_directional_cycle_v21_pass11_down_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass11(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass09(context)
    _apply_twohand_left_anticipation_arm_blend(context)
