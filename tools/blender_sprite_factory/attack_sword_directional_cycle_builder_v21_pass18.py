from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass15 import (
    create_attack_sword_directional_cycle_actions_v21_pass15,
)
from attack_sword_directional_cycle_correction_v21_pass18 import (
    EARLY_SELECTED_ARM_BLEND_BY_FRAME,
    EARLY_SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TWOHAND_RIGHT_EARLY_REVISION,
)


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _apply_twohand_right_early_arm_blends(
    context: factory.BuildContext,
) -> dict[str, float]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass18 action is missing: {action_name}"
        )

    applied: dict[str, float] = {}
    for target_frame, source_frame in EARLY_SOURCE_FRAME_BY_TARGET.items():
        blend = float(EARLY_SELECTED_ARM_BLEND_BY_FRAME[target_frame])
        for bone_name in TARGET_BONES:
            data_path = f'pose.bones["{bone_name}"].rotation_euler'
            for axis_index in range(3):
                curve = _fcurve(action, data_path, axis_index)
                target_point = _point(curve, int(target_frame))
                source_point = _point(curve, int(source_frame))
                target_value = float(target_point.co[1])
                source_value = float(source_point.co[1])
                delta = _shortest_angle_delta(target_value, source_value)
                applied_delta = delta * blend
                target_point.co[1] = target_value + applied_delta
                applied[
                    f"f{int(target_frame):02d}:{bone_name}[{axis_index}]"
                ] = math.degrees(applied_delta)

    action["directional_twohand_right_early_revision"] = (
        TWOHAND_RIGHT_EARLY_REVISION
    )
    action["directional_twohand_right_early_direction"] = TARGET_DIRECTION
    action["directional_twohand_right_early_frames"] = "2,3"
    action["directional_twohand_right_f02_source_frame"] = (
        EARLY_SOURCE_FRAME_BY_TARGET[2]
    )
    action["directional_twohand_right_f02_arm_blend"] = (
        EARLY_SELECTED_ARM_BLEND_BY_FRAME[2]
    )
    action["directional_twohand_right_f03_source_frame"] = (
        EARLY_SOURCE_FRAME_BY_TARGET[3]
    )
    action["directional_twohand_right_f03_arm_blend"] = (
        EARLY_SELECTED_ARM_BLEND_BY_FRAME[3]
    )
    action["directional_twohand_right_early_action_data_changed"] = True
    action["directional_twohand_right_early_geometry_changed"] = False
    action["directional_twohand_right_early_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass18_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass18_early_revision"] = (
        TWOHAND_RIGHT_EARLY_REVISION
    )
    scene["attack_sword_directional_cycle_v21_pass18_down_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass18_left_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass18_onehand_right_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass18(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass15(context)
    _apply_twohand_right_early_arm_blends(context)
