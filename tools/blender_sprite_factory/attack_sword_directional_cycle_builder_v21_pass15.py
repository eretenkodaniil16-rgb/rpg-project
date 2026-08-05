from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass13 import (
    create_attack_sword_directional_cycle_actions_v21_pass13,
)
from attack_sword_directional_cycle_correction_v21_pass13 import (
    CONTACT_VERIFICATION_REVISION,
)
from attack_sword_directional_cycle_correction_v21_pass15 import (
    SELECTED_ARM_BLEND_BY_FRAME,
    SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TWOHAND_LEFT_TAIL_REVISION,
)


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _apply_twohand_left_tail_arm_blend(
    context: factory.BuildContext,
) -> dict[str, float]:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass15 action is missing: {action_name}"
        )
    if (
        action.get("directional_twohand_left_contact_verification_revision")
        != CONTACT_VERIFICATION_REVISION
    ):
        raise RuntimeError(
            "attack sword directional v21 pass15 requires pass13 contact verification"
        )

    applied: dict[str, float] = {}
    for target_frame in TARGET_FRAMES:
        blend = float(SELECTED_ARM_BLEND_BY_FRAME[target_frame])
        if math.isclose(blend, 0.0, abs_tol=1.0e-9):
            continue
        source_frame = int(SOURCE_FRAME_BY_TARGET[target_frame])
        for bone_name in TARGET_BONES:
            data_path = f'pose.bones["{bone_name}"].rotation_euler'
            for axis_index in range(3):
                curve = _fcurve(action, data_path, axis_index)
                target_point = _point(curve, target_frame)
                source_point = _point(curve, source_frame)
                target_value = float(target_point.co[1])
                source_value = float(source_point.co[1])
                delta = _shortest_angle_delta(target_value, source_value)
                applied_delta = delta * blend
                target_point.co[1] = target_value + applied_delta
                applied[
                    f"f{target_frame:02d}:{bone_name}[{axis_index}]"
                ] = math.degrees(applied_delta)

    action["directional_twohand_left_tail_revision"] = (
        TWOHAND_LEFT_TAIL_REVISION
    )
    action["directional_twohand_left_tail_direction"] = TARGET_DIRECTION
    action["directional_twohand_left_tail_frames"] = "5,6,7,8"
    action["directional_twohand_left_tail_f05_source_frame"] = (
        SOURCE_FRAME_BY_TARGET[5]
    )
    action["directional_twohand_left_tail_f05_arm_blend"] = (
        SELECTED_ARM_BLEND_BY_FRAME[5]
    )
    action["directional_twohand_left_tail_action_data_changed"] = True
    action["directional_twohand_left_tail_geometry_changed"] = False
    action["directional_twohand_left_tail_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass15_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass15_tail_revision"] = (
        TWOHAND_LEFT_TAIL_REVISION
    )
    scene["attack_sword_directional_cycle_v21_pass15_f05_arm_blend"] = (
        SELECTED_ARM_BLEND_BY_FRAME[5]
    )
    scene["attack_sword_directional_cycle_v21_pass15_down_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass15_onehand_changed"] = False
    return applied


def create_attack_sword_directional_cycle_actions_v21_pass15(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass13(context)
    _apply_twohand_left_tail_arm_blend(context)
