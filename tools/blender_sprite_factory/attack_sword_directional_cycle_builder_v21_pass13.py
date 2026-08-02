from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_directional_cycle_builder_v21_pass11 import (
    create_attack_sword_directional_cycle_actions_v21_pass11,
)
from attack_sword_directional_cycle_correction_v21_pass11 import (
    SELECTED_ARM_BLEND as ANTICIPATION_ARM_BLEND,
    TARGET_FRAME as ANTICIPATION_FRAME,
    TWOHAND_LEFT_ANTICIPATION_REVISION,
)
from attack_sword_directional_cycle_correction_v21_pass13 import (
    CONTACT_ACTION_DATA_CHANGED,
    CONTACT_FRAME,
    CONTACT_VERIFICATION_REVISION,
    CONTACT_WEAPON_TRANSFORM_REQUIRED,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
)


def _verify_twohand_left_contact_source(
    context: factory.BuildContext,
) -> None:
    action_name = f"{context.config.character_id}_{TARGET_ACTION_ID}"
    action = factory.bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 pass13 action is missing: {action_name}"
        )
    if (
        action.get("directional_twohand_left_anticipation_revision")
        != TWOHAND_LEFT_ANTICIPATION_REVISION
    ):
        raise RuntimeError(
            "attack sword directional v21 pass13 requires pass11 anticipation"
        )
    if not math.isclose(
        float(
            action.get(
                "directional_twohand_left_anticipation_arm_blend",
                -1.0,
            )
        ),
        ANTICIPATION_ARM_BLEND,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "attack sword directional v21 pass13 anticipation blend drifted"
        )

    action["directional_twohand_left_contact_verification_revision"] = (
        CONTACT_VERIFICATION_REVISION
    )
    action["directional_twohand_left_contact_direction"] = TARGET_DIRECTION
    action["directional_twohand_left_contact_frame"] = CONTACT_FRAME
    action["directional_twohand_left_contact_action_data_changed"] = (
        CONTACT_ACTION_DATA_CHANGED
    )
    action["directional_twohand_left_contact_weapon_transform_required"] = (
        CONTACT_WEAPON_TRANSFORM_REQUIRED
    )
    action["directional_twohand_left_contact_geometry_changed"] = False
    action["directional_twohand_left_contact_materials_changed"] = False

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_pass13_action"] = action_name
    scene["attack_sword_directional_cycle_v21_pass13_anticipation_frame"] = (
        ANTICIPATION_FRAME
    )
    scene["attack_sword_directional_cycle_v21_pass13_contact_frame"] = (
        CONTACT_FRAME
    )
    scene["attack_sword_directional_cycle_v21_pass13_contact_changed"] = False
    scene["attack_sword_directional_cycle_v21_pass13_down_changed"] = False


def create_attack_sword_directional_cycle_actions_v21_pass13(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_directional_cycle_actions_v21_pass11(context)
    _verify_twohand_left_contact_source(context)
