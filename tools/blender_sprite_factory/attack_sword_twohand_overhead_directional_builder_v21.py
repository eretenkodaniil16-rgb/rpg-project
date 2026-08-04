from __future__ import annotations

import attack_sword_down_cycle_builder_v20 as cycle_builder
import blender_sprite_factory as factory
from attack_sword_twohand_down_overhead_profile_v21 import (
    OVERHEAD_ACTION_ID,
    load_attack_sword_twohand_down_overhead_profile_v21,
)
from attack_sword_twohand_overhead_directional_profile_v21 import (
    DIRECTIONAL_OVERHEAD_REVISION,
    DIRECTION_ORDER,
    TOTAL_ACTION_COUNT,
    load_attack_sword_twohand_overhead_directional_profile_v21,
)


ORIGINAL_CYCLE_PROFILE_LOADER = cycle_builder.load_attack_sword_down_cycle_profile_v20


def create_attack_sword_twohand_overhead_directional_actions_v21(
    context: factory.BuildContext,
) -> None:
    cycle_builder.load_attack_sword_down_cycle_profile_v20 = (
        load_attack_sword_twohand_down_overhead_profile_v21
    )
    try:
        cycle_builder.create_attack_sword_down_cycle_actions_v20(context)
    finally:
        cycle_builder.load_attack_sword_down_cycle_profile_v20 = (
            ORIGINAL_CYCLE_PROFILE_LOADER
        )

    profile = load_attack_sword_twohand_overhead_directional_profile_v21(
        context.config.character_id
    )
    source_name = f"{context.config.character_id}_{OVERHEAD_ACTION_ID}"
    source_action = factory.bpy.data.actions.get(source_name)
    if source_action is None:
        raise RuntimeError(
            f"directional overhead v21 source action is missing: {source_name}"
        )

    created_names: list[str] = []
    for action_spec in profile.actions:
        target_name = f"{context.config.character_id}_{action_spec.action_id}"
        if action_spec.direction == "down":
            action = source_action
        else:
            if factory.bpy.data.actions.get(target_name) is not None:
                raise RuntimeError(
                    f"directional overhead v21 action already exists: {target_name}"
                )
            action = source_action.copy()
            action.name = target_name
            action.use_fake_user = True
            action["profile_revision"] = "v21"
            action["source_action_id"] = OVERHEAD_ACTION_ID
            action["source_action_revision"] = profile.source_overhead_revision
            action["directional_copy_of_overhead_local_motion"] = True
            created_names.append(target_name)

        action["directional_overhead_revision"] = DIRECTIONAL_OVERHEAD_REVISION
        action["animation_family"] = profile.animation_family
        action["direction"] = action_spec.direction
        action["grip_id"] = action_spec.grip_id
        action["weapon_cycle_id"] = action_spec.weapon_cycle_id
        action["trajectory_id"] = action_spec.trajectory_id
        action["frame_count"] = len(profile.frame_order)
        action["phase_order"] = ",".join(profile.phase_order)
        action["local_action_curves_changed"] = False
        action["root_translation_used"] = False
        action["mirroring_used"] = False
        action["negative_scale_used"] = False
        action["runtime_connected"] = False
        action["manual_directional_review_required"] = True

    if len(profile.actions) != TOTAL_ACTION_COUNT:
        raise RuntimeError("directional overhead v21 action count drifted")
    if len(created_names) != TOTAL_ACTION_COUNT - 1:
        raise RuntimeError("directional overhead v21 must create exactly three copies")

    scene = factory.bpy.context.scene
    scene["twohand_overhead_directional_revision"] = DIRECTIONAL_OVERHEAD_REVISION
    scene["twohand_overhead_direction_order"] = ",".join(DIRECTION_ORDER)
    scene["twohand_overhead_directional_action_count"] = TOTAL_ACTION_COUNT
    scene["twohand_overhead_directional_created_actions"] = ",".join(created_names)
    scene["twohand_overhead_directional_source_action"] = source_name
    scene["twohand_overhead_directional_local_motion_shared"] = True
    scene["twohand_overhead_directional_real_rig_rotation_used"] = True
    scene["twohand_overhead_directional_root_translation_used"] = False
    scene["twohand_overhead_directional_mirroring_used"] = False
    scene["twohand_overhead_directional_negative_scale_used"] = False
    scene["twohand_overhead_directional_geometry_changed"] = False
    scene["twohand_overhead_directional_materials_changed"] = False
    scene["twohand_overhead_directional_runtime_connected"] = False
