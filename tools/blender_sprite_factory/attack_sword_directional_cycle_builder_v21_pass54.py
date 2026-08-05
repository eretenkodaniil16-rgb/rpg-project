from __future__ import annotations

import json
import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass03 import _fcurve, _point
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass54 import (
    ACTION_BONE_DELTAS_DEGREES_BY_FRAME,
    ACTION_CHANGED_FRAMES,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TWOHAND_UP_INTEGRATED_ACTION_REVISION,
)


def create_attack_sword_directional_cycle_actions_v21_pass54(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass26(context)
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass54 action is missing: {action_name}"
        )

    applied: dict[str, float] = {}
    for frame_number in ACTION_CHANGED_FRAMES:
        frame_deltas = ACTION_BONE_DELTAS_DEGREES_BY_FRAME[frame_number]
        for bone_name in TARGET_BONES:
            deltas = frame_deltas[bone_name]
            data_path = f'pose.bones["{bone_name}"].rotation_euler'
            for axis_index, delta_degrees in enumerate(deltas):
                value = float(delta_degrees)
                if math.isclose(value, 0.0, abs_tol=1.0e-9):
                    continue
                curve = _fcurve(action, data_path, axis_index)
                point = _point(curve, frame_number)
                point.co[1] = float(point.co[1]) + math.radians(value)
                applied[f"f{frame_number:02d}/{bone_name}[{axis_index}]"] = value

    action["directional_twohand_up_final_revision"] = (
        TWOHAND_UP_INTEGRATED_ACTION_REVISION
    )
    action["directional_twohand_up_final_direction"] = TARGET_DIRECTION
    action["directional_twohand_up_action_changed_frames"] = ",".join(
        str(frame) for frame in ACTION_CHANGED_FRAMES
    )
    action["directional_twohand_up_bone_deltas_degrees"] = json.dumps(
        {
            str(frame): {
                bone: list(values)
                for bone, values in ACTION_BONE_DELTAS_DEGREES_BY_FRAME[frame].items()
            }
            for frame in ACTION_CHANGED_FRAMES
        },
        sort_keys=True,
    )
    action["directional_twohand_up_action_data_changed"] = True
    action["directional_twohand_up_root_translation_used"] = False
    action["directional_twohand_up_geometry_changed"] = False
    action["directional_twohand_up_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass54_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass54_revision"] = (
        TWOHAND_UP_INTEGRATED_ACTION_REVISION
    )
    scene["attack_sword_directional_cycle_v21_pass54_applied_deltas"] = (
        json.dumps(applied, sort_keys=True)
    )
    scene["attack_sword_directional_cycle_v21_pass54_down_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass54_left_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass54_right_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass54_onehand_up_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass54_twohand_up_changed"] = True
