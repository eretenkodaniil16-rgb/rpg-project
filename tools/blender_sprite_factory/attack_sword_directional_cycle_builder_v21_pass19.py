from __future__ import annotations

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass18 import (
    create_attack_sword_directional_cycle_actions_v21_pass18,
)
from attack_sword_directional_cycle_correction_v21_pass19 import (
    SELECTED_ARM_BLEND_BY_FRAME,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TWOHAND_RIGHT_FULL_REVISION,
)


def create_attack_sword_directional_cycle_actions_v21_pass19(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass18(context)
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass19 action is missing: {action_name}"
        )
    action["directional_twohand_right_full_revision"] = (
        TWOHAND_RIGHT_FULL_REVISION
    )
    action["directional_twohand_right_full_direction"] = TARGET_DIRECTION
    action["directional_twohand_right_full_frames"] = "1,2,3,4,5,6,7,8"
    action["directional_twohand_right_action_changed_frames"] = "2,3"
    action["directional_twohand_right_f02_arm_blend"] = (
        SELECTED_ARM_BLEND_BY_FRAME[2]
    )
    action["directional_twohand_right_f03_arm_blend"] = (
        SELECTED_ARM_BLEND_BY_FRAME[3]
    )
    action["directional_twohand_right_geometry_changed"] = False
    action["directional_twohand_right_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass19_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass19_right_revision"] = (
        TWOHAND_RIGHT_FULL_REVISION
    )
    scene["attack_sword_directional_cycle_v21_pass19_down_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass19_left_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass19_onehand_right_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass19_up_changed"] = False
