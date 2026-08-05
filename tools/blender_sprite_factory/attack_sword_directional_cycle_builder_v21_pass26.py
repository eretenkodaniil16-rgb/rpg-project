from __future__ import annotations

import json
import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass19 import (
    create_attack_sword_directional_cycle_actions_v21_pass19,
)
from attack_sword_directional_cycle_correction_v21_pass26 import (
    ARM_TARGET_FRAME,
    ONEHAND_UP_FINAL_REVISION,
    SELECTED_ARM_PROFILE,
    SELECTED_BONE_DELTAS_DEGREES,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
)


def create_attack_sword_directional_cycle_actions_v21_pass26(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass19(context)
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass26 action is missing: {action_name}"
        )

    applied: dict[str, float] = {}
    for bone_name in TARGET_BONES:
        deltas = SELECTED_BONE_DELTAS_DEGREES[bone_name]
        data_path = f'pose.bones["{bone_name}"].rotation_euler'
        for axis_index, delta_degrees in enumerate(deltas):
            delta_degrees = float(delta_degrees)
            if math.isclose(delta_degrees, 0.0, abs_tol=1.0e-9):
                continue
            curve = _fcurve(action, data_path, axis_index)
            point = _point(curve, ARM_TARGET_FRAME)
            point.co[1] = float(point.co[1]) + math.radians(delta_degrees)
            applied[f"{bone_name}[{axis_index}]"] = delta_degrees

    action["directional_onehand_up_final_revision"] = ONEHAND_UP_FINAL_REVISION
    action["directional_onehand_up_final_direction"] = TARGET_DIRECTION
    action["directional_onehand_up_final_frames"] = "5,6,7,8"
    action["directional_onehand_up_arm_changed_frame"] = ARM_TARGET_FRAME
    action["directional_onehand_up_arm_profile"] = json.dumps(
        SELECTED_ARM_PROFILE,
        sort_keys=True,
    )
    action["directional_onehand_up_f05_bone_deltas_degrees"] = json.dumps(
        {key: list(value) for key, value in SELECTED_BONE_DELTAS_DEGREES.items()},
        sort_keys=True,
    )
    action["directional_onehand_up_action_data_changed"] = True
    action["directional_onehand_up_geometry_changed"] = False
    action["directional_onehand_up_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass26_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass26_revision"] = (
        ONEHAND_UP_FINAL_REVISION
    )
    scene["attack_sword_directional_cycle_v21_pass26_applied_deltas"] = (
        json.dumps(applied, sort_keys=True)
    )
    scene["attack_sword_directional_cycle_v21_pass26_down_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass26_left_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass26_right_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass26_twohand_up_changed"] = False
