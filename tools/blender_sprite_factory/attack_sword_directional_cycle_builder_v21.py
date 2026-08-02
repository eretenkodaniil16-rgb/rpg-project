from __future__ import annotations

import blender_sprite_factory as factory
from attack_sword_directional_cycle_profile_v21 import (
    DIRECTIONAL_CYCLE_REVISION,
    DIRECTION_ORDER,
    TOTAL_ACTION_COUNT,
    load_attack_sword_directional_cycle_profile_v21,
)
from attack_sword_down_cycle_builder_v20 import (
    create_attack_sword_down_cycle_actions_v20,
)


def create_attack_sword_directional_cycle_actions_v21(
    context: factory.BuildContext,
) -> None:
    create_attack_sword_down_cycle_actions_v20(context)
    profile = load_attack_sword_directional_cycle_profile_v21(
        context.config.character_id
    )
    created_names: list[str] = []

    for action_spec in profile.actions:
        source_name = (
            f"{context.config.character_id}_{action_spec.source_action_id}"
        )
        target_name = f"{context.config.character_id}_{action_spec.action_id}"
        source_action = factory.bpy.data.actions.get(source_name)
        if source_action is None:
            raise RuntimeError(
                f"attack sword directional v21 source action is missing: {source_name}"
            )

        if action_spec.direction == "down":
            action = source_action
        else:
            if factory.bpy.data.actions.get(target_name) is not None:
                raise RuntimeError(
                    f"attack sword directional v21 action already exists: {target_name}"
                )
            action = source_action.copy()
            action.name = target_name
            action.use_fake_user = True
            action["profile_revision"] = DIRECTIONAL_CYCLE_REVISION
            action["source_action_id"] = action_spec.source_action_id
            action["source_action_revision"] = "full_cycle_v20_pass05"
            action["directional_copy_of_approved_local_motion"] = True
            created_names.append(target_name)

        action["directional_family_revision"] = DIRECTIONAL_CYCLE_REVISION
        action["animation_family"] = profile.animation_family
        action["direction"] = action_spec.direction
        action["grip_id"] = action_spec.grip_id
        action["weapon_cycle_id"] = action_spec.weapon_cycle_id
        action["frame_count"] = len(profile.frame_order)
        action["phase_order"] = ",".join(profile.phase_order)
        action["root_translation_used"] = False
        action["mirroring_used"] = False
        action["negative_scale_used"] = False
        action["runtime_connected"] = False
        action["manual_directional_review_required"] = True

    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_revision"] = DIRECTIONAL_CYCLE_REVISION
    scene["attack_sword_directional_cycle_direction_order"] = ",".join(
        DIRECTION_ORDER
    )
    scene["attack_sword_directional_cycle_action_count"] = TOTAL_ACTION_COUNT
    scene["attack_sword_directional_cycle_created_action_count"] = len(
        created_names
    )
    scene["attack_sword_directional_cycle_created_actions"] = ",".join(
        created_names
    )
    scene["attack_sword_directional_cycle_source_down_revision"] = (
        "v20_pass05_artist_approved"
    )
    scene["attack_sword_directional_cycle_local_motion_shared"] = True
    scene["attack_sword_directional_cycle_real_rig_rotation_used"] = True
    scene["attack_sword_directional_cycle_directional_weapon_modules_used"] = True
    scene["attack_sword_directional_cycle_root_translation_used"] = False
    scene["attack_sword_directional_cycle_mirroring_used"] = False
    scene["attack_sword_directional_cycle_negative_scale_used"] = False
    scene["attack_sword_directional_cycle_geometry_changed"] = False
    scene["attack_sword_directional_cycle_materials_changed"] = False
    scene["attack_sword_directional_cycle_runtime_connected"] = False
