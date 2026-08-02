from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass04 import (
    create_attack_sword_directional_cycle_actions_v21_pass04,
)
from attack_sword_directional_cycle_correction_v21_pass05 import (
    GUARD_FRAME,
    RECOVERY_CLEARANCE_REVISION,
    SELECTED_ARM_BLEND,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
)


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _apply_left_recovery_arm_blend(
    context: factory.BuildContext,
) -> dict[str, float]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass05 action is missing: {action_name}"
        )
    if action.get("directional_anticipation_revision") is None:
        raise RuntimeError(
            "attack sword directional v21 pass05 requires pass04 anticipation correction"
        )

    applied: dict[str, float] = {}
    for bone_name in TARGET_BONES:
        data_path = f'pose.bones["{bone_name}"].rotation_euler'
        for axis_index in range(3):
            curve = _fcurve(action, data_path, axis_index)
            recovery_point = _point(curve, TARGET_FRAME)
            guard_point = _point(curve, GUARD_FRAME)
            source_value = float(recovery_point.co[1])
            guard_value = float(guard_point.co[1])
            delta = _shortest_angle_delta(source_value, guard_value)
            applied_delta = delta * SELECTED_ARM_BLEND
            recovery_point.co[1] = source_value + applied_delta
            applied[f"{bone_name}[{axis_index}]"] = math.degrees(applied_delta)

    action["directional_recovery_revision"] = RECOVERY_CLEARANCE_REVISION
    action["directional_recovery_direction"] = TARGET_DIRECTION
    action["directional_recovery_frame"] = TARGET_FRAME
    action["directional_recovery_guard_frame"] = GUARD_FRAME
    action["directional_recovery_arm_blend"] = SELECTED_ARM_BLEND
    action["directional_recovery_action_only"] = True
    action["directional_recovery_geometry_changed"] = False
    action["directional_recovery_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass05_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass05_arm_blend"] = (
        SELECTED_ARM_BLEND
    )
    scene["attack_sword_directional_cycle_v21_pass05_action_only"] = True
    scene["attack_sword_directional_cycle_v21_pass05_down_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass05(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass04(context)
    _apply_left_recovery_arm_blend(context)
