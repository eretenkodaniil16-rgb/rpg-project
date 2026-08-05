from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass15 import (
    create_attack_sword_directional_cycle_actions_v21_pass15,
)
from attack_sword_directional_cycle_correction_v21_pass17 import (
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TWOHAND_RIGHT_WINDUP_REVISION,
    WINDUP_FRAME,
    WINDUP_SELECTED_ARM_BLEND,
    WINDUP_SOURCE_FRAME,
)


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _apply_twohand_right_windup_arm_blend(
    context: factory.BuildContext,
) -> dict[str, float]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass17 action is missing: {action_name}"
        )

    applied: dict[str, float] = {}
    for bone_name in TARGET_BONES:
        data_path = f'pose.bones["{bone_name}"].rotation_euler'
        for axis_index in range(3):
            curve = _fcurve(action, data_path, axis_index)
            target_point = _point(curve, WINDUP_FRAME)
            source_point = _point(curve, WINDUP_SOURCE_FRAME)
            target_value = float(target_point.co[1])
            source_value = float(source_point.co[1])
            delta = _shortest_angle_delta(target_value, source_value)
            applied_delta = delta * WINDUP_SELECTED_ARM_BLEND
            target_point.co[1] = target_value + applied_delta
            applied[f"{bone_name}[{axis_index}]"] = math.degrees(applied_delta)

    action["directional_twohand_right_windup_revision"] = (
        TWOHAND_RIGHT_WINDUP_REVISION
    )
    action["directional_twohand_right_windup_direction"] = TARGET_DIRECTION
    action["directional_twohand_right_windup_frame"] = WINDUP_FRAME
    action["directional_twohand_right_windup_source_frame"] = (
        WINDUP_SOURCE_FRAME
    )
    action["directional_twohand_right_windup_arm_blend"] = (
        WINDUP_SELECTED_ARM_BLEND
    )
    action["directional_twohand_right_windup_action_data_changed"] = True
    action["directional_twohand_right_windup_geometry_changed"] = False
    action["directional_twohand_right_windup_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass17_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass17_windup_revision"] = (
        TWOHAND_RIGHT_WINDUP_REVISION
    )
    scene["attack_sword_directional_cycle_v21_pass17_windup_arm_blend"] = (
        WINDUP_SELECTED_ARM_BLEND
    )
    scene["attack_sword_directional_cycle_v21_pass17_down_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass17_left_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass17_onehand_right_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass17(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass15(context)
    _apply_twohand_right_windup_arm_blend(context)
